with
  discord_id := <str>$discord_id,
  discord_username := <str>$discord_username,
  birthday := <optional datetime>$birthday,
  full_name := <optional str>$full_name,
  graduation_year := <optional int16>$graduation_year,
  photo := <optional str>$photo,
  pronouns := <optional str>$pronouns,
  n7_major := <optional str>$n7_major,
  telephone := <optional str>$telephone,
  user := (
    insert user::User {
      discord_id := discord_id,
      discord_username := discord_username,
    }
    unless conflict on .discord_id
    else (
      update user::User set {
        discord_username := discord_username,
      }
    )
  ),
  profile := (
    insert user::Profile {
      birthday := birthday,
      full_name := full_name,
      graduation_year := graduation_year,
      photo := photo,
      pronouns := pronouns,
      n7_major := n7_major,
      telephone := telephone,
      user := user,
    }
    unless conflict on .user
    else (
      update user::Profile set {
        birthday := birthday,
        full_name := full_name,
        graduation_year := graduation_year,
        photo := photo,
        pronouns := pronouns,
        n7_major := n7_major,
        telephone := telephone,
      }
    )
  )
select profile {
  birthday,
  graduation_year,
  full_name,
  photo,
  pronouns,
  n7_major,
  telephone,
  user: {
    discord_id,
  },
}
