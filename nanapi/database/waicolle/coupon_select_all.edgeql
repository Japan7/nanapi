select waicolle::Coupon {
  code,
  claimed_by: {
    user: {
      discord_id,
    },
  },
}
filter .client = global client
