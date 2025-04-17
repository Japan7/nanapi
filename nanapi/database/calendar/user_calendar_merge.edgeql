with
  discord_id := <str>$discord_id,
  discord_username := <str>$discord_username,
  ics := <str>$ics,
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
insert calendar::UserCalendar {
  ics := ics,
  user := user,
}
unless conflict on .user
else (
  update calendar::UserCalendar set {
    ics := ics,
  }
)
