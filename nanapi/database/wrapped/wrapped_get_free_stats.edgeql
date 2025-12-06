with
  discord_id := <str>$discord_id,
  year_start := <datetime>$year_start,
  year_end := <datetime>$year_end,
  # Find player by discord_id and client
  player := (select waicolle::Player filter .user.discord_id = discord_id and .client = global client),
  # Free drop rolls (event + coupon) for this player in the year
  free_rolls := (
    select player.<author[is waicolle::RollOperation]
    filter
      .reason in {'event', 'coupon'}
      and .created_at >= year_start
      and .created_at < year_end
  )
select {
  event_count := count((select free_rolls filter .reason = 'event')),
  coupon_count := count((select free_rolls filter .reason = 'coupon')),
  # Return ranks as array - counting done in Python for performance
  ranks := array_agg(free_rolls.received.character.rank),
}
