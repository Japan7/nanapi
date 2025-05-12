with
  discord_id := <str>$discord_id,
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
          and not .disabled
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
          and not .disabled
        ),
      select count(owned) > 1
    )
  ),
select distinct (tracked union duplicated) {
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
order by .timestamp desc
