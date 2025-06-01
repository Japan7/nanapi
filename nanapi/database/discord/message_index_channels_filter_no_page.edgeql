with
  messages := (
    select discord::Message
    filter .client = global client and not exists .deleted_at and not exists .pages
  )
select distinct messages.channel_id
