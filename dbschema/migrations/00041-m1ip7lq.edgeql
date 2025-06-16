CREATE MIGRATION m1ip7lq7xjxi5hckmv7pryhh5ujpehmkqzk6vlacethkr57ciprfqq
    ONTO m1fsljnotyzxbwbpwm3myxe3dr4pdl3z4wgpdpo5kvi5hodgp2pzpq
{
  CREATE MODULE ai IF NOT EXISTS;
  CREATE TYPE ai::PromptArgument EXTENDING default::ClientObject {
      CREATE PROPERTY description: std::str;
      CREATE REQUIRED PROPERTY name: std::str;
  };
  CREATE TYPE ai::Prompt EXTENDING default::ClientObject {
      CREATE REQUIRED PROPERTY name: std::str;
      CREATE CONSTRAINT std::exclusive ON ((.client, .name));
      CREATE MULTI LINK arguments: ai::PromptArgument {
          ON SOURCE DELETE DELETE TARGET;
          CREATE CONSTRAINT std::exclusive;
      };
      CREATE PROPERTY description: std::str;
      CREATE REQUIRED PROPERTY prompt: std::str;
  };
};
