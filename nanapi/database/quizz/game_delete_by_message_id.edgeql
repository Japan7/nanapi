with
  message_id := <str>$message_id
delete quizz::Game
filter .message_id = message_id
