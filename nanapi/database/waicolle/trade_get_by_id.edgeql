with
  id := <uuid>$id,
select waicolle::TradeOperation {
  *,
  author: {
    user: {
      discord_id,
      discord_id_str,
    },
  },
  received,
  offeree: {
    user: {
      discord_id,
      discord_id_str,
    },
  },
  offered,
}
filter .id = id
