insert user::User {
    discord_id := <str>$discord_id,
    age_verified := <bool>$age_verified,
    discord_username := <str>$discord_username,
}
unless conflict on .discord_id
else (
    update user::User set {
        age_verified := <bool>$age_verified,
        discord_username := <str>$discord_username,
    }
)
