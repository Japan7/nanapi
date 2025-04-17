with
  id_al := <int32>$id_al,
select anilist::Entry {
  status,
  progress,
  score,
  account: {
    user: {
      discord_id,
    },
  }
}
filter .media.id_al = id_al
