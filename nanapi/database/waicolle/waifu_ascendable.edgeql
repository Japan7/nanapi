with
  discord_id := <int64>$discord_id,
  player := (select waicolle::Player filter .client = global client and .user.discord_id = discord_id),
  waifus := (
    select waicolle::Waifu
    filter .client = global client
    and .owner = assert_exists(player)
    and not .trade_locked and not .blooded
    and not .disabled
  ),
  grouped := (
    group waifus
    using chara_id_al := .character.id_al
    by chara_id_al, .level
  ),
  counted := (
    select grouped {
      count := count(.elements),
    }
  ),
select counted {
  key: { chara_id_al, level },
  grouping,
  elements: {
    id,
    timestamp,
    level,
    locked,
    trade_locked,
    blooded,
    nanaed,
    custom_image,
    custom_name,
    custom_collage,
    custom_position,
    character: { id_al },
    owner: {
      user: {
        discord_id,
        discord_id_str,
      },
    },
    original_owner: {
      user: {
        discord_id,
        discord_id_str,
      },
    },
    custom_position_waifu: { id },
  } order by .timestamp desc
}
filter .count >= 4
