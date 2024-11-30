with
  discord_id := <int64>$discord_id,
  hide_singles := <bool>$hide_singles,
  player := (select waicolle::Player filter .client = global client and .user.discord_id = discord_id),
  player := assert_exists(player),
  unlocked := (
    select waicolle::Waifu
    filter .client = global client
    and not .locked
    and not .blooded
    and not .disabled
  ),
  tracked := (
    select unlocked
    filter .character.id_al in player.tracked_characters.id_al
    and ((
      with
        chara_id_al := .character.id_al,
        owned := (
          select detached waicolle::Waifu
          filter .character.id_al = chara_id_al
          and .owner = player
          and .locked
        ),
      select count(owned) != 1
    ) if hide_singles else true)
  ),
  duplicated := (
    select unlocked
    filter (
      with
        chara_id_al := .character.id_al,
        owned := (
          select detached waicolle::Waifu
          filter .character.id_al = chara_id_al
          and .owner = player
          and .locked
        ),
      select count(owned) > 1
    )
  ),
select distinct (tracked union duplicated) {
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
}
order by .timestamp desc
