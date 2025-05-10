with
  id := <uuid>$id,
select quizz::Game {
  *,
  winner: {
    discord_id,
    discord_id_str,
  },
  quizz: {
    *,
    author: {
      discord_id,
      discord_id_str,
    },
  }
}
filter .id = id
