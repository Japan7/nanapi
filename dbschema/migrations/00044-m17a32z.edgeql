CREATE MIGRATION m17a32zespcjhtvj54xexsy2uo35c6bxbdne5upfwf4leu23oc4hga
    ONTO m14yfi7hea6ehplmbvughu7rszq7ah2es6wskvagoirizpten4lgpq
{
  ALTER TYPE discord::Reaction {
      CREATE INDEX ON ((.message, .user, (((.name ++ ':') ++ .emoji_id) IF EXISTS (.emoji_id) ELSE .name)));
  };
};
