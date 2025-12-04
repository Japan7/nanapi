with
  channel_id := <optional str>$channel_id,
  guild_id := <optional str>$guild_id,
  start_date := <optional datetime>$start_date,
  end_date := <optional datetime>$end_date,
select discord::Message {
  content,
  channel_id,
  guild_id,
  author_id,
  timestamp,
}
filter
  (.channel_id = channel_id if exists channel_id else true) and
  (.guild_id = guild_id if exists guild_id else true) and
  (.timestamp >= start_date if exists start_date else true) and
  (.timestamp <= end_date if exists end_date else true) and
  not exists .deleted_at and
  not exists .noindex and
  len(.content) > 0
order by .timestamp desc

