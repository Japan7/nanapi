with
  channel_id := <str>$channel_id,
  n_offset := <optional int64>$offset,
  n_limit := <optional int64>$limit,
select discord::Message { data }
filter .client = global client
and .channel_id = channel_id
and not exists .deleted_at
and not exists .pages
order by .timestamp asc
offset n_offset
limit n_limit;
