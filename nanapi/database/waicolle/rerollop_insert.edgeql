with
  author_discord_id := <int64>$author_discord_id,
  received_ids := <array<uuid>>$received_ids,
  rerolled_ids := <array<uuid>>$rerolled_ids,
  author := (select waicolle::Player filter .client = global client and .user.discord_id = author_discord_id),
insert waicolle::RerollOperation {
  client := global client,
  author := author,
  received := (select waicolle::Waifu filter .id in array_unpack(received_ids)),
  rerolled := (select waicolle::Waifu filter .id in array_unpack(rerolled_ids)),
}
