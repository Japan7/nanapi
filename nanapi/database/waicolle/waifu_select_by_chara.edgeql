with
  id_al := <int32>$id_al,
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
and .character.id_al = id_al
and not .disabled
order by .timestamp desc
