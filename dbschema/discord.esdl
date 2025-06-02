module discord {
  type Message extending default::ClientObject {
    required property data -> json;
    property guild_id -> str;
    required property channel_id -> str;
    required property message_id -> str;
    required property author_id -> str;
    link author := (with author_id := .author_id select detached user::User filter .discord_id = author_id);
    required property content -> str;
    required property timestamp -> datetime;
    property edited_timestamp -> datetime;
    property deleted_at -> datetime;
    multi link pages := .<messages[is MessagePage];
    constraint exclusive on ((.client, .message_id));
    index on ((.guild_id, .channel_id, .message_id, .author_id, .timestamp, .edited_timestamp, .deleted_at));
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
