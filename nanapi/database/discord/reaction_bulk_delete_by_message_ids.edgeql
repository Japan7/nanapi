with
  message_ids := <array<str>>$message_ids,
delete discord::Reaction
filter .client = global client
and .message.message_id in array_unpack(message_ids)
