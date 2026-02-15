CREATE MIGRATION m1fjqfwzmxszvkdaqxd3ygmk75xhfd35kmfkr4xmgswlkh7xxoddaq
    ONTO m1axeqqxygv6gealfrhk6kvfbjd3eoj3rw3xzb6r6wujjaegng5mpq
{
  ALTER TYPE user::User {
      CREATE REQUIRED PROPERTY age_verified: std::bool {
          SET default := true;
      };
  };
};
