with
  channel_id := <str>$channel_id,
  tafter := <optional datetime>$after,
  n_offset := <optional int32>$offset,
  n_limit := <optional int32>$limit,
select discord::Message { data }
filter .client = global client
and not exists .pages
and not exists .deleted_at
and not exists .noindex
and .channel_id = channel_id
and (.timestamp > tafter if exists tafter else true)
order by .timestamp asc
offset n_offset
limit n_limit
