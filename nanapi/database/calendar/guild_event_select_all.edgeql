with
  start_after := <optional datetime>$start_after,
select calendar::GuildEvent {
  *,
  organizer: { * },
  participants: { * },
}
filter .client = global client
and (.start_time > start_after if exists start_after else true)
