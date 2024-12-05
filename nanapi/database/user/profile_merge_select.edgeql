with
  discord_id := <int64>$discord_id,
  discord_username := <str>$discord_username,
  birthday := <optional datetime>$birthday,
  full_name := <optional str>$full_name,
  photo := <optional str>$photo,
  promotion := <optional str>$promotion,
  pronouns := <optional str>$pronouns,
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
      photo := photo,
      promotion := promotion,
      pronouns := pronouns,
      telephone := telephone,
      user := user,
    }
    unless conflict on .user
    else (
      update user::Profile set {
        birthday := birthday,
        full_name := full_name,
        photo := photo,
        promotion := promotion,
        pronouns := pronouns,
        telephone := telephone,
      }
    )
  )
select profile {
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
