with
  message_id := <str>$message_id,
  noindex := <str>$noindex,
update discord::Message
filter .client = global client and .message_id = message_id
set {
  noindex := noindex if noindex != '' else {}
}
