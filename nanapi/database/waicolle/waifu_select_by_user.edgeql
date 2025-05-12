with
  discord_id := <str>$discord_id,
  characters_ids_al := <optional array<int32>>$characters_ids_al,
  level := <optional int32>$level,
  locked := <optional bool>$locked,
  trade_locked := <optional bool>$trade_locked,
  blooded := <optional bool>$blooded,
  nanaed := <optional bool>$nanaed,
  custom_collage := <optional bool>$custom_collage,
  ascended := <optional bool>$ascended,
  as_og := <optional bool>$as_og ?? false,
  disabled := <optional bool>$disabled ?? false,
  player := (select waicolle::Player filter .client = global client and .user.discord_id = discord_id),
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
filter .client = global client
and (.owner = assert_exists(player) if not as_og else .original_owner = assert_exists(player))
and (.character.id_al in array_unpack(characters_ids_al) if exists characters_ids_al else true)
and (.level = level if exists level else true)
and (.locked = locked if exists locked else true)
and (.trade_locked = trade_locked if exists trade_locked else true)
and (.blooded = blooded if exists blooded else true)
and (.nanaed = nanaed if exists nanaed else true)
and (.custom_collage = custom_collage if exists custom_collage else true)
and (.level > 0 if exists ascended else true)
and .disabled = disabled
order by .timestamp desc
