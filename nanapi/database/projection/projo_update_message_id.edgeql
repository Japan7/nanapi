with
  id := <uuid>$id,
  message_id := <str>$message_id,
update projection::Projection
filter .id = id
set { message_id := message_id }
