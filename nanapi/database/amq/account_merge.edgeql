with
  discord_id := <str>$discord_id,
  discord_username := <str>$discord_username,
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
insert amq::Account {
  username := username,
  user := user,
}
unless conflict on .user
else (
  update amq::Account set {
    username := username,
  }
)
