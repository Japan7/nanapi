with
  channel_id := <int64>$channel_id,
  question := <optional str>$question,
  attachment_url := <optional str>$attachment_url,
  answer := <optional str>$answer,
  hints := <optional array<str>>$hints,
  author_discord_id := <int64>$author_discord_id,
  author_discord_username := <str>$author_discord_username,
  author := (
    insert user::User {
      discord_id := author_discord_id,
      discord_username := author_discord_username,
    }
    unless conflict on .discord_id
    else (
      update user::User set {
        discord_username := author_discord_username,
      }
    )
  ),
insert quizz::Quizz {
  client := global client,
  channel_id := channel_id,
  question := question,
  attachment_url := attachment_url,
  answer := answer,
  hints := hints,
  author := author,
}
