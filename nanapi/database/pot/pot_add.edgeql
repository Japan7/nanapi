with
  discord_id := <str>$discord_id,
  discord_username := <str>$discord_username,
  amount := <float32>$amount,
  user := (
    insert user::User {
      discord_id := discord_id,
      discord_username := discord_username,
    }
    unless conflict on .discord_id
    else (
      update user::User set {
        discord_username := discord_username,
      }
    )
  ),
  pot := (
    insert pot::Pot {
      client := global client,
      amount := amount,
      count := 1,
      user := user,
    }
    unless conflict on ((.client, .user))
    else (
      update pot::Pot set {
        amount := .amount + amount,
        count := .count + 1,
      }
    )
  ),
select pot { amount, count }
