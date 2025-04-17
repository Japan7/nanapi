module quizz {
  type Quizz extending default::ClientObject {
    required property channel_id -> str;
    property description -> str;
    property url -> str;
    required property is_image -> bool {
      default := false;
    }
    property answer -> str;
    property answer_source -> str;
    required property submitted_at -> datetime {
      default := datetime_current();
    }
    required link author -> user::User {
      on target delete delete source;
    }
    property hikaried := .url ilike 'https://hikari.butaishoujo.moe%';
    link game := .<quizz[is Game];
    index on (.channel_id);
  }

  scalar type Status extending enum<STARTED, ENDED>;

  type Game extending default::ClientObject {
    required property status -> Status {
      default := Status.STARTED;
    }
    required property message_id -> str {
      constraint exclusive;
    }
    property answer_bananed -> str;
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
