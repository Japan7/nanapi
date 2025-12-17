with
  message_id := <str>$message_id,
  user_id := <optional str>$user_id,
  name := <optional str>$name,
  emoji_id := <optional str>$emoji_id,
delete discord::Reaction
filter .client = global client
and .message.message_id = message_id
and (.user_id = user_id if exists user_id else true)
and (.name = name if exists name else true)
and (.emoji_id = emoji_id if exists emoji_id else true)
