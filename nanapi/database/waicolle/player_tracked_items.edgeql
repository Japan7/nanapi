with
  discord_id := <str>$discord_id,
  player := (select waicolle::Player filter .client = global client and .user.discord_id = discord_id),
select assert_exists(player) {
  tracked_medias := .tracked_items[is anilist::Media] {
    id_al,
  },
  tracked_staffs := .tracked_items[is anilist::Staff] {
    id_al,
  },
  tracked_collections: {
    id,
  },
}
