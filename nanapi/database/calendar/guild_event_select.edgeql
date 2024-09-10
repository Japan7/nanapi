with
  discord_id := <optional int64>$discord_id,
  start_after := <optional datetime>$start_after,
select calendar::GuildEvent { ** }
filter .client = global client
and (.participants.discord_id = discord_id if exists discord_id else true)
and (.start_time > start_after if exists start_after else true)
