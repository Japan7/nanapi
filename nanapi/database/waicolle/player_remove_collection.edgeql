with
  discord_id := <str>$discord_id,
  id := <uuid>$id,
  collection := (select waicolle::Collection filter .id = id),
update waicolle::Player
filter .client = global client and .user.discord_id = discord_id
set {
  tracked_collections -= collection,
}
