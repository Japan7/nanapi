with
  messages := <array <json>>$messages,
  # Pre-extract all unique users from the entire payload to batch insert them once
  all_users := (
    for data in array_unpack(messages) union (
      for item in array_unpack(<array <json>>json_get(data, 'reactions')) union (
        for user_data in array_unpack(<array <json>>json_get(item, 'users')) union (
          (<str>json_get(user_data, 'id'), <str>json_get(user_data, 'username'))
        )
      )
    )
  ),
  # Batch insert all unique users upfront
  inserted_users := (
    for user_tuple in (select distinct all_users) union (
      insert user::User {
        discord_id := user_tuple.0,
        discord_username := user_tuple.1,
      }
      unless conflict on .discord_id
      else (select user::User)
    )
  ),
for data in array_unpack(messages) union (
  with
    message_data := <json>json_get(data, 'message'),
    reactions_data := <array <json>>json_get(data, 'reactions'),
    message_id := <str>json_get(message_data, 'id'),
    inserted := (
      insert discord::Message {
        client := global client,
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
  for item in array_unpack(reactions_data) union (
    with
      reaction_data := <json>json_get(item, 'reaction'),
      users_data := <array <json>>json_get(item, 'users'),
      emoji := <json>json_get(reaction_data, 'emoji'),
      name := <str>json_get(emoji, 'name'),
      emoji_id := <str>json_get(emoji, 'id'),
      animated := <bool>json_get(emoji, 'animated') ?? false,
      burst := <int32>json_get(reaction_data, 'count_details', 'burst') > 0,
    for user_data in array_unpack(users_data) union (
      with
        user_id := <str>json_get(user_data, 'id'),
        # Look up the pre-inserted user instead of inserting again
        user := (select inserted_users filter .discord_id = user_id limit 1),
      insert discord::Reaction {
        client := global client,
        message := inserted,
        user := user,
        name := name,
        emoji_id := emoji_id,
        animated := animated,
        burst := burst,
      }
      unless conflict
    )
  )
)
