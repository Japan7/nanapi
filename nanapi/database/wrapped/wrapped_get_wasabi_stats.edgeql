with
    discord_id := <str>$discord_id,
    year_start := <datetime>$year_start,
    year_end := <datetime>$year_end,
    # Find player by discord_id and client (uses backlink for efficiency)
    player := (select waicolle::Player filter .user.discord_id = discord_id and .client = global client),
    wasabi_rolls := (
        select player.<author[is waicolle::RollOperation]
        filter
            .created_at >= year_start
            and .created_at < year_end
            and .reason = 'wasabi'
    )
select {
    total_rolls := count(wasabi_rolls),
    ranks := array_agg(wasabi_rolls.received.character.rank),
}
