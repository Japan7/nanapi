with
  messages := <array <json>>$messages,
  current_client := global client,
for data in array_unpack(messages) union (
  with
    message_data := <json>json_get(data, 'message'),
    reactions_data := <array <json>>json_get(data, 'reactions'),
    message_id := <str>json_get(message_data, 'id'),
    inserted := (
      insert discord::Message {
        client := current_client,
        data := message_data,
        guild_id := <str>json_get(message_data, 'guild_id'),
        channel_id := <str>json_get(message_data, 'channel_id'),
        message_id := message_id,
        author_id := <str>json_get(message_data, 'author', 'id'),
        content := <str>json_get(message_data, 'content'),
        timestamp := <datetime>json_get(message_data, 'timestamp'),
        edited_timestamp := <datetime>json_get(message_data, 'edited_timestamp'),
      }
      unless conflict on ((.client, .message_id))
      else (select discord::Message)
    ),
    # Flatten reaction data to reduce nesting depth
    reaction_items := (
      for item in array_unpack(reactions_data) union (
        with
          reaction_data := <json>json_get(item, 'reaction'),
          users_data := <array <json>>json_get(item, 'users'),
          emoji := <json>json_get(reaction_data, 'emoji'),
          emoji_name := <str>json_get(emoji, 'name'),
          emoji_id := <str>json_get(emoji, 'id'),
          animated := <bool>json_get(emoji, 'animated') ?? false,
          burst := <int32>json_get(reaction_data, 'count_details', 'burst') > 0,
        for user_data in array_unpack(users_data) union (
          (
            name := emoji_name,
            emoji_id := emoji_id,
            animated := animated,
            burst := burst,
            user_id := <str>json_get(user_data, 'id'),
            username := <str>json_get(user_data, 'username'),
          )
        )
      )
    ),
  for r in reaction_items union (
    with
      user := (
        insert user::User {
          discord_id := r.user_id,
          discord_username := r.username,
        }
        unless conflict on .discord_id
        else (select user::User)
      ),
    insert discord::Reaction {
      client := current_client,
      message := inserted,
      user := user,
      name := r.name,
      emoji_id := r.emoji_id,
      animated := r.animated,
      burst := r.burst,
    }
    unless conflict
  )
)
