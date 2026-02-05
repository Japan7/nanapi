with
  discord_id := <optional str>$discord_id,
  player := (select waicolle::Player filter .client = global client and .user.discord_id = discord_id),
  anilist := (select anilist::Account filter .user.discord_id = discord_id),
  pool := (
    select anilist::Character
    filter (
      ((
        .edges.media.entries.account = anilist
        if exists anilist else true
      ) or (
        (.id_al in player.tracked_characters.id_al)
        if exists player else true
      ))
      and
      any(.image_large not ilike '%/default.jpg')
    )
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
  ) if exists player else pool
group genred {
  id_al,
}
by .rank
