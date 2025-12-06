with
  year_start := <datetime>$year_start,
  year_end := <datetime>$year_end,
  community_messages := (
    select discord::Message
    filter .author_id != <str>$discord_id
       and .timestamp >= year_start
       and .timestamp < year_end
       and len(.content) > 0
    limit 50000
  )
select {
  community_contents := array_agg(community_messages.content),
}
