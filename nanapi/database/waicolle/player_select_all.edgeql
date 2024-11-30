select waicolle::Player {
  *,
  user: {
    discord_id,
    discord_id_str,
  },
}
filter .client = global client
