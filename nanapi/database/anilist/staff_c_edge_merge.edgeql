with
  staff := <int32>$staff,
  characters := <json>$characters,
for edge in json_array_unpack(characters) union (
  with
    voice_actor_ids := <array<int32>>json_get(edge, 'voice_actor_ids'),
    character_id := <int32>json_get(edge, 'character_id'),
    media_id := <int32>json_get(edge, 'media_id'),
    character_role := <anilist::CharacterRole>json_get(edge, 'character_role'),
    voice_actor := (select anilist::Staff filter .id_al in array_unpack(voice_actor_ids)),
    character := (select anilist::Character filter .id_al = character_id),
    media := (select anilist::Media filter .id_al = media_id),
  insert anilist::CharacterEdge {
    character_role := character_role,
    character := character,
    media := media,
    voice_actors := voice_actor,
  }
  unless conflict on ((.character, .media)) else (
    update anilist::CharacterEdge set {
      character_role := character_role,
      voice_actors += voice_actor,
    }
  )
)
