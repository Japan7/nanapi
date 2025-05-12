with
  channel_id := <str>$channel_id,
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
filter .client = global client and .quizz.channel_id = channel_id and .status = quizz::Status.ENDED
order by .ended_at desc
limit 1
