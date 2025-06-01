with
  id := <uuid>$id,
  context := <str>$context,
  message_ids := <array<str>>$message_ids,
  messages := (
    select discord::Message
    filter .client = global client and .message_id in array_unpack(message_ids)
  )
update discord::MessagePage
filter .id = id
set {
  context := context,
  messages := messages,
}
