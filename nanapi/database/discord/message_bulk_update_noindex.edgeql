with
  items := <array <json>>$items,
for item in array_unpack(items)
union (
  with
    message_id := <str>json_get(item, 'message_id'),
    noindex := <str>json_get(item, 'noindex'),
  update discord::Message
  filter .client = global client and .message_id = message_id
  set {
    noindex := noindex if noindex != '' else {}
  }
)
