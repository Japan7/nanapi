with
  message_id := <str>$message_id,
  data := <json>$data,
  noindex := <optional str>$noindex,
insert discord::Message {
  client := global client,
  data := data,
  guild_id := <str>json_get(data, 'guild_id'),
  channel_id := <str>json_get(data, 'channel_id'),
  message_id := message_id,
  author_id := <str>json_get(data, 'author', 'id'),
  content := <str>json_get(data, 'content'),
  timestamp := <datetime>json_get(data, 'timestamp'),
  edited_timestamp := <datetime>json_get(data, 'edited_timestamp'),
  noindex := noindex,
}
unless conflict on ((.client, .message_id))
else (
  update discord::Message set {
    data := data,
    guild_id := <str>json_get(data, 'guild_id'),
    channel_id := <str>json_get(data, 'channel_id'),
    author_id := <str>json_get(data, 'author', 'id'),
    content := <str>json_get(data, 'content'),
    timestamp := <datetime>json_get(data, 'timestamp'),
    edited_timestamp := <datetime>json_get(data, 'edited_timestamp'),
    noindex := (noindex if noindex != '' else {}) if exists noindex else .noindex,
  }
)
