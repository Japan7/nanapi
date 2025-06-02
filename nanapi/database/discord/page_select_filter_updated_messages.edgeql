select discord::MessagePage {
  id,
  messages: { data, deleted_at, noindex }
}
filter .client = global client
and any(.messages.edited_timestamp > .updated_at or .messages.deleted_at > .updated_at)
