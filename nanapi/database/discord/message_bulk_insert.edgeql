with
  messages := <array <json>>$messages,
for data in array_unpack(messages) union (
  with
    message_id := <str>json_get(data, 'id'),
  insert discord::Message {
    client := global client,
    message_id := message_id,
    data := data,
  }
  unless conflict on ((.client, .message_id))
)
