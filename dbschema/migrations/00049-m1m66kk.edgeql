CREATE MIGRATION m1m66kk5nognqxp7hwt4w2on7qnfuclv7u2zdj7rstidlntw7a23kq
    ONTO m1fjqfwzmxszvkdaqxd3ygmk75xhfd35kmfkr4xmgswlkh7xxoddaq
{
  CREATE SCALAR TYPE waicolle::WaifuStatus EXTENDING enum<WAICOLLE, WAIVENTURE, DEAD, RETIRED>;
  ALTER TYPE waicolle::Waifu {
      CREATE PROPERTY season: std::str;
      CREATE PROPERTY status: waicolle::WaifuStatus {
          SET default := (waicolle::WaifuStatus.WAICOLLE);
      };
  };
};
