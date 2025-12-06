select count(
  discord::Message filter
    .author_id = <str>$discord_id
    and .timestamp >= <datetime>$year_start
    and .timestamp < <datetime>$year_end
)
