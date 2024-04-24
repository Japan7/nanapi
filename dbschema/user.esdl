module user {
  type User {
    required property discord_id -> int64 {
      constraint exclusive;
    }
    required property discord_id_str := <str>.discord_id;
    required property discord_username -> str;
    link profile := .<user[is Profile];
    link amq := .<user[is amq::Account];
    link anilist := .<user[is anilist::Account];
    multi link pots := .<user[is pot::Pot];
    multi link quizzes := .<author[is quizz::Quizz];
    multi link reminders := .<user[is reminder::Reminder];
    multi link waicolles := .<user[is waicolle::Player];
    index on (.discord_id);
  }

  type Profile {
    property full_name -> str;
    property photo -> str;
    property promotion -> str;
    property telephone -> str;
    required link user -> User {
      constraint exclusive;
      on target delete delete source;
    }
  }
}
