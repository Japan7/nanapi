with
  role_id := <str>$role_id,
delete role::Role
filter .client = global client and .role_id = role_id
