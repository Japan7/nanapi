with
  id_al := <int32>$id_al,
  character := (select anilist::Character filter .id_al = id_al),
select waicolle::Player {
  *,
  user: {
    discord_id,
  },
}
filter .client = global client
and character in .tracked_characters
