CREATE MIGRATION m1connfa6f7l2poqf7qc37vksj2vxqkhogqjvdw4v43mhd52roxtta
    ONTO m1sbqiuyd3lhky4vdepxxacsxe4p7t4l5yeeyu3uaeedaf323shwha
{
  CREATE ABSTRACT TYPE waicolle::Operation {
      CREATE REQUIRED LINK author: waicolle::Player {
          ON TARGET DELETE DELETE SOURCE;
      };
      CREATE MULTI LINK received: waicolle::Waifu {
          ON TARGET DELETE DELETE SOURCE;
      };
      CREATE REQUIRED PROPERTY created_at: std::datetime {
          SET default := (std::datetime_current());
      };
  };
  CREATE TYPE waicolle::RerollOperation EXTENDING default::ClientObject, waicolle::Operation {
      CREATE MULTI LINK rerolled: waicolle::Waifu {
          ON TARGET DELETE DELETE SOURCE;
      };
  };
  CREATE TYPE waicolle::RollOperation EXTENDING default::ClientObject, waicolle::Operation {
      CREATE REQUIRED PROPERTY moecoins: std::int32 {
          SET default := 0;
      };
      CREATE REQUIRED PROPERTY roll_id: std::str;
  };
  ALTER TYPE waicolle::Trade {
      ALTER LINK player_a {
          RENAME TO author;
      };
  };
  ALTER TYPE waicolle::Trade {
      ALTER LINK player_b {
          RENAME TO offeree;
      };
  };
  ALTER TYPE waicolle::Trade {
      ALTER LINK waifus_a {
          RENAME TO offered;
      };
  };
  ALTER TYPE waicolle::Trade {
      ALTER LINK waifus_b {
          RENAME TO received;
      };
  };
  ALTER TYPE waicolle::Trade {
      ALTER PROPERTY blood_shards_a {
          RENAME TO blood_shards;
      };
  };
  ALTER TYPE waicolle::Trade {
      DROP PROPERTY blood_shards_b;
  };
  ALTER TYPE waicolle::Trade {
      CREATE PROPERTY completed_at: std::datetime;
  };
  ALTER TYPE waicolle::Trade {
      CREATE REQUIRED PROPERTY created_at: std::datetime {
          SET default := (std::datetime_current());
      };
  };
  ALTER TYPE waicolle::Trade {
      DROP PROPERTY moecoins_a;
  };
  ALTER TYPE waicolle::Trade {
      DROP PROPERTY moecoins_b;
  };
  ALTER TYPE waicolle::Waifu {
      ALTER PROPERTY trade_locked {
          USING ((EXISTS (.<received[IS waicolle::Trade]) OR EXISTS (.<offered[IS waicolle::Trade])));
      };
  };
};
