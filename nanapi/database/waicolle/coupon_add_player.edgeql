with
  code := <str>$code,
  discord_id := <str>$discord_id,
  player := (select waicolle::Player filter .client = global client and .user.discord_id = discord_id),
update waicolle::Coupon
filter .client = global client and .code = code
set {
  claimed_by += player,
}
