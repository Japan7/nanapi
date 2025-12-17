module discord {
  type Message extending default::ClientObject {
    required property data -> json;
    property guild_id -> str;
    required property channel_id -> str;
    required property message_id -> str;
    required property author_id -> str;
    link author := (select user::User filter .discord_id = Message.author_id);
    required property content -> str;
    required property timestamp -> datetime;
    property edited_timestamp -> datetime;
    property deleted_at -> datetime;
    property noindex -> str;
    multi link reactions := .<message[is Reaction];
    multi link pages := .<messages[is MessagePage];
    constraint exclusive on ((.client, .message_id));
    index on ((.guild_id, .channel_id, .message_id, .author_id, .timestamp, .edited_timestamp, .deleted_at, .noindex));
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

  type Reaction extending default::ClientObject {
    required link message -> Message {
      on target delete delete source;
    }
    required property user_id -> str;
    link user := (select user::User filter .discord_id = Reaction.user_id);
    required property name -> str;
    property emoji_id -> str;
    required property animated -> bool {
      default := false;
    }
    required property burst -> bool {
      default := false;
    }
    required property emoji_key -> str {
      default := .name ++ ((':' ++ .emoji_id) if exists .emoji_id else '');
    }
    constraint exclusive on ((.message, .user_id, .emoji_key));
    index on ((.message, .user_id, .emoji_key));
  }
}
