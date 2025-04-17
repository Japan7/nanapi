with
  discord_id := <str>$discord_id,
  participant_id := <str>$participant_id,
update calendar::GuildEvent
filter .client = global client and .discord_id = discord_id
set {
  participants -= (select user::User filter .discord_id = participant_id),
};
