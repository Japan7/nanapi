with
  ids_al := <array<int32>>$ids_al,
  discord_id := <optional str>$discord_id,
  genred := <optional bool>$genred ?? false,
  player := (select waicolle::Player filter .client = global client and .user.discord_id = discord_id),
  medias := (select anilist::Media filter .id_al in array_unpack(ids_al)),
  pool := (
    select anilist::Character
    filter .edges.media in medias and any(.image_large not ilike '%/default.jpg')
  ),
genred := (
    select pool
    filter (
      re_test(r"(?i)\y(?:female|non-binary)\y", .fuzzy_gender)
      if player.game_mode = waicolle::GameMode.WAIFU else
      re_test(r"(?i)\y(?:male|non-binary)\y", .fuzzy_gender)
      if player.game_mode = waicolle::GameMode.HUSBANDO else
      true
    )
  ) if genred and exists player else pool
group genred {
  id_al,
}
by .rank
