CREATE MIGRATION m1lbvqie7ow2wewdsenhxsafhudy6d3dyspvwq542t2g4lxym3ywyq
    ONTO m134daqcvzezm2zxmdi3fomwtpqboxhocl6lyxhprfjj46rludolxa
{
  ALTER TYPE discord::Message {
      CREATE PROPERTY noindex: std::str;
  };
  ALTER TYPE discord::Message {
      CREATE INDEX ON ((.guild_id, .channel_id, .message_id, .author_id, .timestamp, .edited_timestamp, .deleted_at, .noindex));
  };
  ALTER TYPE discord::Message {
      DROP INDEX ON ((.guild_id, .channel_id, .message_id, .author_id, .timestamp, .edited_timestamp, .deleted_at));
  };
};
