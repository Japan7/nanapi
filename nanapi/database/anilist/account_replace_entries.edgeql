with
  service := <anilist::Service>$service,
  username := <str>$username,
  type := <anilist::MediaType>$type,
  account := (select anilist::Account filter .service = service and .username = username),
delete anilist::Entry
filter .account = account and .media.type = type;

with
  service := <anilist::Service>$service,
  username := <str>$username,
  entries := <json>$entries,
  account := (select anilist::Account filter .service = service and .username = username),
for entry in json_array_unpack(entries) union (
  with
    id_al := <int32>json_get(entry, 'id_al'),
    status := <anilist::EntryStatus>json_get(entry, 'status'),
    progress := <int32>json_get(entry, 'progress'),
    score := <float32>json_get(entry, 'score'),
    media := (select anilist::Media filter .id_al = id_al),
  insert anilist::Entry {
    status := status,
    progress := progress,
    score := score,
    account := account,
    media := media,
  }
);
