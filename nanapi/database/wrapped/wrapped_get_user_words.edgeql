with
  year_start := <datetime>$year_start,
  year_end := <datetime>$year_end,
  user_messages := (
    select discord::Message
    filter .author_id = <str>$discord_id
       and .timestamp >= year_start
       and .timestamp < year_end
       and len(.content) > 0
  )
select {
  user_contents := array_agg(user_messages.content),
}
