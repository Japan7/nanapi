with
  id := <uuid>$id,
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
filter .id = id
