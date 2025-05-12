with
  channel_id := <str>$channel_id
select quizz::Quizz {
  *,
  author: {
    discord_id,
  },
}
filter .client = global client and not exists .game and .channel_id = channel_id
order by .submitted_at
limit 1
