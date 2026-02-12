module user {
  type User {
    required property discord_id -> str {
      constraint exclusive;
    }
    required property discord_username -> str;
    required property age_verified -> bool {
        default := true;
    };
    link profile := .<user[is Profile];
    link amq := .<user[is amq::Account];
    link anilist := .<user[is anilist::Account];
    link calendar := .<user[is calendar::UserCalendar];
    multi link guild_events := .<participants[is calendar::GuildEvent];
    multi link pots := .<user[is pot::Pot];
    multi link quizzes := .<author[is quizz::Quizz];
    multi link reminders := .<user[is reminder::Reminder];
    multi link waicolles := .<user[is waicolle::Player];
    index on (.discord_id);
  }

  type Profile {
    property birthday -> datetime;
    property full_name -> str;
    property graduation_year -> int16;
    property photo -> str;
    property pronouns -> str;
    property n7_major -> str;
    property telephone -> str;
    required link user -> User {
      constraint exclusive;
      on target delete delete source;
    }
  }
}
