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
    constraint exclusive on ((.client, .message_id));
    index on ((.message_id, .deleted_at));
  }
}
