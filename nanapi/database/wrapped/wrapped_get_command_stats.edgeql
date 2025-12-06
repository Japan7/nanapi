with
  discord_id := <str>$discord_id,
  year_start := <datetime>$year_start,
  year_end := <datetime>$year_end,
  # Commands used by this user (from any bot's response messages)
  command_messages := (
    select discord::Message {
      cmd_name := <str>json_get(.data, 'interaction', 'name') ?? ''
    }
    filter
      .timestamp >= year_start
      and .timestamp < year_end
      and <str>json_get(.data, 'interaction', 'user', 'id') ?? '' = discord_id
  )
select {
  command_distribution := (
    with command_groups := (
      group command_messages
      using command_name := .cmd_name
      by command_name
    )
    select command_groups {
      command_name := .key.command_name,
      count := count(.elements)
    }
    order by count(.elements) desc
    limit 10
  ),
}
