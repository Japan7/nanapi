with
  ids := <array<uuid>>$ids,
select waicolle::Waifu {
  *,
  character: { id_al },
  owner: {
    user: {
      discord_id,
    },
  },
  original_owner: {
    user: {
      discord_id,
    },
  },
  custom_position_waifu: { id },
}
filter .id in array_unpack(ids)
