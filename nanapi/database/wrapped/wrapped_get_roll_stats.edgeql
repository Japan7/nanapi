with
  discord_id := <str>$discord_id,
  year_start := <datetime>$year_start,
  year_end := <datetime>$year_end,
  # Find player by discord_id and client
  player := (select waicolle::Player filter .user.discord_id = discord_id and .client = global client),
  # Paid rolls (A-H + daily/weekly) for this player in the year
  paid_rolls := (
    select player.<author[is waicolle::RollOperation]
    filter
      .reason in {'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'daily', 'weekly'}
      and .created_at >= year_start
      and .created_at < year_end
  )
select {
  total_rolls := count(paid_rolls),
  total_moecoins := sum(paid_rolls.moecoins),
  total_waifus := count(paid_rolls.received),
  # Return reasons as array - counting done in Python for performance
  reasons := array_agg(paid_rolls.reason),
}
