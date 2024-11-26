CREATE MIGRATION m1le6voeri4lwdmnryfylvuh3apwr5butrbqnmsuguniwuteoqf4qq
    ONTO m1connfa6f7l2poqf7qc37vksj2vxqkhogqjvdw4v43mhd52roxtta
{
  ALTER TYPE waicolle::Trade {
      EXTENDING waicolle::Operation LAST;
      ALTER LINK author {
          RESET OPTIONALITY;
          DROP OWNED;
          RESET TYPE;
      };
      ALTER LINK received {
          RESET CARDINALITY;
          DROP OWNED;
          RESET TYPE;
      };
      ALTER PROPERTY created_at {
          RESET OPTIONALITY;
          DROP OWNED;
          RESET TYPE;
      };
  };
};
