with
  id := <uuid>$id,
  winner_discord_id := <int64>$winner_discord_id,
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
  id,
  status,
  message_id,
  message_id_str,
  answer_bananed,
  started_at,
  ended_at,
  winner: {
    discord_id,
    discord_id_str,
  },
  quizz: {
    id,
    channel_id,
    channel_id_str,
    description,
    url,
    is_image,
    answer,
    answer_source,
    submitted_at,
    hikaried,
    author: {
      discord_id,
      discord_id_str,
    },
  }
}
