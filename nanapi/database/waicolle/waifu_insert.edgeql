with
  discord_id := <str>$discord_id,
  charas_ids := <array<int32>>$charas_ids,
  player := (select waicolle::Player filter .client = global client and .user.discord_id = discord_id),
for id_al in array_unpack(charas_ids) union (
  with
    chara := (select anilist::Character filter .id_al = id_al),
    inserted := (
      insert waicolle::Waifu {
        client := global client,
        character := chara,
        owner := player,
        original_owner := player,
      }
    ),
  select inserted {
    *,
    character: { id_al },
    owner: {
      user: {
        discord_id,
      },
    },
    original_owner: {
      user: {
        discord_id,
      },
    },
    custom_position_waifu: { id },
  }
)
