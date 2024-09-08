module calendar {
  type UserCalendar {
    required property ics -> str;
    required link user -> user::User {
      constraint exclusive;
      on target delete delete source;
    }
  }

  type GuildEvent extending default::ClientObject {
    required property discord_id -> int64;
    required property discord_id_str := <str>.discord_id;
    required property name -> str;
    property description -> str;
    property location -> str;
    required property start_time -> datetime;
    required property end_time -> datetime;
    property image -> str;
    property url -> str;
    required link organizer -> user::User {
      on target delete delete source;
    }
    multi link participants -> user::User {
      on target delete allow;
    }
    constraint exclusive on ((.client, .discord_id));
  }
}