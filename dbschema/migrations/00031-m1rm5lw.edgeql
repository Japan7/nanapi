CREATE MIGRATION m1rm5lwsh576n5jgeuf547yphao2nzjbbxce6vctn3fmtkjjfccaoq
    ONTO m1byjsf7s7qwcbtu24hczjtd22sxdytbie5ymwlupgakylv3tjt4yq
{
  ALTER TYPE quizz::Game {
      DROP PROPERTY answer_bananed;
  };
  ALTER TYPE quizz::Quizz {
      DROP PROPERTY answer_source;
  };
  ALTER TYPE quizz::Quizz {
      ALTER PROPERTY description {
          RENAME TO question;
      };
  };
  ALTER TYPE quizz::Quizz {
      DROP PROPERTY hikaried;
  };
  ALTER TYPE quizz::Quizz {
      CREATE PROPERTY hints: array<std::str>;
  };
  ALTER TYPE quizz::Quizz {
      DROP PROPERTY is_image;
  };
  ALTER TYPE quizz::Quizz {
      ALTER PROPERTY url {
          RENAME TO attachment_url;
      };
  };
};
