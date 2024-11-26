select waicolle::TradeOperation {
  *,
  author: {
    user: {
      discord_id,
      discord_id_str,
    },
  },
  received: {
    *,
    character: { id_al },
    owner: {
      user: {
        discord_id,
        discord_id_str,
      },
    },
    original_owner: {
      user: {
        discord_id,
        discord_id_str,
      },
    },
    custom_position_waifu: { id },
  },
  offeree: {
    user: {
      discord_id,
      discord_id_str,
    },
  },
  offered: {
    *,
    character: { id_al },
    owner: {
      user: {
        discord_id,
        discord_id_str,
      },
    },
    original_owner: {
      user: {
        discord_id,
        discord_id_str,
      },
    },
    custom_position_waifu: { id },
  },
}
filter .client = global client
