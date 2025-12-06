with
    discord_id := <str>$discord_id,
    year_start := <datetime>$year_start,
    year_end := <datetime>$year_end,
    daily_tag_messages := (
        select discord::Message
        filter
            .timestamp >= year_start
            and .timestamp < year_end
            and .content like 'Rolling %'
            and .content like '%Daily tag%'
            and <str>json_get(.data, 'interaction', 'user', 'id') ?? '' = discord_id
    )
select {
    total_rolls := count(daily_tag_messages),
    contents := array_agg(daily_tag_messages.content),
}
