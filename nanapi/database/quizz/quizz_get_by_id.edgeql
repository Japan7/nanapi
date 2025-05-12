with
  id := <uuid>$id
select quizz::Quizz {
  *,
  author: {
    discord_id,
  },
}
filter .id = id;
