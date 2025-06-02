with
  messages := (
    select discord::Message
    filter .client = global client
    and not exists .pages
    and not exists .deleted_at
    and not exists .noindex
  )
select distinct messages.channel_id
