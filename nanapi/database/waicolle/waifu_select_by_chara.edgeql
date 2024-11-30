with
  id_al := <int32>$id_al,
select waicolle::Waifu {
  id,
  timestamp,
  trade_locked,
  level,
  locked,
  blooded,
  nanaed,
  custom_image,
  custom_name,
  custom_collage,
  custom_position,
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
filter .client = global client
and .character.id_al = id_al
and not .disabled
order by .timestamp desc
