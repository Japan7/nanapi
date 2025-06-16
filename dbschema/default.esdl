module default {
  global client_id -> uuid;
  global client := (select Client filter .id = global client_id);

  type Client {
    required property username -> str {
      constraint exclusive;
    }
    required property password_hash -> str;
    index on (.username);
  }

  abstract type ClientObject {
    required link client -> Client {
      on target delete delete source;
    }
    access policy client_rw
      allow all
      using (global client ?= .client);
    access policy everyone_ro
      allow select;
  }
}
