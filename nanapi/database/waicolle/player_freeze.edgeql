with
  discord_id := <int64>$discord_id,
update waicolle::Player
filter .client = global client and .user.discord_id = discord_id
set {
  frozen_at := datetime_current(),
}
