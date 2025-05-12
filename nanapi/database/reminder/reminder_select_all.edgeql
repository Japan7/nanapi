select reminder::Reminder {
  id,
  channel_id,
  message,
  timestamp,
  user: {
    discord_id,
  },
}
filter .client = global client
