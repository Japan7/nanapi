module quizz {
  type Quizz extending default::ClientObject {
    required property channel_id -> int64;
    required property channel_id_str := <str>.channel_id;
    property question -> str;
    property attachment_url -> str;
    property answer -> str;
    property hints -> array<str>;
    required property submitted_at -> datetime {
      default := datetime_current();
    }
    required link author -> user::User {
      on target delete delete source;
    }
    link game := .<quizz[is Game];
    index on (.channel_id);
  }

  scalar type Status extending enum<STARTED, ENDED>;

  type Game extending default::ClientObject {
    required property status -> Status {
      default := Status.STARTED;
    }
    required property message_id -> int64 {
      constraint exclusive;
    }
    required property message_id_str := <str>.message_id;
    required property started_at -> datetime {
      default := datetime_current();
    }
    property ended_at -> datetime;
    link winner -> user::User {
      on target delete allow;
    }
    required link quizz -> Quizz {
      constraint exclusive;
      on target delete delete source;
    }
    index on (.message_id);
  }
}
