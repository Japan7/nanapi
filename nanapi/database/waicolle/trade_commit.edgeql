with
  id := <uuid>$id,
update waicolle::TradeOperation
filter .id = id
set {
  completed_at := datetime_current(),
}
