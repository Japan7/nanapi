with
  channel_id := <str>$channel_id,
  games := (
    select quizz::Game
    filter .client = global client and .quizz.channel_id = channel_id and .status = quizz::Status.STARTED
  )
select assert_single(games) {
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
