with
  ids := <array<uuid>>$ids,
  locked := <optional bool>$locked,
  blooded := <optional bool>$blooded,
  nanaed := <optional bool>$nanaed,
  level := <optional int32>$level,
  custom_collage := <optional bool>$custom_collage,
  timestamp := <optional datetime>$timestamp,
  updated := (
    update waicolle::Waifu
    filter .id in array_unpack(ids)
    set {
      locked := locked ?? .locked,
      blooded := blooded ?? .blooded,
      nanaed := nanaed ?? .nanaed,
      level := level ?? .level,
      custom_collage := custom_collage ?? .custom_collage,
      timestamp := timestamp ?? .timestamp,
    }
  )
select updated {
  *,
  character: { id_al },
  owner: {
    user: {
      discord_id,
      discord_id_str,
    },
  },
  original_owner: {
    user: {
      discord_id,
      discord_id_str,
    },
  },
  custom_position_waifu: { id },
}
