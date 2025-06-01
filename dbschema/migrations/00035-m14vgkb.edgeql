CREATE MIGRATION m14vgkbrfccsklgevtpaofikuhdfloostscl6cwcoxrrw3ti2v3zlq
    ONTO m1npz6jubn6i4gaem4v33adxhvlydhfsctqcct44crga4dyik5l27a
{
  CREATE EXTENSION pgvector VERSION '0.7';
  CREATE EXTENSION ai VERSION '1.0';
  CREATE TYPE discord::MessagePage EXTENDING default::ClientObject {
      CREATE MULTI LINK messages: discord::Message {
          ON TARGET DELETE ALLOW;
      };
      CREATE REQUIRED PROPERTY context: std::str;
      CREATE DEFERRED INDEX ext::ai::index(embedding_model := 'text-embedding-3-small') ON (.context);
      CREATE PROPERTY from_timestamp := (SELECT
          std::min(.messages.timestamp)
      );
      CREATE PROPERTY to_timestamp := (SELECT
          std::max(.messages.timestamp)
      );
      CREATE REQUIRED PROPERTY channel_id: std::str;
      CREATE REQUIRED PROPERTY updated_at: std::datetime {
          CREATE REWRITE
              INSERT 
              USING (std::datetime_of_statement());
          CREATE REWRITE
              UPDATE 
              USING (std::datetime_of_statement());
      };
  };
  ALTER TYPE discord::Message {
      CREATE MULTI LINK pages := (.<messages[IS discord::MessagePage]);
  };
};
