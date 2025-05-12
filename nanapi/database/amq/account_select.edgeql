with
  username := <optional str>$username,
  filtered := (
    (select amq::Account filter .username = username)
    if exists username else
    (select amq::Account)
  )
select filtered {
  username,
  user: {
    discord_id,
  }
}
