with
  discord_id := <int64>$discord_id,
  moecoins := <optional int32>$moecoins,
  blood_shards := <optional int32>$blood_shards,
  updated := (
    update waicolle::Player
    filter .client = global client and .user.discord_id = discord_id
    set {
      moecoins := .moecoins + (moecoins ?? 0),
      blood_shards := .blood_shards + (blood_shards ?? 0),
      frozen_at := {},
    }
  )
select updated {
  *,
  user: {
    discord_id,
    discord_id_str,
  },
}
