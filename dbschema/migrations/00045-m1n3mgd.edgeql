CREATE MIGRATION m1n3mgdheh74qm3eqn6qwarmynsk76qtvkg4t4zjzfy3437ni5hiyq
    ONTO m17a32zespcjhtvj54xexsy2uo35c6bxbdne5upfwf4leu23oc4hga
{
  ALTER TYPE discord::Reaction {
      DROP INDEX ON ((.message, .user, (((.name ++ ':') ++ .emoji_id) IF EXISTS (.emoji_id) ELSE .name)));
  };
  ALTER TYPE discord::Reaction {
      CREATE INDEX ON ((.message, .user, (.emoji_id ?? .name)));
  };
};
