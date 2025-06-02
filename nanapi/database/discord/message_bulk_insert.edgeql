with
  messages := <array <json>>$messages,
for data in array_unpack(messages) union (
  insert discord::Message {
    client := global client,
    data := data,
    guild_id := <str>json_get(data, 'guild_id'),
    channel_id := <str>json_get(data, 'channel_id'),
    message_id := <str>json_get(data, 'id'),
    author_id := <str>json_get(data, 'author', 'id'),
    content := <str>json_get(data, 'content'),
    timestamp := <datetime>json_get(data, 'timestamp'),
    edited_timestamp := <datetime>json_get(data, 'edited_timestamp'),
  }
  unless conflict on ((.client, .message_id))
)
