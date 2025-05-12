with
  discord_id := <str>$discord_id,
  id_al := <int32>$id_al,
  media := (select anilist::Media filter .id_al = id_al),
update waicolle::Player
filter .client = global client and .user.discord_id = discord_id
set {
  tracked_items -= media,
}
