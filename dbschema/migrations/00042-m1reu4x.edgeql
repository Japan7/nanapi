CREATE MIGRATION m1reu4xwxyrc65hj2fn6gtv6k23k44auqnzvp7rr5dadybe232etoa
    ONTO m1ip7lq7xjxi5hckmv7pryhh5ujpehmkqzk6vlacethkr57ciprfqq
{
  CREATE TYPE discord::Reaction EXTENDING default::ClientObject {
      CREATE REQUIRED LINK message: discord::Message {
          ON TARGET DELETE DELETE SOURCE;
      };
      CREATE REQUIRED LINK user: user::User {
          ON TARGET DELETE DELETE SOURCE;
      };
      CREATE PROPERTY emoji_id: std::str;
      CREATE REQUIRED PROPERTY name: std::str;
      CREATE CONSTRAINT std::exclusive ON ((.message, .user, (.emoji_id ?? .name)));
      CREATE REQUIRED PROPERTY animated: std::bool {
          SET default := false;
      };
      CREATE REQUIRED PROPERTY burst: std::bool {
          SET default := false;
      };
  };
  ALTER TYPE discord::Message {
      CREATE MULTI LINK reactions := (.<message[IS discord::Reaction]);
  };
};
