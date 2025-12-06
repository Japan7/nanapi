with
  messages := (
    select discord::Message
    filter
      .author_id = <str>$discord_id
      and .timestamp >= <datetime>$year_start
      and .timestamp < <datetime>$year_end
  ),
  # Extract all custom emotes from message content
  # Discord custom emotes format: <:name:id> or <a:name:id> (animated)
  emote_matches := (
    for msg in messages
    union (
      for m in re_match_all('<a?:([^:]+):[0-9]+>', msg.content)
      union m
    )
  ),
  # Group emotes by name and count occurrences
  emote_groups := (
    group emote_matches
    using name := emote_matches[0]
    by name
  )
select {
  total_emote_count := count(emote_matches),
  # Return emote counts grouped by name (sorted by count in Python)
  emote_counts := (
    select emote_groups {
      name := .key.name,
      count := count(.elements)
    }
  ),
}
