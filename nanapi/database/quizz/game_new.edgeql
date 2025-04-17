with
  message_id := <str>$message_id,
  answer_bananed := <optional str>$answer_bananed,
  quizz_id := <uuid>$quizz_id,
  quizz := (select quizz::Quizz filter .id = quizz_id),
insert quizz::Game {
  client := global client,
  message_id := message_id,
  answer_bananed := answer_bananed,
  quizz := quizz,
}
