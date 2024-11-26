with
  author_discord_id := <int64>$author_discord_id,
  received_ids := <array<uuid>>$received_ids,
  blood_shards := <optional int32>$blood_shards ?? 0,
  offeree_discord_id := <int64>$offeree_discord_id,
  offered_ids := <array<uuid>>$offered_ids,
  author := (select waicolle::Player filter .client = global client and .user.discord_id = author_discord_id),
  offeree := (select waicolle::Player filter .client = global client and .user.discord_id = offeree_discord_id),
  inserted := (
    insert waicolle::TradeOperation {
      client := global client,
      author := author,
      received := (select waicolle::Waifu filter .id in array_unpack(received_ids)),
      blood_shards := blood_shards,
      offeree := offeree,
      offered := (select waicolle::Waifu filter .id in array_unpack(offered_ids)),
    }
  )
select inserted {
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
