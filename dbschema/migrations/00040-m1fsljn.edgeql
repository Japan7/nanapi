CREATE MIGRATION m1fsljnotyzxbwbpwm3myxe3dr4pdl3z4wgpdpo5kvi5hodgp2pzpq
    ONTO m1wxabdwbvl6uoqf7khxw5b7hyr342s4fvcchfqflgzwah5pwanora
{
  ALTER TYPE discord::MessagePage {
      DROP INDEX ext::ai::index(embedding_model := 'text-embedding-3-large') ON (.context);
  };
  ALTER TYPE discord::MessagePage {
      CREATE DEFERRED INDEX ext::ai::index(embedding_model := 'text-embedding-3-small') ON (.context);
  };
};
