CREATE MIGRATION m1iobqglb5fwba6aqzdopghc3s7puqharj4fomvl7p47elj3yfbs3q
    ONTO m1n3mgdheh74qm3eqn6qwarmynsk76qtvkg4t4zjzfy3437ni5hiyq
{
  ALTER TYPE discord::Message {
      ALTER LINK author {
          USING (SELECT
              user::User
          FILTER
              (.discord_id = discord::Message.author_id)
          );
      };
  };
  ALTER TYPE discord::Reaction {
      DROP CONSTRAINT std::exclusive ON ((.message, .user, (.emoji_id ?? .name)));
      CREATE REQUIRED PROPERTY emoji_key: std::str {
          SET default := ((.name ++ ((':' ++ .emoji_id) IF EXISTS (.emoji_id) ELSE '')));
      };
      CREATE REQUIRED PROPERTY user_id: std::str {
          SET REQUIRED USING (.user.discord_id);
      };
  };
  ALTER TYPE discord::Reaction {
      CREATE CONSTRAINT std::exclusive ON ((.message, .user_id, .emoji_key));
  };
  ALTER TYPE discord::Reaction {
      DROP INDEX ON ((.message, .user, (.emoji_id ?? .name)));
  };
  ALTER TYPE discord::Reaction {
      CREATE INDEX ON ((.message, .user_id, .emoji_key));
      ALTER LINK user {
          USING (SELECT
              user::User
          FILTER
              (.discord_id = discord::Reaction.user_id)
          );
          RESET ON TARGET DELETE;
          RESET OPTIONALITY;
      };
  };
};
