with
  message_id := <str>$message_id,
select poll::Poll {
  message_id,
  channel_id,
  question,
  options: {
    rank,
    text,
    votes: {
      user: {
        discord_id,
      }
    }
  }
}
filter .message_id = message_id
