with
  discord_id := <str>$discord_id
delete calendar::UserCalendar
filter .user.discord_id = discord_id
