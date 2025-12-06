with
    discord_id := <str>$discord_id,
    year_start := <datetime>$year_start,
    year_end := <datetime>$year_end,
    wasabi_messages := (
        select discord::Message
        filter
            .timestamp >= year_start
            and .timestamp < year_end
            and .content like '%[**Wasabi**]%'
            and .content like '%You received%character%'
            and <str>json_get(.data, 'mentions', '0', 'id') ?? '' = discord_id
    )
select {
    total_wasabi := count(wasabi_messages),
    contents := array_agg(wasabi_messages.content),
}
