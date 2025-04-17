module poll {
  type Poll extending default::ClientObject {
    required property message_id -> str {
      constraint exclusive;
    }
    required property channel_id -> str;
    required property question -> str;
    multi link options := .<poll[is Option];
    index on (.message_id);
  }

  type Option extending default::ClientObject {
    required property rank -> int32;
    required property text -> str;
    required link poll -> Poll {
      on target delete delete source;
    }
    multi link votes := .<option[is Vote];
    constraint exclusive on ((.rank, .poll));
  }

  type Vote extending default::ClientObject {
    required link poll -> Poll {
      on target delete delete source;
    }
    required link option -> Option {
      on target delete delete source;
    }
    required link user -> user::User {
      on target delete delete source;
    }
    constraint exclusive on ((.poll, .user));
  }
}
