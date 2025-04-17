module projection {
  scalar type Status extending enum<ONGOING, COMPLETED>;

  type Projection extending default::ClientObject {
    required property name -> str;
    required property status -> Status {
      default := Status.ONGOING
    }
    required property channel_id -> str;
    property message_id -> str {
      constraint exclusive;
    }
    multi link medias -> anilist::Media {
      added: datetime {
        default   := datetime_of_statement();
        readonly  := true;
      }
      on target delete allow;
    }
    multi link external_medias -> ExternalMedia {
      added: datetime {
        default   := datetime_of_statement();
        readonly  := true;
      }
      on target delete allow;
    }
    multi link participants -> user::User {
      on target delete allow;
    }
    multi link guild_events -> calendar::GuildEvent {
      constraint exclusive;
      on target delete allow;
    }
    multi link legacy_events := .<projection[is LegacyEvent];
  }

  type ExternalMedia extending default::ClientObject {
    required property title -> str;
  }

  type LegacyEvent extending default::ClientObject {
    required property date -> datetime;
    required property description -> str;
    required link projection -> Projection {
      on target delete delete source;
    }
  }
}
