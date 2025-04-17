with
  discord_id := <str>$discord_id,
  calendar := (select calendar::UserCalendar filter .user.discord_id = discord_id),
select assert_single(calendar) { ** }
