with
  channel_id := <str>$channel_id
select quizz::Quizz {
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
filter .client = global client and not exists .game and .channel_id = channel_id
order by .submitted_at
limit 1
