with
  discord_id := <str>$discord_id,
  profiles := (
    select user::Profile
    filter .user.discord_id = discord_id
  )
select profiles {
  birthday,
  full_name,
  graduation_year,
  photo,
  pronouns,
  n7_major,
  telephone,
  user: {
    discord_id,
  },
}
