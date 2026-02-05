with
  discord_id := <str>$discord_id,
  player := (select waicolle::Player filter .client = global client and .user.discord_id = discord_id),
  id := <uuid>$id,
  collec := (select waicolle::Collection filter .id = id),
  charas := (
    select collec.characters
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
  collection := assert_exists(collec) {
    id,
    name,
    author: {
      user: {
        discord_id,
      },
    },
    medias := .items[is anilist::Media] {
      type,
      id_al,
      title_user_preferred,
    },
    staffs := .items[is anilist::Staff] {
      id_al,
      name_user_preferred,
      name_native,
    },
  },
  nb_charas := nb_charas,
  nb_owned := nb_owned,
}
