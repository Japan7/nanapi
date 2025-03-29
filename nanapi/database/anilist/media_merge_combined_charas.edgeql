with
  media := <json>$media,
  characters := <array<int32>>$characters,
  last_update := <int64>$last_update,
  _media := (
    with
      type := <anilist::MediaType>json_get(media, 'type'),
      id_al := <int32>json_get(media, 'id_al'),
      id_mal := <int32>json_get(media, 'id_mal'),
      title_user_preferred := <str>json_get(media, 'title_user_preferred'),
      title_english := <str>json_get(media, 'title_english'),
      title_native := <str>json_get(media, 'title_native'),
      synonyms := <array<str>>json_get(media, 'synonyms'),
      description := <str>json_get(media, 'description'),
      status := <anilist::MediaStatus>json_get(media, 'status'),
      season := <anilist::MediaSeason>json_get(media, 'season'),
      season_year := <int32>json_get(media, 'season_year'),
      episodes := <int32>json_get(media, 'episodes'),
      duration := <int32>json_get(media, 'duration'),
      chapters := <int32>json_get(media, 'chapters'),
      cover_image_extra_large := <str>json_get(media, 'cover_image_extra_large'),
      cover_image_color := <str>json_get(media, 'cover_image_color'),
      popularity := <int32>json_get(media, 'popularity'),
      favourites := <int32>json_get(media, 'favourites'),
      site_url := <str>json_get(media, 'site_url'),
      is_adult := <bool>json_get(media, 'is_adult'),
      genres := <array<str>>json_get(media, 'genres'),
      tags := <json>json_get(media, 'tags'),
    insert anilist::Media {
      type := type,
      id_al := id_al,
      id_mal := id_mal,
      last_update := last_update,
      title_user_preferred := title_user_preferred,
      title_english := title_english,
      title_native := title_native,
      synonyms := synonyms,
      description := description,
      status := status,
      season := season,
      season_year := season_year,
      episodes := episodes,
      duration := duration,
      chapters := chapters,
      cover_image_extra_large := cover_image_extra_large,
      cover_image_color := cover_image_color,
      popularity := popularity,
      favourites := favourites,
      site_url := site_url,
      is_adult := is_adult,
      genres := genres,
      tags := distinct (
        for tag in json_array_unpack(tags) union (
          with
            tag_id_al := <int32>json_get(tag, 'id_al'),
            tag_rank := <int32>json_get(tag, 'rank'),
          select anilist::Tag {
            @rank := tag_rank,
          }
          filter .id_al = tag_id_al
        )
      ),
    }
    unless conflict on .id_al
    else (
      update anilist::Media set {
        type := type,
        id_mal := id_mal,
        title_user_preferred := title_user_preferred,
        title_english := title_english,
        title_native := title_native,
        last_update := last_update,
        synonyms := synonyms,
        description := description,
        status := status,
        season := season,
        season_year := season_year,
        episodes := episodes,
        duration := duration,
        chapters := chapters,
        cover_image_extra_large := cover_image_extra_large,
        cover_image_color := cover_image_color,
        popularity := popularity,
        favourites := favourites,
        site_url := site_url,
        is_adult := is_adult,
        genres := genres,
        tags := distinct (
          for tag in json_array_unpack(tags) union (
            with
              tag_id_al := <int32>json_get(tag, 'id_al'),
              tag_rank := <int32>json_get(tag, 'rank'),
            select anilist::Tag {
              @rank := tag_rank,
            }
            filter .id_al = tag_id_al
          )
        ),
      }
    )
  ),
  _characters := (
    for chara_id in array_unpack(characters) union (
        select anilist::Character filter .id_al = <int32>chara_id
    )
  )
select {
  media := _media,
  characters := assert_distinct(_characters),
}
