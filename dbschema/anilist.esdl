module anilist {
  scalar type Service extending enum<ANILIST, MYANIMELIST>;

  type Account {
    required property service -> Service;
    required property username -> str;
    required link user -> user::User {
      constraint exclusive;
      on target delete delete source;
    }
    multi link entries := .<account[is Entry];
    constraint exclusive on ((.service, .username));
    index on ((.service, .username));
  }

  scalar type EntryStatus extending enum<CURRENT, COMPLETED, PAUSED, DROPPED, PLANNING, REPEATING>;

  type Entry {
    required property status -> EntryStatus;
    required property progress -> int32;
    required property score -> float32;
    required link account -> Account {
      on target delete delete source;
    }
    required link media -> Media {
      on target delete delete source;
    }
  }

  abstract type AniListData {
    required property id_al -> int32;
    required property favourites -> int32;
    required property site_url -> str;
    index on (.id_al);
  }

  scalar type MediaType extending enum<ANIME, MANGA>;

  scalar type MediaStatus extending enum<FINISHED, RELEASING, NOT_YET_RELEASED, CANCELLED, HIATUS>;

  scalar type MediaSeason extending enum<WINTER, SPRING, SUMMER, FALL>;

  type Media extending AniListData, waicolle::Trackable {
    overloaded required property id_al -> int32 {
      constraint exclusive;
    }
    required property type -> MediaType;
    required property last_update -> int64 {
      constraint min_value(0);
      default := 0;
    }
    property id_mal -> int32;
    required property title_user_preferred -> str;
    property title_native -> str;
    property title_english -> str;
    required property synonyms -> array<str>;
    property description -> str;
    property status -> MediaStatus;
    property season -> MediaSeason;
    property season_year -> int32;
    property episodes -> int32;
    property duration -> int32;
    property chapters -> int32;
    required property cover_image_extra_large -> str;
    property cover_image_color -> str;
    required property popularity -> int32;
    required property is_adult -> bool;
    required property genres -> array<str>;
    multi link tags -> Tag {
      property rank -> int32;
    }
    multi link entries := .<media[is Entry];
    multi link character_edges := .<media[is anilist::CharacterEdge];
  }

  type Character extending AniListData {
    overloaded required property id_al -> int32 {
      constraint exclusive;
    }
    required property last_update -> int64 {
      constraint min_value(0);
      default := 0;
    }
    required property name_user_preferred -> str;
    required property name_alternative -> array<str>;
    required property name_alternative_spoiler -> array<str>;
    property name_native -> str;
    property description -> str;
    required property image_large -> str;
    property gender -> str;
    property age -> str;
    property date_of_birth_year -> int32;
    property date_of_birth_month -> int32;
    property date_of_birth_day -> int32;
    multi link edges := .<character[is CharacterEdge];
    # WaiColle
    property rank := (
      waicolle::Rank.S if .favourites >= 3000 else
      waicolle::Rank.A if .favourites >= 1000 else
      waicolle::Rank.B if .favourites >= 200 else
      waicolle::Rank.C if .favourites >= 20 else
      waicolle::Rank.D if .favourites >= 1 else
      waicolle::Rank.E
    );
    property fuzzy_gender := (
      .gender if exists .gender else
      (
        with
          female := re_match_all(r'(?i)\y(she|her)\y', .description),
          male := re_match_all(r'(?i)\y(he|his)\y', .description),
        select (
          ('Female' if count(female) > count(male) else 'Male')
          if (
            (count(female) != count(male))
            and
            (max({count(female), count(male)}) >= 3 * min({count(female), count(male)}))
          )
          else <str>{}
        )
      )
      if exists .description else
      <str>{}
    )
  }

  type Staff extending AniListData, waicolle::Trackable {
    overloaded required property id_al -> int32 {
      constraint exclusive;
    }
    required property last_update -> int64 {
      constraint min_value(0);
      default := 0;
    }
    required property name_user_preferred -> str;
    required property name_alternative -> array<str>;
    property name_native -> str;
    property description -> str;
    required property image_large -> str;
    property gender -> str;
    property age -> int32;
    property date_of_birth_year -> int32;
    property date_of_birth_month -> int32;
    property date_of_birth_day -> int32;
    property date_of_death_year -> int32;
    property date_of_death_month -> int32;
    property date_of_death_day -> int32;
    multi link character_edges := .<voice_actors[is anilist::CharacterEdge];
  }

  scalar type CharacterRole extending enum<MAIN, SUPPORTING, BACKGROUND>;

  type CharacterEdge {
    required property character_role -> CharacterRole;
    required link character -> Character {
      on target delete delete source;
    }
    required link media -> Media {
      on target delete delete source;
    }
    multi link voice_actors -> Staff {
      on target delete allow;
    }
    constraint exclusive on ((.character, .media));
  }

  type Image {
    required property url -> str {
      constraint exclusive;
    }
    required property data -> str;
    index on (.url);
  }

  type Tag {
    required property id_al -> int32 {
      constraint exclusive;
    }
    required property name -> str {
      constraint exclusive;
    }
    required property description -> str;
    required property category -> str;
    required property is_adult -> bool;
    multi link medias := .<tags[is Media];
    index on (.id_al);
  }
}
