module reminder {
  type Reminder extending default::ClientObject {
    required link user -> user::User {
      on target delete delete source;
    }
    required property channel_id -> str;
    required property timestamp -> datetime;
    required property message -> str;
  }
}
