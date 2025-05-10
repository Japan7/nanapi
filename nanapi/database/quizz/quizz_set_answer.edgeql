with
  id := <uuid>$id,
  answer := <optional str>$answer,
  hints := <optional array<str>>$hints,
update quizz::Quizz
filter .id = id
set {
  answer := answer,
  hints := hints,
}
