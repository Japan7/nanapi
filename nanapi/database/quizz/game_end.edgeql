with
  id := <uuid>$id,
  winner_discord_id := <str>$winner_discord_id,
  winner_discord_username := <str>$winner_discord_username,
  winner := (
    insert user::User {
      discord_id := winner_discord_id,
      discord_username := winner_discord_username,
    }
    unless conflict on .discord_id
    else (
      update user::User set {
        discord_username := winner_discord_username,
      }
    )
  ),
  updated := (
    update quizz::Game
    filter .id = id
    set {
      status := quizz::Status.ENDED,
      ended_at := datetime_current(),
      winner := winner,
    }
  )
select updated {
  *,
  winner: {
    discord_id,
  },
  quizz: {
    *,
    author: {
      discord_id,
    },
  }
}
