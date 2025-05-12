with
  role_id := <str>$role_id,
  emoji := <str>$emoji,
  role := (
    insert role::Role {
      client := global client,
      role_id := role_id,
      emoji := emoji,
    }
  )
select role {
  role_id,
  emoji,
}
