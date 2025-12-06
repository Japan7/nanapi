with
  discord_id := <str>$discord_id,
  year_start := <datetime>$year_start,
  year_end := <datetime>$year_end,
  # Find all wordle result messages
  wordle_messages := (
    select discord::Message {
      content,
      timestamp
    }
    filter
      .timestamp >= year_start
      and .timestamp < year_end
      and .content ilike "**Your group is on a%"
  )
select {
  messages := wordle_messages {
    content,
    timestamp
  },
  discord_id_pattern := '<@' ++ discord_id ++ '>',
}
