with
  channel_id := <int64>$channel_id
select quizz::Quizz {
  *,
  author: {
    discord_id,
    discord_id_str,
  },
}
filter .client = global client and not exists .game and .channel_id = channel_id
order by .submitted_at
limit 1
