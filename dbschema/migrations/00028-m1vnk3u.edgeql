CREATE MIGRATION m1vnk3u6ttr6yrd4dkxficgsidqy5264drzusoppur7gowyhmkzmwa
    ONTO m1mim5pih5xgtor6tm6znfotxp7wlkobamdoy7ih72fnwlrldagcqa
{
  ALTER TYPE user::Profile {
      CREATE PROPERTY n7_major: std::str;
  };
  ALTER TYPE user::Profile {
      CREATE PROPERTY graduation_year: std::str;
      DROP PROPERTY promotion;
  };
};
