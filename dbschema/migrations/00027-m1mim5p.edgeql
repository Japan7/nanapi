CREATE MIGRATION m1mim5pih5xgtor6tm6znfotxp7wlkobamdoy7ih72fnwlrldagcqa
    ONTO m1hq7rmg46b7aiblmrpr75s7uo4iob2q254cbv6zgwzzn27b2pxsqq
{
  ALTER TYPE user::Profile {
      CREATE PROPERTY birthday: std::datetime;
      CREATE PROPERTY pronouns: std::str;
  };
};
