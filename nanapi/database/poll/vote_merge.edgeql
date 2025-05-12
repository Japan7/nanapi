with
  discord_id := <str>$discord_id,
  discord_username := <str>$discord_username,
  message_id := <str>$message_id,
  rank := <int32>$rank,
  user := (
    insert user::User {
      discord_id := discord_id,
      discord_username := discord_username,
    }
    unless conflict on .discord_id
    else (
      update user::User set {
        discord_username := discord_username,
      }
    )
  ),
  poll := (select poll::Poll filter .message_id = message_id),
  option := (select poll::Option filter .poll = poll and .rank = rank),
insert poll::Vote {
  client := global client,
  poll := poll,
  option := option,
  user := user,
}
unless conflict on ((.poll, .user)) else (
  update poll::Vote set {
    option := option,
  }
)
