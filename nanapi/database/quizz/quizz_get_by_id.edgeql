with
  id := <uuid>$id
select quizz::Quizz {
  *,
  author: {
    discord_id,
    discord_id_str,
  },
}
filter .id = id;
