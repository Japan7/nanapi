with
  discord_id := <int64>$discord_id,
  discord_username := <str>$discord_username,
  channel_id := <int64>$channel_id,
  message := <str>$message,
  timestamp := <datetime>$timestamp,
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
  reminder := (
    insert reminder::Reminder {
      client := global client,
      channel_id := channel_id,
      message := message,
      timestamp := timestamp,
      user := user,
    }
  )
select reminder {
  id,
  channel_id,
  channel_id_str,
  message,
  timestamp,
  user: {
    discord_id,
    discord_id_str,
  },
};
