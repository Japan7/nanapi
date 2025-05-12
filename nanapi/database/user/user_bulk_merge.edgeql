with
  users := <json>$users,
for user in json_array_unpack(users) union (
  with
    discord_id := <str>json_get(user, 'discord_id'),
    discord_username := <str>json_get(user, 'discord_username'),
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
)
