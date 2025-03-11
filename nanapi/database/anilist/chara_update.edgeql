with
  characters := <array<int32>>$characters,
  last_update := <int64>$last_update,
for character_id in array_unpack(characters) union (
  update anilist::Character
  filter .id_al = <int32>character_id
  set {
    last_update := last_update
  }
)
