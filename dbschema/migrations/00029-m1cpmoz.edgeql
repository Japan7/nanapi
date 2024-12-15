CREATE MIGRATION m1cpmoz6ue576uzldgepkp5bolfgg2n7l32dfx4ga5gudxbo7ypxxa
    ONTO m1vnk3u6ttr6yrd4dkxficgsidqy5264drzusoppur7gowyhmkzmwa
{
  ALTER TYPE user::Profile {
      ALTER PROPERTY graduation_year {
          SET TYPE std::int16 USING (<std::int16>.graduation_year);
      };
  };
};
