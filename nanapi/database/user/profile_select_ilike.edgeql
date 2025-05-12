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
  },
}
filter (
  (.full_name ilike pattern) ?? false
  or (.n7_major ilike pattern) ?? false
  or (.pronouns ilike pattern) ?? false
)
