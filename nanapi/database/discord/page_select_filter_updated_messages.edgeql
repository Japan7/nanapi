select discord::MessagePage {
  id,
  messages: { data, deleted_at, noindex }
}
filter .client = global client
and (
  any(.messages.edited_timestamp > .updated_at)
  or any(.messages.deleted_at > .updated_at)
  or any(exists .messages.noindex)
)
