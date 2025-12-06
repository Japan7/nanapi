with
  discord_id := <str>$discord_id,
  year_start := <datetime>$year_start,
  year_end := <datetime>$year_end,
  messages := (
    select discord::Message
    filter
      .author_id = discord_id
      and .timestamp >= year_start
      and .timestamp < year_end
  ),
  link_messages := (
    select messages
    filter re_test('https?://', .content)
  )
select {
  total_link_count := count(link_messages),
  # YouTube (youtube.com, youtu.be)
  youtube_count := count(
    link_messages filter re_test('https?://(www\\.)?(youtube\\.com|youtu\\.be)', .content)
  ),
  # Twitter/X (x.com, twitter.com, vxtwitter, fixupx, fxtwitter, fixvx)
  twitter_count := count(
    link_messages filter re_test('https?://(www\\.)?(x\\.com|twitter\\.com|vxtwitter\\.com|fixupx\\.com|fxtwitter\\.com|fixvx\\.com|girlcockx\\.com)', .content)
  ),
  # Reddit (reddit.com, vxreddit)
  reddit_count := count(
    link_messages filter re_test('https?://(www\\.)?(reddit\\.com|vxreddit\\.com|old\\.reddit\\.com)', .content)
  ),
  # Bluesky
  bluesky_count := count(
    link_messages filter re_test('https?://(www\\.)?bsky\\.app', .content)
  ),
  # Tenor (GIFs)
  tenor_count := count(
    link_messages filter re_test('https?://(www\\.)?tenor\\.com', .content)
  ),
  # Discord
  discord_count := count(
    link_messages filter re_test('https?://(www\\.)?(discord\\.com|cdn\\.discordapp\\.com|media\\.discordapp\\.net)', .content)
  ),
  # GitHub
  github_count := count(
    link_messages filter re_test('https?://(www\\.)?github\\.com', .content)
  ),
  # AniList
  anilist_count := count(
    link_messages filter re_test('https?://(www\\.)?anilist\\.co', .content)
  ),
  # Instagram
  instagram_count := count(
    link_messages filter re_test('https?://(www\\.)?(instagram\\.com|kkinstagram\\.com|ddinstagram\\.com)', .content)
  ),
  # Wikipedia
  wikipedia_count := count(
    link_messages filter re_test('https?://[a-z]{2}\\.wikipedia\\.org', .content)
  ),
  # Steam
  steam_count := count(
    link_messages filter re_test('https?://(www\\.)?store\\.steampowered\\.com', .content)
  ),
}
