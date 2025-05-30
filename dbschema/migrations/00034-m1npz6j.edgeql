CREATE MIGRATION m1npz6jubn6i4gaem4v33adxhvlydhfsctqcct44crga4dyik5l27a
    ONTO m12mcej6ew2z5cjmhi2ywlnbj2cuam5s7lfxe2cus6wuq53posw6ha
{
  ALTER TYPE discord::Message {
      CREATE LINK client: default::Client {
          ON TARGET DELETE DELETE SOURCE;
          SET REQUIRED USING (SELECT
              default::Client
          FILTER
              (.username = 'nana')
          );
      };
      EXTENDING default::ClientObject LAST;
      CREATE CONSTRAINT std::exclusive ON ((.client, .message_id));
      ALTER PROPERTY message_id {
          DROP CONSTRAINT std::exclusive;
      };
  };
  ALTER TYPE discord::Message {
      ALTER LINK client {
          RESET OPTIONALITY;
          DROP OWNED;
          RESET TYPE;
      };
  };
};
