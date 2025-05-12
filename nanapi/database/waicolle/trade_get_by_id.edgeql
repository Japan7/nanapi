with
  id := <uuid>$id,
select waicolle::TradeOperation {
  *,
  author: {
    user: {
      discord_id,
    },
  },
  received,
  offeree: {
    user: {
      discord_id,
    },
  },
  offered,
}
filter .id = id
