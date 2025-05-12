with
  discord_id := <str>$discord_id,
  id := <uuid>$id,
  collection := (select waicolle::Collection filter .id = id),
  _update := (
    update waicolle::Player
    filter .client = global client and .user.discord_id = discord_id
    set {
      tracked_collections += collection,
    }
  )
select {
  player := assert_exists(_update),
  collection := assert_exists(collection) {
    id,
    name,
  },
}
