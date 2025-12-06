with
  year_start := <datetime>$year_start,
  year_end := <datetime>$year_end,
  messages := (
    select discord::Message
    filter .content ilike '%Conditional drop%'
       and .content ilike '%<@' ++ <str>$discord_id ++ '>%'
       and .timestamp >= year_start
       and .timestamp < year_end
  )
select {
  total := count(messages),
  contents := array_agg(messages.content),
}
