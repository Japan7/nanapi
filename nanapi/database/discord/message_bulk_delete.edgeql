with
  message_ids := <array<str>>$message_ids,
update discord::Message
filter .client = global client
and .message_id in array_unpack(message_ids)
and not exists(.deleted_at)
set {
  deleted_at := datetime_of_transaction(),
}
