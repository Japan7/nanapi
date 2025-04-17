with
  id := <uuid>$id,
  participant_id := <str>$participant_id,
  participant_username := <str>$participant_username,
  participant := (
    insert user::User {
      discord_id := participant_id,
      discord_username := participant_username,
    }
    unless conflict on .discord_id
    else (
      update user::User set {
        discord_username := participant_username,
      }
    )
  ),
update projection::Projection
filter .id = id
set {
  participants += participant,
};
