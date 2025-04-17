with
  discord_id := <str>$discord_id,
select pot::Pot { amount, count }
filter .client = global client and .user.discord_id = discord_id
