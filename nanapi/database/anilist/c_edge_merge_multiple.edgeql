with
  edges := <array<tuple<
    voice_actor_ids: array<int32>,
    character_id: int32,
    media_id: int32,
    character_role: anilist::CharacterRole
  >>>$edges,
for edge in array_unpack(edges) union (
  with
    voice_actors := (select anilist::Staff filter .id_al in array_unpack(edge.voice_actor_ids)),
    character := (select anilist::Character filter .id_al = edge.character_id),
    media := (select anilist::Media filter .id_al = edge.media_id),
  insert anilist::CharacterEdge {
    character_role := edge.character_role,
    character := character,
    media := media,
    voice_actors := voice_actors,
  }
  unless conflict on ((.character, .media)) else (
    update anilist::CharacterEdge set {
      character_role := edge.character_role,
      voice_actors += voice_actors,
    }
  )
)
