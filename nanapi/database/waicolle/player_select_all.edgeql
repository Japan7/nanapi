select waicolle::Player {
  *,
  user: {
    discord_id,
  },
}
filter .client = global client
