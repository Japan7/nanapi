with
  discord_id := <str>$discord_id,
  year_start := <datetime>$year_start,
  year_end := <datetime>$year_end,
  # Find player by discord_id and client
  player := (select waicolle::Player filter .user.discord_id = discord_id and .client = global client),
  # Reroll operations for this player in the year
  rerolls := (
    select player.<author[is waicolle::RerollOperation]
    filter
      .created_at >= year_start
      and .created_at < year_end
  )
select {
  total_rerolls := count(rerolls),
  total_rerolled := sum(count(rerolls.rerolled)),
  total_received := sum(count(rerolls.received)),
  # Single rerolls (exactly 1 waifu rerolled)
  single_rerolls := count((select rerolls filter count(.rerolled) = 1)),
  single_success := count((select rerolls filter count(.rerolled) = 1 and count(.received) = 1)),
}
