import asyncio
import base64
import io
import logging
import math
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from dataclasses import field as dc_field
from importlib import resources
from typing import Any, Callable, ClassVar, Self, Sequence, override
from uuid import uuid4

import aiohttp
import backoff
import numpy as np
import numpy.typing as npt
from asyncache import cached
from cachetools import LRUCache
from PIL import Image, ImageEnhance, ImageFilter, ImageOps, UnidentifiedImageError

import nanapi.resources
from nanapi.database.anilist.chara_select import chara_select
from nanapi.database.anilist.image_save import image_save
from nanapi.database.anilist.image_select import image_select
from nanapi.database.anilist.media_select import MediaSelectResult, media_select
from nanapi.database.waicolle.waifu_insert import WaicolleCollagePosition
from nanapi.utils.clients import get_edgedb, get_session
from nanapi.utils.misc import default_backoff, to_producer
from nanapi.utils.waicolle import CHARA_TYPES, RNG, WAIFU_TYPES

logger = logging.getLogger(__name__)


get_img_sema = asyncio.Semaphore(10)


def load_img(buffer: bytes) -> Image.Image:
    img = Image.open(io.BytesIO(buffer))
    img.load()
    return img


@cached(cache=LRUCache(2048))
@backoff.on_exception(backoff.expo, (aiohttp.ServerTimeoutError, ValueError), max_time=600)
@default_backoff
async def fetch_img(url: str) -> Image.Image:
    try:
        async with get_img_sema:
            async with get_session().get(url) as resp:
                resp.raise_for_status()
                buffer = await resp.read()

            asyncio.create_task(
                image_save(get_edgedb(), url=url, data=base64.b64encode(buffer).decode())
            )

            img = await asyncio.to_thread(load_img, buffer)
            return img
    except UnidentifiedImageError as e:
        raise RuntimeError(f'failed to load {url}') from e


@dataclass
class ALImage(ABC):
    WIDTH: ClassVar[int] = 100
    HEIGHT: ClassVar[int] = round(WIDTH * 3 / 2)

    def __post_init__(self):
        self.image: Image.Image | None = None

    @abstractmethod
    async def load_image(self, al_img: bytes | None = None):
        pass

    @classmethod
    def crop(cls, img: Image.Image) -> Image.Image:
        if img.height / img.width < 3 / 2:
            new_width = int(2 / 3 * img.height)
            new_x0 = (img.width - new_width) // 2
            img = img.crop((new_x0, 0, new_x0 + new_width, img.height))
        else:
            new_height = int(3 / 2 * img.width)
            new_y0 = (img.height - new_height) // 2
            img = img.crop((0, new_y0, img.width, new_y0 + new_height))
        return img

    @classmethod
    def normalize(cls, img: Image.Image, zoom: int) -> Image.Image:
        img = img.resize((cls.WIDTH * zoom, cls.HEIGHT * zoom))
        return img

    def __getattr__(self, key):
        return getattr(self.image, key)


@dataclass
class CharaImageProps:
    zoom: int = 1
    custom_image: Image.Image | None = None

    @classmethod
    def from_waifu(cls, waifu: WAIFU_TYPES) -> Self:
        props = cls()
        if waifu.level > 0:
            props.zoom = 2**waifu.level
        if waifu.custom_image is not None:
            props.custom_image = load_img(base64.b64decode(waifu.custom_image))
        return props


ImageEnhancer = Callable[[Image.Image], Image.Image]


def blood_enhancer(img: Image.Image) -> Image.Image:
    img = ImageOps.grayscale(img).convert('RGB')
    with (
        resources.path(nanapi.resources, 'blood.png') as bloody_path,
        Image.open(bloody_path) as bloody,
    ):
        for _ in range(5):
            bloody_x = RNG.integers(0, bloody.width - img.width, dtype=int)
            bloody_y = RNG.integers(0, bloody.height - img.height, dtype=int)

            bloody_i = bloody.crop(
                (bloody_x, bloody_y, bloody_x + img.width, bloody_y + img.height)
            )

            img.paste(bloody_i, (0, 0), bloody_i)
    return img


class CharaImageEnhancer:
    DARKEN = lambda img: ImageEnhance.Brightness(img).enhance(0.5)
    BLUR = lambda img: img.filter(ImageFilter.BoxBlur(10))
    BLOOD = staticmethod(blood_enhancer)


@dataclass
class CharaImage(ALImage):
    chara: CHARA_TYPES
    properties: CharaImageProps = dc_field(default_factory=CharaImageProps)
    enhancers: list[ImageEnhancer] = dc_field(default_factory=list)

    def set_hidden(self):
        self.enhancers = [CharaImageEnhancer.DARKEN, CharaImageEnhancer.BLUR]

    def set_blooded(self):
        self.enhancers = [CharaImageEnhancer.BLOOD]

    @override
    async def load_image(self, al_img: bytes | None = None):
        img = self.properties.custom_image

        if img is None:
            if al_img is not None:
                img = await asyncio.to_thread(load_img, al_img)
            else:
                try:
                    img = await fetch_img(self.chara.image_large)
                except Exception as e:
                    logger.exception(e)
                    img = await fetch_img('https://hikari.butaishoujo.moe/p/6b5e1488/default.jpg')

        img = img.convert('RGBA')
        img = self.crop(img)
        img = self.normalize(img, self.properties.zoom)

        for enhancer in self.enhancers:
            img = enhancer(img)  # type: ignore

        self.image = img

    @classmethod
    async def load_image_groups(cls, image_groups: list[list['CharaImage']]):
        al_images = await image_select(
            get_edgedb(), urls=[i.chara.image_large for g in image_groups for i in g]
        )
        al_images_dict = {i.url: base64.b64decode(i.data) for i in al_images}
        tasks = [
            img.load_image(al_images_dict.get(img.chara.image_large, None))
            for g in image_groups
            for img in g
        ]
        await asyncio.gather(*tasks)


def sorted_custom_positions(waifus_charas: list[WAIFU_TYPES | Any]) -> list[WAIFU_TYPES | Any]:
    waifus_ids = set(w.id if isinstance(w, WAIFU_TYPES) else 0 for w in waifus_charas)
    rev_left_of_waifus = defaultdict(list)
    rev_right_of_waifus = defaultdict(list)
    sorted_waifus: list[WAIFU_TYPES | Any] = []
    sorted_waifus_ids = set()

    for waifu_chara in waifus_charas:
        if (
            isinstance(waifu_chara, WAIFU_TYPES)
            and waifu_chara.custom_position_waifu is not None
            and waifu_chara.custom_position != WaicolleCollagePosition.DEFAULT
            and waifu_chara.custom_position_waifu.id in waifus_ids
        ):
            if waifu_chara.custom_position == WaicolleCollagePosition.LEFT_OF:
                rev_left_of_waifus[waifu_chara.custom_position_waifu.id].append(waifu_chara)
            elif waifu_chara.custom_position == WaicolleCollagePosition.RIGHT_OF:
                rev_right_of_waifus[waifu_chara.custom_position_waifu.id].append(waifu_chara)

    waifus_ids = (
        waifus_ids
        - set(w.id for lo in rev_left_of_waifus.values() for w in lo)
        - set(w.id for ro in rev_right_of_waifus.values() for w in ro)
    )

    def _get_custom_positions_group(waifu: WAIFU_TYPES) -> list[WAIFU_TYPES]:
        group = []
        left_of_waifus = rev_left_of_waifus.pop(waifu.id, [])
        right_of_waifus = rev_right_of_waifus.pop(waifu.id, [])
        for left_of_waifu in left_of_waifus:
            group.extend(_get_custom_positions_group(left_of_waifu))
        group.append(waifu)
        sorted_waifus_ids.add(waifu.id)
        for right_of_waifu in right_of_waifus:
            group.extend(_get_custom_positions_group(right_of_waifu))
        return group

    for waifu_chara in waifus_charas:
        if isinstance(waifu_chara, WAIFU_TYPES):
            if waifu_chara.id in waifus_ids:
                sorted_waifus.extend(_get_custom_positions_group(waifu_chara))
        else:
            sorted_waifus.append(waifu_chara)

    # Add forgotten waifus at the end
    for waifu_chara in waifus_charas:
        if isinstance(waifu_chara, WAIFU_TYPES) and waifu_chara.id not in sorted_waifus_ids:
            sorted_waifus.append(waifu_chara)

    return sorted_waifus


def _make_collage(image_binary: io.BytesIO, chara_images: list[list[CharaImage]]):
    n_imgs = 0
    max_group_width = 0
    sizes = []
    for i, img_group in enumerate(chara_images):
        group_height = 0
        group_width = 0
        individual_sizes = []
        for img in img_group:
            n_imgs += img.properties.zoom**2
            group_width += img.properties.zoom
            group_height = max(img.properties.zoom, group_height)
            individual_sizes.append(img.properties.zoom)
        max_group_width = max(max_group_width, group_width)
        sizes.append((i, group_width, group_height, individual_sizes))

    total_area = ALImage.WIDTH * ALImage.HEIGHT * n_imgs
    total_est_height = math.sqrt(9 / 16 * total_area)

    nb_rows = round(total_est_height / ALImage.HEIGHT)
    nb_columns = max(math.ceil(n_imgs / nb_rows), max_group_width)

    positions, availability_matrix = _find_positions(sizes, nb_rows, nb_columns)
    # After computing positions, the size of availability_matrix might change

    collage = Image.new(
        'RGBA',
        (
            ALImage.WIDTH * len(availability_matrix[0]),
            ALImage.HEIGHT * len(availability_matrix),
        ),
    )
    for ind_group, img_group in enumerate(chara_images):
        i, j = positions[ind_group]
        curr_width = 0
        for img in img_group:
            collage.paste(img, ((j + curr_width) * ALImage.WIDTH, i * ALImage.HEIGHT))  # type: ignore
            curr_width += img.properties.zoom

    collage.save(image_binary, 'WEBP', method=6, quality=80)
    image_binary.seek(0)


def _find_positions(
    sizes: list[tuple[int, int, int, list[int]]], nb_rows: int, nb_columns: int
) -> tuple[list[tuple[int, int]], npt.NDArray[Any]]:
    availability_matrix = np.ones((nb_rows, nb_columns), dtype=bool)
    positions: list[tuple[int, int]] = [(0, 0) for _ in range(len(sizes))]

    # We reverse the list to delete from the end
    sizes.reverse()

    i = 0
    while i < availability_matrix.shape[0]:
        j = 0
        while j < availability_matrix.shape[1]:
            curr_size_i = len(sizes) - 1
            found_position = False
            while not found_position and curr_size_i >= 0:
                found_position = True
                (index, width, height, individual_sizes) = sizes[curr_size_i]
                while i + height - 1 >= availability_matrix.shape[0]:
                    # Last lines, need to make the matrix bigger
                    new_row = np.ones((1, availability_matrix.shape[1]))
                    availability_matrix = np.vstack((availability_matrix, new_row))
                if j + width - 1 < availability_matrix.shape[1]:
                    for i_i in range(height):
                        for j_i in range(width):
                            if not availability_matrix[i + i_i, j + j_i]:
                                found_position = False
                else:
                    found_position = False

                if found_position:
                    positions[index] = (i, j)
                    curr_width = 0
                    for individual_size in individual_sizes:
                        for i_i in range(individual_size):
                            for j_i in range(curr_width, curr_width + individual_size):
                                availability_matrix[i + i_i, j + j_i] = False
                        curr_width += individual_size
                    del sizes[curr_size_i]
                else:
                    curr_size_i -= 1

            j += 1
        i += 1

        if i == availability_matrix.shape[0] and sizes:
            # No more line, need to make the matrix bigger
            new_row = np.ones((1, availability_matrix.shape[1]))
            availability_matrix = np.vstack((availability_matrix, new_row))

    # Cleaning
    h, w = availability_matrix.shape
    for i in range(availability_matrix.shape[0]):
        if availability_matrix[i].all():
            h = i
            break

    for i in range(availability_matrix.shape[1]):
        if availability_matrix[:, i].all():
            w = i
            break

    availability_matrix = availability_matrix[:h, :w]

    return positions, availability_matrix


async def waifu_collage(waifus: list[WAIFU_TYPES]) -> str:
    ids_al = {w.character.id_al for w in waifus}
    charas_data = await chara_select(get_edgedb(), ids_al=list(ids_al))
    charas_dict = {c.id_al: c for c in charas_data}
    charas = [charas_dict[w.character.id_al] for w in waifus]

    _, sorted_waifus = zip(
        *sorted(zip(charas, waifus), key=lambda cw: (-cw[0].favourites, cw[0].id_al, -cw[1].level))
    )

    ordered_waifus = sorted_custom_positions(list(sorted_waifus))

    chara_images: list[list[CharaImage]] = []
    i = 0
    while i < len(ordered_waifus):
        w = ordered_waifus[i]
        if isinstance(w, WAIFU_TYPES):
            curr_group = [
                CharaImage(
                    charas_dict[w.character.id_al], properties=CharaImageProps.from_waifu(w)
                )
            ]
            while _is_left_part_of_waifu_group(ordered_waifus, i):
                i += 1
                w = ordered_waifus[i]
                curr_group.append(
                    CharaImage(
                        charas_dict[w.character.id_al], properties=CharaImageProps.from_waifu(w)
                    )
                )
            chara_images.append(curr_group)
        i += 1

    await CharaImage.load_image_groups(chara_images)

    try:
        with io.BytesIO() as image_binary:
            await asyncio.to_thread(_make_collage, image_binary, chara_images)
            hikari = await to_producer(image_binary, filename=f'wc_{uuid4()}.webp')
            return hikari['url']
    finally:
        for group in chara_images:
            for img in group:
                img.close()


async def chara_collage(ids_al: list[int], hide_no_images: bool = False, blooded: bool = False):
    data = await _chara_collage(tuple(ids_al), hide_no_images=hide_no_images, blooded=blooded)
    with io.BytesIO() as image_binary:
        image_binary.write(data)
        image_binary.seek(0)
        for b in image_binary:
            yield b


@cached(cache=LRUCache(1024))
async def _chara_collage(
    ids_al: tuple[int, ...], hide_no_images: bool = False, blooded: bool = False
) -> bytes:
    charas_data = await chara_select(get_edgedb(), ids_al=list(ids_al))
    chara_dict = {
        c.id_al: c
        for c in charas_data
        if (not hide_no_images) or (not c.image_large.endswith('/default.jpg'))
    }
    charas = [chara_dict.get(id_al) for id_al in ids_al]
    charas = filter(None, charas)

    chara_images: list[list[CharaImage]] = []
    for c in charas:
        image = CharaImage(c)
        if blooded:
            image.set_blooded()
        chara_images.append([image])

    await CharaImage.load_image_groups(chara_images)

    try:
        with io.BytesIO() as image_binary:
            await asyncio.to_thread(_make_collage, image_binary, chara_images)
            image_binary.seek(0)
            return image_binary.read()
    finally:
        for group in chara_images:
            for img in group:
                img.close()


async def chara_album(
    charas: list[CHARA_TYPES], waifus: list[WAIFU_TYPES], owned_only: bool = False
) -> str:
    to_collage: list[CHARA_TYPES | WAIFU_TYPES] = []
    waifu_chara_ids = [w.character.id_al for w in waifus]
    for chara in charas:
        if chara.id_al in waifu_chara_ids:
            current_waifus = [w for w in waifus if w.character.id_al == chara.id_al]
            current_waifus_ascended = [w for w in current_waifus if w.level > 0]
            if current_waifus_ascended:
                to_collage += current_waifus_ascended
            else:
                to_collage.append(current_waifus[0])
        elif not owned_only:
            to_collage.append(chara)

    sorted_to_collage = sorted_custom_positions(to_collage)

    chara_images: list[list[CharaImage]] = []
    chara_map = {c.id_al: c for c in charas}
    i = 0
    while i < len(sorted_to_collage):
        waifu_or_chara = sorted_to_collage[i]
        if isinstance(waifu_or_chara, WAIFU_TYPES):
            curr_group = [
                CharaImage(
                    chara_map[waifu_or_chara.character.id_al],
                    properties=CharaImageProps.from_waifu(waifu_or_chara),
                )
            ]
            while _is_left_part_of_waifu_group(sorted_to_collage, i):
                i += 1
                waifu_or_chara = sorted_to_collage[i]
                curr_group.append(
                    CharaImage(
                        chara_map[waifu_or_chara.character.id_al],
                        properties=CharaImageProps.from_waifu(waifu_or_chara),
                    )
                )
            chara_images.append(curr_group)
        else:
            img = CharaImage(waifu_or_chara)
            img.set_hidden()
            chara_images.append([img])

        i += 1

    await CharaImage.load_image_groups(chara_images)

    try:
        with io.BytesIO() as image_binary:
            await asyncio.to_thread(_make_collage, image_binary, chara_images)
            hikari = await to_producer(image_binary, filename=f'wc_{uuid4()}.webp')
            return hikari['url']
    finally:
        for group in chara_images:
            for img in group:
                img.close()


def _is_left_part_of_waifu_group(waifus: list[WAIFU_TYPES | Any], index: int) -> bool:
    if index + 1 < len(waifus):
        cw = waifus[index]
        nw = waifus[index + 1]
        return (
            isinstance(cw, WAIFU_TYPES)
            and isinstance(nw, WAIFU_TYPES)
            and (
                (
                    cw.custom_position == WaicolleCollagePosition.LEFT_OF
                    and cw.custom_position_waifu is not None
                    and cw.custom_position_waifu.id == nw.id
                )
                or (
                    nw.custom_position == WaicolleCollagePosition.RIGHT_OF
                    and nw.custom_position_waifu is not None
                    and nw.custom_position_waifu.id == cw.id
                )
            )
        )
    return False


@dataclass
class MediaImage(ALImage):
    media: MediaSelectResult

    @override
    async def load_image(self, al_img: bytes | None = None):
        if al_img is not None:
            img = await asyncio.to_thread(load_img, al_img)
        else:
            img = await fetch_img(self.media.cover_image_extra_large)
        self.image = self.crop(img)
        self.image = self.normalize(self.image, 4)

    @classmethod
    async def load_images(cls, images: list[Self]):
        al_images = await image_select(
            get_edgedb(), urls=[img.media.cover_image_extra_large for img in images]
        )
        al_images_dict = {i.url: base64.b64decode(i.data) for i in al_images}
        async with asyncio.TaskGroup() as tg:
            for img in images:
                tg.create_task(
                    img.load_image(al_images_dict.get(img.media.cover_image_extra_large, None))
                )


async def media_collage(ids_al: list[int]):
    data = await _media_collage(tuple(ids_al))
    with io.BytesIO() as image_binary:
        image_binary.write(data)
        image_binary.seek(0)
        for b in image_binary:
            yield b


@cached(cache=LRUCache(1024))
async def _media_collage(ids_al: tuple[int, ...]) -> bytes:
    medias_data = await media_select(get_edgedb(), ids_al=list(ids_al))
    media_dict = {m.id_al: m for m in medias_data}
    medias = [media_dict.get(id_al) for id_al in ids_al]
    medias = filter(None, medias)

    media_images = [MediaImage(m) for m in medias]
    await MediaImage.load_images(media_images)

    try:
        with io.BytesIO() as image_binary:
            await asyncio.to_thread(_make_dumb_collage, image_binary, media_images)
            image_binary.seek(0)
            return image_binary.read()
    finally:
        for img in media_images:
            img.close()


def _make_dumb_collage(image_binary: io.BytesIO, images: Sequence[ALImage]):
    collage = Image.new(
        'RGBA',
        (images[0].width * len(images), images[0].height),
    )
    curr_width = 0
    for img in images:
        collage.paste(img, (curr_width, 0))  # type: ignore
        curr_width += img.width
    collage.save(image_binary, 'WEBP', method=6, quality=80)
    image_binary.seek(0)
