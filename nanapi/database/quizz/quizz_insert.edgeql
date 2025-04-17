with
  channel_id := <str>$channel_id,
  description := <str>$description,
  url := <optional str>$url,
  is_image := <bool>$is_image,
  author_discord_id := <str>$author_discord_id,
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
  description := description,
  url := url,
  is_image := is_image,
  author := author,
}
