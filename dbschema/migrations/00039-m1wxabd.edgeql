CREATE MIGRATION m1wxabdwbvl6uoqf7khxw5b7hyr342s4fvcchfqflgzwah5pwanora
    ONTO m1lbvqie7ow2wewdsenhxsafhudy6d3dyspvwq542t2g4lxym3ywyq
{
  ALTER TYPE discord::MessagePage {
      DROP INDEX ext::ai::index(embedding_model := 'text-embedding-3-small') ON (.context);
  };
  ALTER TYPE discord::MessagePage {
      CREATE DEFERRED INDEX ext::ai::index(embedding_model := 'text-embedding-3-large') ON (.context);
  };
};
