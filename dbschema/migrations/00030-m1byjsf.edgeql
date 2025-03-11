CREATE MIGRATION m1byjsf7s7qwcbtu24hczjtd22sxdytbie5ymwlupgakylv3tjt4yq
    ONTO m1fibjb65ikohyekq75dj5exzzwaipmzoqldo7vyhodxpkglbdx44q
{
  ALTER TYPE anilist::Character {
      CREATE REQUIRED PROPERTY last_update: std::int64 {
          SET default := 0;
          CREATE CONSTRAINT std::min_value(0);
      };
  };
  ALTER TYPE anilist::Media {
      CREATE REQUIRED PROPERTY last_update: std::int64 {
          SET default := 0;
          CREATE CONSTRAINT std::min_value(0);
      };
  };
  ALTER TYPE anilist::Staff {
      CREATE REQUIRED PROPERTY last_update: std::int64 {
          SET default := 0;
          CREATE CONSTRAINT std::min_value(0);
      };
  };
};
