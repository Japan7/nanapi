module redis {
  type Data {
    required property key -> str {
      constraint exclusive;
    }
    required property value -> str;
    index on (.key);
  }
}
