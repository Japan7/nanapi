with
  discord_id := <str>$discord_id,
  discord_username := <str>$discord_username,
  game_mode := <waicolle::GameMode>$game_mode,
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
insert waicolle::Player {
  client := global client,
  game_mode := game_mode,
  user := user,
}
unless conflict on ((.client, .user))
else (
  update waicolle::Player set {
    game_mode := game_mode,
    frozen_at := {},
  }
)
