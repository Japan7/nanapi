with
  discord_id := <str>$discord_id,
  player := (select waicolle::Player filter .client = global client and .user.discord_id = discord_id),
  id_al := <int32>$id_al,
  staff := (select anilist::Staff filter .id_al = id_al),
  charas := (
    select staff.character_edges.character
    filter any(.image_large not ilike '%/default.jpg')
  ),
  nb_charas := count(charas),
  owned := (
    select waicolle::Waifu
    filter .client = global client
    and .owner = assert_exists(player)
    and .character in charas
    and not .disabled
  ),
  owned_ids := (select owned.character.id_al),
  nb_owned := count(owned_ids),
select {
  staff := assert_exists(staff) {
    id_al,
    name_user_preferred,
    name_native,
  },
  nb_charas := nb_charas,
  nb_owned := nb_owned,
}
