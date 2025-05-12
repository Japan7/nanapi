with
  status := <quizz::Status>$status,
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
filter .client = global client and .status = status
