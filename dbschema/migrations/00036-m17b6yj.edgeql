CREATE MIGRATION m17b6yj57wsivjzkzj5gvyfji3v6nxgdf6h5pmsgowpavln3xxtecq
    ONTO m14vgkbrfccsklgevtpaofikuhdfloostscl6cwcoxrrw3ti2v3zlq
{
  ALTER TYPE discord::Message {
      DROP INDEX ON ((.message_id, .deleted_at));
      ALTER PROPERTY author_id {
          RESET EXPRESSION;
          RESET CARDINALITY;
          SET REQUIRED USING (<std::str>std::json_get(.data, 'author', 'id'));
          SET TYPE std::str;
      };
      ALTER PROPERTY channel_id {
          RESET EXPRESSION;
          RESET CARDINALITY;
          SET REQUIRED USING (<std::str>std::json_get(.data, 'channel_id'));
          SET TYPE std::str;
      };
      ALTER PROPERTY edited_timestamp {
          RESET EXPRESSION;
          RESET CARDINALITY;
          RESET OPTIONALITY;
          SET TYPE std::datetime;
      };
      ALTER PROPERTY guild_id {
          RESET EXPRESSION;
          RESET CARDINALITY;
          RESET OPTIONALITY;
          SET TYPE std::str;
      };
      ALTER PROPERTY timestamp {
          RESET EXPRESSION;
          RESET CARDINALITY;
          SET REQUIRED USING (<std::datetime>std::json_get(.data, 'timestamp'));
          SET TYPE std::datetime;
      };
  };
  ALTER TYPE discord::Message {
      CREATE INDEX ON ((.guild_id, .channel_id, .message_id, .author_id, .timestamp, .edited_timestamp, .deleted_at));
      ALTER PROPERTY content {
          RESET EXPRESSION;
          RESET CARDINALITY;
          RESET OPTIONALITY;
          SET TYPE std::str;
      };
  };
};
