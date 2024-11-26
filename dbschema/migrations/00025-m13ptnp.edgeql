CREATE MIGRATION m13ptnpczpdqcveh7kqjqsqf6wy7c723cmcqo6aoui57fed7duz3wa
    ONTO m1h2cd2drglgt2qvagqif5js7c6ui6f42nr2225g24xmlshixduqoq
{
  ALTER TYPE waicolle::Waifu {
      ALTER PROPERTY trade_locked {
          USING (EXISTS ((SELECT
              (.<received[IS waicolle::TradeOperation] UNION .<offered[IS waicolle::TradeOperation])
          FILTER
              NOT (EXISTS (.completed_at))
          )));
      };
  };
};
