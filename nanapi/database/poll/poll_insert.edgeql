with
  message_id := <str>$message_id,
  channel_id := <str>$channel_id,
  question := <str>$question,
  options := <json>$options,
  _poll := (
    insert poll::Poll {
      client := global client,
      message_id := message_id,
      channel_id := channel_id,
      question := question,
    }
  ),
  _options := (
    for option in json_array_unpack(options) union (
      with
        rank := <int32>json_get(option, 'rank'),
        text := <str>json_get(option, 'text'),
      insert poll::Option {
        client := global client,
        rank := rank,
        text := text,
        poll := _poll
      }
    )
  ),
select { _poll, _options }
