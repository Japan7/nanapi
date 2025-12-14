CREATE MIGRATION m14yfi7hea6ehplmbvughu7rszq7ah2es6wskvagoirizpten4lgpq
    ONTO m1reu4xwxyrc65hj2fn6gtv6k23k44auqnzvp7rr5dadybe232etoa
{
  ALTER TYPE default::ClientObject {
      CREATE INDEX ON (.client);
  };
};
