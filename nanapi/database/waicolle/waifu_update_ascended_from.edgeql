with
  ascended_id := <uuid>$ascended_id,
  ascended_from_ids := <array<uuid>>$ascended_from_ids,
  waifus := (select waicolle::Waifu filter .id in array_unpack(ascended_from_ids)),
update waicolle::Waifu
filter .id = ascended_id
set {
  ascended_from += waifus
}
