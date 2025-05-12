with
  id := <uuid>$id,
select quizz::Game {
  *,
  winner: {
    discord_id,
  },
  quizz: {
    *,
    author: {
      discord_id,
    },
  }
}
filter .id = id
