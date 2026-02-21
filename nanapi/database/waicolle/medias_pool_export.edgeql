with
  ids_al := <array<int32>>$ids_al,
  medias := (select anilist::Media filter .id_al in array_unpack(ids_al)),
  pool := (
    select anilist::Character
    filter any(.edges.media in medias) and .image_large not ilike '%/default.jpg'
  ),
select pool {
  id_al,
  image := str_split(.image_large, '/')[-1],
  favourites,
}
