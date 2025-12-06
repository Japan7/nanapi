with
  year_start := <datetime>$year_start,
  year_end := <datetime>$year_end,
  player := (
    select waicolle::Player
    filter .user.discord_id = <str>$discord_id
       and .client = global client
  ),
  trades_as_author := (
    select player.<author[is waicolle::TradeOperation]
    filter .created_at >= year_start and .created_at < year_end
       and exists .completed_at
  ),
  trades_as_offeree := (
    select player.<offeree[is waicolle::TradeOperation]
    filter .created_at >= year_start and .created_at < year_end
       and exists .completed_at
  )
select {
  total_trades := count(trades_as_author) + count(trades_as_offeree),
  trades_as_author := count(trades_as_author),
  trades_as_offeree := count(trades_as_offeree),
  total_offered := count(trades_as_author.offered),
  total_received := count(trades_as_author.received),
  # Use for loop to preserve duplicates when aggregating partner IDs
  partners_as_author := array_agg((for t in trades_as_author union t.offeree.user.discord_id)),
  partners_as_offeree := array_agg((for t in trades_as_offeree union t.author.user.discord_id)),
}
