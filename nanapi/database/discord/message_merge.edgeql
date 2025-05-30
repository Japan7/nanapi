with
  message_id := <str>$message_id,
  data := <json>$data,
insert discord::Message {
  client := global client,
  message_id := message_id,
  data := data,
}
unless conflict on ((.client, .message_id))
else (
  update discord::Message set {
    data := data,
  }
)
