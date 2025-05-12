select waicolle::TradeOperation {
  *,
  author: {
    user: {
      discord_id,
    },
  },
  received: {
    *,
    character: { id_al },
    owner: {
      user: {
        discord_id,
      },
    },
    original_owner: {
      user: {
        discord_id,
      },
    },
    custom_position_waifu: { id },
  },
  offeree: {
    user: {
      discord_id,
    },
  },
  offered: {
    *,
    character: { id_al },
    owner: {
      user: {
        discord_id,
      },
    },
    original_owner: {
      user: {
        discord_id,
      },
    },
    custom_position_waifu: { id },
  },
}
filter .client = global client
and not exists .completed_at
