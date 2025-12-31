CREATE MIGRATION m1axeqqxygv6gealfrhk6kvfbjd3eoj3rw3xzb6r6wujjaegng5mpq
    ONTO m1iobqglb5fwba6aqzdopghc3s7puqharj4fomvl7p47elj3yfbs3q
{
  DROP TYPE ai::Prompt;
  DROP TYPE ai::PromptArgument;
  CREATE TYPE ai::Skill EXTENDING default::ClientObject {
      CREATE REQUIRED PROPERTY name: std::str;
      CREATE CONSTRAINT std::exclusive ON ((.client, .name));
      CREATE REQUIRED PROPERTY content: std::str;
      CREATE REQUIRED PROPERTY description: std::str;
  };
};
