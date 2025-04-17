with
  discord_id := <str>$discord_id,
  name := <str>$name,
  description := <optional str>$description,
  location := <optional str>$location,
  start_time := <datetime>$start_time,
  end_time := <datetime>$end_time,
  image := <optional str>$image,
  url := <optional str>$url,
  organizer_id := <str>$organizer_id,
  organizer_username := <str>$organizer_username,
  organizer := (
    insert user::User {
      discord_id := organizer_id,
      discord_username := organizer_username,
    }
    unless conflict on .discord_id
    else (
      update user::User set {
        discord_username := organizer_username,
      }
    )
  ),
  event := (
    insert calendar::GuildEvent {
      client := global client,
      discord_id := discord_id,
      name := name,
      description := description,
      location := location,
      start_time := start_time,
      end_time := end_time,
      image := image,
      url := url,
      organizer := organizer,
    }
    unless conflict on ((.client, .discord_id))
    else (
      update calendar::GuildEvent set {
        name := name,
        description := description,
        location := location,
        start_time := start_time,
        end_time := end_time,
        image := image,
        url := url,
        organizer := organizer,
      }
    )
  ),
select assert_exists(event) { ** }
