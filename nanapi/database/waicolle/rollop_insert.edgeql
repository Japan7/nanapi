with
  author_discord_id := <int64>$author_discord_id,
  received_ids := <array<uuid>>$received_ids,
  roll_id := <str>$roll_id,
  moecoins := <optional int32>$moecoins ?? 0,
  author := (select waicolle::Player filter .client = global client and .user.discord_id = author_discord_id),
insert waicolle::RollOperation {
  client := global client,
  author := author,
  received := (select waicolle::Waifu filter .id in array_unpack(received_ids)),
  roll_id := roll_id,
  moecoins := moecoins,
}
