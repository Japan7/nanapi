with
  discord_id := <str>$discord_id,
  ids := <array<uuid>>$ids,
  player := (select waicolle::Player filter .client = global client and .user.discord_id = discord_id),
  updated := (
    update waicolle::Waifu
    filter .id in array_unpack(ids)
    set {
      timestamp := datetime_current(),
      locked := false,
      custom_collage := false,
      custom_position := waicolle::CollagePosition.DEFAULT,
      owner := player,
      custom_position_waifu := {},
    }
  )
select updated {
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
