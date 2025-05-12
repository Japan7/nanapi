with
  discord_id := <str>$discord_id,
  id_al := <int32>$id_al,
  media := (select anilist::Media filter .id_al = id_al),
  _update := (
    update waicolle::Player
    filter .client = global client and .user.discord_id = discord_id
    set {
      tracked_items += media,
    }
  )
select {
  player := assert_exists(_update),
  media := assert_exists(media) {
    id_al,
    type,
    title_user_preferred,
  },
}
