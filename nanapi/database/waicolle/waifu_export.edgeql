with
  players := (select waicolle::Player filter .client = global client),
  waifus := (select waicolle::Waifu filter .client = global client and not .disabled),
  charas := (select anilist::Character filter .id_al in waifus.character.id_al),
select {
  players := players {
    discord_id := .user.discord_id_str,
    discord_username := .user.discord_username,
    tracked := .tracked_characters.id_al
  },
  waifus := waifus {
    id,
    character_id := .character.id_al,
    owner_discord_id := .owner.user.discord_id_str,
    original_owner_discord_id := .original_owner.user.discord_id_str,
    timestamp,
    level,
    locked,
    nanaed,
    blooded,
    trade_locked,
  },
  charas := charas {
    id_al,
    image := str_split(.image_large, '/')[-1],
    favourites,
  },
}
