CREATE MIGRATION m12mcej6ew2z5cjmhi2ywlnbj2cuam5s7lfxe2cus6wuq53posw6ha
    ONTO m1hsv63ztkuffis7wju3nysoiewchrkledocfn7p3pfcwka2xw7cba
{
  CREATE MODULE discord IF NOT EXISTS;
  CREATE TYPE discord::Message {
      CREATE PROPERTY deleted_at: std::datetime;
      CREATE REQUIRED PROPERTY message_id: std::str {
          CREATE CONSTRAINT std::exclusive;
      };
      CREATE INDEX ON ((.message_id, .deleted_at));
      CREATE REQUIRED PROPERTY data: std::json;
      CREATE PROPERTY author_id := (SELECT
          <std::str>std::json_get(.data, 'author', 'id')
      );
      CREATE LINK author := (WITH
          author_id := 
              .author_id
      SELECT
          DETACHED user::User
      FILTER
          (.discord_id = author_id)
      );
      CREATE PROPERTY channel_id := (SELECT
          <std::str>std::json_get(.data, 'channel_id')
      );
      CREATE PROPERTY content := (SELECT
          <std::str>std::json_get(.data, 'content')
      );
      CREATE PROPERTY edited_timestamp := (SELECT
          <std::datetime>std::json_get(.data, 'edited_timestamp')
      );
      CREATE PROPERTY guild_id := (SELECT
          <std::str>std::json_get(.data, 'guild_id')
      );
      CREATE PROPERTY timestamp := (SELECT
          <std::datetime>std::json_get(.data, 'timestamp')
      );
  };
};
