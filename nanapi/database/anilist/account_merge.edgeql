with
  discord_id := <str>$discord_id,
  discord_username := <str>$discord_username,
  service := <anilist::Service>$service,
  username := <str>$username,
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
insert anilist::Account {
  service := service,
  username := username,
  user := user,
}
unless conflict on .user
else (
  update anilist::Account set {
    service := service,
    username := username,
  }
)
