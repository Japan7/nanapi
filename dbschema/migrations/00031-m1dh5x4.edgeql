CREATE MIGRATION m1dh5x466pnfiajiey4zlplsrm33w7btpx75m74i2grhzocmgjbjma
    ONTO m1byjsf7s7qwcbtu24hczjtd22sxdytbie5ymwlupgakylv3tjt4yq
{
  ALTER TYPE calendar::GuildEvent {
      ALTER PROPERTY discord_id {
          SET TYPE std::str USING (<std::str>.discord_id);
      };
      DROP PROPERTY discord_id_str;
  };
  ALTER TYPE poll::Poll {
      ALTER PROPERTY channel_id {
          SET TYPE std::str USING (<std::str>.channel_id);
      };
      DROP PROPERTY channel_id_str;
      ALTER PROPERTY message_id {
          SET TYPE std::str USING (<std::str>.message_id);
      };
      DROP PROPERTY message_id_str;
  };
  ALTER TYPE projection::Projection {
      ALTER PROPERTY channel_id {
          SET TYPE std::str USING (<std::str>.channel_id);
      };
      DROP PROPERTY channel_id_str;
      ALTER PROPERTY message_id {
          SET TYPE std::str USING (<std::str>.message_id);
      };
      DROP PROPERTY message_id_str;
  };
  ALTER TYPE quizz::Game {
      ALTER PROPERTY message_id {
          SET TYPE std::str USING (<std::str>.message_id);
      };
      DROP PROPERTY message_id_str;
  };
  ALTER TYPE quizz::Quizz {
      ALTER PROPERTY channel_id {
          SET TYPE std::str USING (<std::str>.channel_id);
      };
      DROP PROPERTY channel_id_str;
  };
  ALTER TYPE reminder::Reminder {
      ALTER PROPERTY channel_id {
          SET TYPE std::str USING (<std::str>.channel_id);
      };
      DROP PROPERTY channel_id_str;
  };
  ALTER TYPE role::Role {
      ALTER PROPERTY role_id {
          SET TYPE std::str USING (<std::str>.role_id);
      };
      DROP PROPERTY role_id_str;
  };
  ALTER TYPE user::User {
      ALTER PROPERTY discord_id {
          SET TYPE std::str USING (<std::str>.discord_id);
      };
      DROP PROPERTY discord_id_str;
  };
};
