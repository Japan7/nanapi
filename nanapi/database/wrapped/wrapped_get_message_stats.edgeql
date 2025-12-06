with
  tz := <str>$timezone,
  discord_id := <str>$discord_id,
  year_start := <datetime>$year_start,
  year_end := <datetime>$year_end,
  messages := (
    select discord::Message
    filter
      .author_id = discord_id
      and .timestamp >= year_start
      and .timestamp < year_end
  ),
  sorted_msgs := (select messages order by .timestamp),
  timestamps := array_agg((select sorted_msgs.timestamp)),
  gap_info := (
    for i in range_unpack(range(0, len(timestamps) - 1))
    union (
      select {
        gap := timestamps[i + 1] - timestamps[i],
        gap_start := timestamps[i],
      }
    )
  ),
  longest_gap := (select gap_info order by .gap desc limit 1)
select {
  total_count := count(messages),
  total_length := sum(len(messages.content)),
  total_words := sum(len(str_split(messages.content, ' '))),
  attachment_count := count(
    messages filter json_typeof(.data['attachments']) = 'array'
      and len(<array<json>>.data['attachments']) > 0
  ),
  link_count := count(
    messages filter (
      re_test('https?://', .content)
      or (
        json_typeof(.data['embeds']) = 'array'
        and len(<array<json>>.data['embeds']) > 0
      )
    )
  ),
  mention_count := sum(
    len(<array<json>>(messages.data['mentions'] ?? <json>[]))
  ),
  everyone_count := count(
    messages filter .data['mention_everyone'] = <json>true
  ),
  longest_silence_seconds := <optional int64>(
    duration_get(longest_gap.gap, 'totalseconds')
  ),
  longest_silence_start := longest_gap.gap_start,
  hour_distribution := (
    with hour_groups := (
      group messages
      using hour := <int64>datetime_get(
        cal::to_local_datetime(.timestamp, tz), 'hour'
      )
      by hour
    )
    select hour_groups {
      hour := .key.hour,
      count := count(.elements)
    }
  ),
  weekday_distribution := (
    with weekday_groups := (
      group messages
      using weekday := <int64>datetime_get(
        cal::to_local_datetime(.timestamp, tz), 'dow'
      )
      by weekday
    )
    select weekday_groups {
      weekday := .key.weekday,
      count := count(.elements)
    }
  ),
  day_distribution := (
    with day_groups := (
      group messages
      using day := <int64>datetime_get(
        cal::to_local_datetime(.timestamp, tz), 'doy'
      )
      by day
    )
    select day_groups {
      day := .key.day,
      count := count(.elements)
    }
  ),
  month_distribution := (
    with month_groups := (
      group messages
      using month := <int64>datetime_get(
        cal::to_local_datetime(.timestamp, tz), 'month'
      )
      by month
    )
    select month_groups {
      month := .key.month,
      count := count(.elements)
    }
  ),
  channel_distribution := (
    with channel_groups := (
      group messages
      using channel_id := .channel_id
      by channel_id
    )
    select channel_groups {
      channel_id := .key.channel_id,
      count := count(.elements)
    }
    order by count(.elements) desc
    limit 5
  ),
}
