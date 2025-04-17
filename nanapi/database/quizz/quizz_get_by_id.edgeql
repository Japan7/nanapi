with
  id := <uuid>$id
select quizz::Quizz {
  id,
  channel_id,
  description,
  url,
  is_image,
  answer,
  answer_source,
  submitted_at,
  hikaried,
  author: {
    discord_id,
  },
}
filter .id = id;
