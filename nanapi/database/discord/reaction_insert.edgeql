with
  message_id := <str>$message_id,
  user_id := <str>$user_id,
  name := <str>$name,
  emoji_id := <optional str>$emoji_id,
  animated := <optional bool>$animated,
  burst := <optional bool>$burst,
  message := (select discord::Message filter .message_id = message_id and .client = global client),
  user := (select user::User filter .discord_id = user_id)
insert discord::Reaction {
  client := global client,
  message := message,
  user := user,
  name := name,
  emoji_id := emoji_id,
  animated := animated,
  burst := burst,
}
