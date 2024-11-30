CREATE MIGRATION m1hq7rmg46b7aiblmrpr75s7uo4iob2q254cbv6zgwzzn27b2pxsqq
    ONTO m13ptnpczpdqcveh7kqjqsqf6wy7c723cmcqo6aoui57fed7duz3wa
{
  ALTER TYPE waicolle::Waifu {
      CREATE MULTI LINK ascended_from: waicolle::Waifu {
          ON TARGET DELETE ALLOW;
      };
      CREATE MULTI LINK ascended_to := (.<ascended_from[IS waicolle::Waifu]);
      CREATE PROPERTY disabled := (EXISTS (.ascended_to));
  };
};
