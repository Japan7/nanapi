CREATE MIGRATION m1foqeni64zy7clxk3jbqdxm4ozesieofvuldxx3qg3azwfwxglcqa
    ONTO m1hq7rmg46b7aiblmrpr75s7uo4iob2q254cbv6zgwzzn27b2pxsqq
{
  ALTER TYPE waicolle::Player {
      CREATE PROPERTY frozen_at: std::datetime;
  };
  ALTER TYPE waicolle::Waifu {
      CREATE PROPERTY frozen := (EXISTS (.owner.frozen_at));
  };
};
