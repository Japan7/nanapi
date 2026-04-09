with
  guild_id := <str>$guild_id,
  channel_ids := <array<str>>$channel_ids,
  messages := (
    select discord::Message
    filter .client = global client
    and .guild_id = guild_id
    and .channel_id in array_unpack(channel_ids)
  ),
  groups := (
    group messages
    using channel_id := .channel_id
    by channel_id
  )
select groups {
  channel_id := .key.channel_id,
  latest_timestamp := max(.elements.timestamp),
}
