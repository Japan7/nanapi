with
  items := <array<tuple<message_id: str, noindex: str>>>$items,
for item in array_unpack(items)
union (
  update discord::Message
  filter .client = global client and .message_id = item.message_id
  set {
    noindex := item.noindex if item.noindex != '' else {}
  }
)
