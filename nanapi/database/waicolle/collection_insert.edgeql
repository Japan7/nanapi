with
  discord_id := <str>$discord_id,
  name := <str>$name,
  player := (select waicolle::Player filter .client = global client and .user.discord_id = discord_id),
  inserted := (
    insert waicolle::Collection {
      client := global client,
      name := name,
      author := player,
    }
  ),
select inserted {
  id,
  name,
  author: {
    user: {
      discord_id,
    },
  },
}
