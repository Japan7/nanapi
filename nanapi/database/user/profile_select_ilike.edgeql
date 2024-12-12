with
  pattern := <str>$pattern
select user::Profile {
  birthday,
  full_name,
  graduation_year,
  photo,
  pronouns,
  n7_major,
  telephone,
  user: {
    discord_id,
    discord_id_str,
  },
}
filter .full_name ilike pattern or .telephone ilike pattern
