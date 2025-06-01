module discord {
  type Message extending default::ClientObject {
    required property message_id -> str;
    required property data -> json;
    property guild_id := (select <str>json_get(.data, 'guild_id'));
    property channel_id := (select <str>json_get(.data, 'channel_id'));
    property author_id := (select <str>json_get(.data, 'author', 'id'));
    link author := (with author_id := .author_id select detached user::User filter .discord_id = author_id);
    property content := (select <str>json_get(.data, 'content'));
    property timestamp := (select <datetime>json_get(.data, 'timestamp'));
    property edited_timestamp := (select <datetime>json_get(.data, 'edited_timestamp'));
    property deleted_at -> datetime;
    multi link pages := .<messages[is MessagePage];
    constraint exclusive on ((.client, .message_id));
    index on ((.message_id, .deleted_at));
  }

  type MessagePage extending default::ClientObject {
    required property context -> str;
    required property channel_id -> str;
    property from_timestamp := (select min(.messages.timestamp));
    property to_timestamp := (select max(.messages.timestamp));
    required property updated_at -> datetime {
      rewrite insert, update using (datetime_of_statement())
    }
    multi link messages -> Message {
      on target delete allow;
    }
    deferred index ext::ai::index(embedding_model := 'text-embedding-3-small') on (.context);
  }
}
