with
  context := <str>$context,
  channel_id := <str>$channel_id,
  message_ids := <array<str>>$message_ids,
  messages := (
      select discord::Message
      filter .client = global client and .message_id in array_unpack(message_ids)
  )
insert discord::MessagePage {
  client := global client,
  context := context,
  channel_id := channel_id,
  messages := messages,
}
