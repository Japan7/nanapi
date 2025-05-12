module role {
  type Role extending default::ClientObject {
    required property role_id -> str;
    required property emoji -> str;
    constraint exclusive on ((.client, .role_id));
    constraint exclusive on ((.client, .emoji));
    index on (.role_id);
  }
}
