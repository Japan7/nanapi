with
  discord_id := <str>$discord_id,
  year_start := <datetime>$year_start,
  year_end := <datetime>$year_end,
  # Find player by discord_id and client
  player := (select waicolle::Player filter .user.discord_id = discord_id and .client = global client),
  # Random drop rolls for this player in the year (using backlink for efficiency)
  drop_rolls := (
    select player.<author[is waicolle::RollOperation]
    filter
      .reason = 'random'
      and .created_at >= year_start
      and .created_at < year_end
  )
select {
  total_drops := count(drop_rolls),
  # Return ranks as array - counting done in Python for performance
  ranks := array_agg(drop_rolls.received.character.rank),
}
