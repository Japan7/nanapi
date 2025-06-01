with
  channel_id := <str>$channel_id
select discord::MessagePage {
  id,
  messages: { data }
}
filter .client = global client
and .channel_id = channel_id
order by .to_timestamp desc
limit 1
