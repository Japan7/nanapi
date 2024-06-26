with
  id_al := <int32>$id_al,
select anilist::CharacterEdge {
  character_role,
  media: {
    id_al,
    favourites,
    site_url,
    type,
    id_mal,
    title_user_preferred,
    title_native,
    title_english,
    synonyms,
    description,
    status,
    season,
    season_year,
    episodes,
    duration,
    chapters,
    cover_image_extra_large,
    cover_image_color,
    popularity,
    is_adult,
    genres,
  },
  character: {
    id_al,
    favourites,
    site_url,
    name_user_preferred,
    name_alternative,
    name_alternative_spoiler,
    name_native,
    description,
    image_large,
    gender,
    age,
    date_of_birth_year,
    date_of_birth_month,
    date_of_birth_day,
    rank,
    fuzzy_gender,
  },
}
filter .voice_actors.id_al = id_al
order by .media.popularity desc
