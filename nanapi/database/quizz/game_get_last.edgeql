with
  channel_id := <int64>$channel_id,
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
filter .client = global client and .quizz.channel_id = channel_id and .status = quizz::Status.ENDED
order by .ended_at desc
limit 1
