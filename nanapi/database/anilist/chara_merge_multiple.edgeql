with
  characters := <json>$characters,
for character in json_array_unpack(characters) union (
  with
    id_al := <int32>json_get(character, 'id_al'),
    name_user_preferred := <str>json_get(character, 'name_user_preferred'),
    name_alternative := <array<str>>json_get(character, 'name_alternative'),
    name_alternative_spoiler := <array<str>>json_get(character, 'name_alternative_spoiler'),
    name_native := <str>json_get(character, 'name_native'),
    description := <str>json_get(character, 'description'),
    image_large := <str>json_get(character, 'image_large'),
    gender := <str>json_get(character, 'gender'),
    age := <str>json_get(character, 'age'),
    date_of_birth_year := <int32>json_get(character, 'date_of_birth_year'),
    date_of_birth_month := <int32>json_get(character, 'date_of_birth_month'),
    date_of_birth_day := <int32>json_get(character, 'date_of_birth_day'),
    favourites := <int32>json_get(character, 'favourites'),
    site_url := <str>json_get(character, 'site_url'),
  insert anilist::Character {
    id_al := id_al,
    name_user_preferred := name_user_preferred,
    name_alternative := name_alternative,
    name_alternative_spoiler := name_alternative_spoiler,
    name_native := name_native,
    description := description,
    image_large := image_large,
    gender := gender,
    age := age,
    date_of_birth_year := date_of_birth_year,
    date_of_birth_month := date_of_birth_month,
    date_of_birth_day := date_of_birth_day,
    favourites := favourites,
    site_url := site_url,
  }
  unless conflict on .id_al
  else (
    update anilist::Character set {
      name_user_preferred := name_user_preferred,
      name_alternative := name_alternative,
      name_alternative_spoiler := name_alternative_spoiler,
      name_native := name_native,
      description := description,
      image_large := image_large,
      gender := gender,
      age := age,
      date_of_birth_year := date_of_birth_year,
      date_of_birth_month := date_of_birth_month,
      date_of_birth_day := date_of_birth_day,
      favourites := favourites,
      site_url := site_url,
    }
  )
)
