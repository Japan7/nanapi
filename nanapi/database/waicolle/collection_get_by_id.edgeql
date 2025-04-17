with
  id := <uuid>$id,
select waicolle::Collection {
  id,
  name,
  author: {
    user: {
      discord_id,
    },
  },
  medias_ids_al := .items[is anilist::Media].id_al,
  staffs_ids_al := .items[is anilist::Staff].id_al,
  characters_ids_al := .characters.id_al,
}
filter .id = id
