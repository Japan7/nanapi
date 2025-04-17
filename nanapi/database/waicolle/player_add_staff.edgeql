with
  discord_id := <str>$discord_id,
  id_al := <int32>$id_al,
  staff := (select anilist::Staff filter .id_al = id_al),
  _update := (
    update waicolle::Player
    filter .client = global client and .user.discord_id = discord_id
    set {
      tracked_items += staff,
    }
  )
select {
  player := assert_exists(_update),
  staff := assert_exists(staff) {
    id_al,
    name_user_preferred,
    name_native,
  },
}
