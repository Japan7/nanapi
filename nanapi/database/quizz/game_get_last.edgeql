with
  channel_id := <str>$channel_id,
select quizz::Game {
  id,
  status,
  message_id,
  answer_bananed,
  started_at,
  ended_at,
  winner: {
    discord_id,
  },
  quizz: {
    id,
    channel_id,
    description,
    url,
    is_image,
    answer,
    answer_source,
    submitted_at,
    hikaried,
    author: {
      discord_id,
    },
  }
}
filter .client = global client and .quizz.channel_id = channel_id and .status = quizz::Status.ENDED
order by .ended_at desc
limit 1
