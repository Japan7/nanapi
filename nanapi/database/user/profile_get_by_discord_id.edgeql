with
  discord_id := <int64>$discord_id,
  profiles := (
    select user::Profile
    filter .user.discord_id = discord_id
  )
select profiles {
  birthday,
  full_name,
  photo,
  promotion,
  pronouns,
  telephone,
  user: {
    discord_id,
    discord_id_str,
  },
}
