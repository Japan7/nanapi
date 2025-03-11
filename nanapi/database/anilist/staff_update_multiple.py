from typing import Any
from uuid import UUID

import orjson
from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  staffs := <json>$staffs,
  last_update := <int64>$last_update
for staff in json_array_unpack(staffs) union (
  with
    id_al := <int32>json_get(staff, 'id_al'),
    favourites := <int32>json_get(staff, 'favourites'),
    site_url := <str>json_get(staff, 'site_url'),
    name_user_preferred := <str>json_get(staff, 'name_user_preferred'),
    name_alternative := <array<str>>json_get(staff, 'name_alternative'),
    name_native := <str>json_get(staff, 'name_native'),
    description := <str>json_get(staff, 'description'),
    image_large := <str>json_get(staff, 'image_large'),
    gender := <str>json_get(staff, 'gender'),
    age := <int32>json_get(staff, 'age'),
    date_of_birth_year := <int32>json_get(staff, 'date_of_birth_year'),
    date_of_birth_month := <int32>json_get(staff, 'date_of_birth_month'),
    date_of_birth_day := <int32>json_get(staff, 'date_of_birth_day'),
    date_of_death_year := <int32>json_get(staff, 'date_of_death_year'),
    date_of_death_month := <int32>json_get(staff, 'date_of_death_month'),
    date_of_death_day := <int32>json_get(staff, 'date_of_death_day'),
  insert anilist::Staff {
    id_al := id_al,
    last_update := last_update,
    favourites := favourites,
    site_url := site_url,
    name_user_preferred := name_user_preferred,
    name_alternative := name_alternative,
    name_native := name_native,
    description := description,
    image_large := image_large,
    gender := gender,
    age := age,
    date_of_birth_year := date_of_birth_year,
    date_of_birth_month := date_of_birth_month,
    date_of_birth_day := date_of_birth_day,
    date_of_death_year := date_of_death_year,
    date_of_death_month := date_of_death_month,
    date_of_death_day := date_of_death_day,
  }
  unless conflict on .id_al
  else (
    update anilist::Staff set {
      last_update := last_update,
      favourites := favourites,
      site_url := site_url,
      name_user_preferred := name_user_preferred,
      name_alternative := name_alternative,
      name_native := name_native,
      description := description,
      image_large := image_large,
      gender := gender,
      age := age,
      date_of_birth_year := date_of_birth_year,
      date_of_birth_month := date_of_birth_month,
      date_of_birth_day := date_of_birth_day,
      date_of_death_year := date_of_death_year,
      date_of_death_month := date_of_death_month,
      date_of_death_day := date_of_death_day,
    }
  )
)
"""


class StaffUpdateMultipleResult(BaseModel):
    id: UUID


adapter = TypeAdapter(list[StaffUpdateMultipleResult])


async def staff_update_multiple(
    executor: AsyncIOExecutor,
    *,
    staffs: Any,
    last_update: int,
) -> list[StaffUpdateMultipleResult]:
    resp = await executor.query_json(
        EDGEQL_QUERY,
        staffs=orjson.dumps(staffs).decode(),
        last_update=last_update,
    )
    return adapter.validate_json(resp, strict=False)
