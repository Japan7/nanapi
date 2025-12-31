using extension ai;

module ai {
  type Skill extending default::ClientObject {
    required property name -> str;
    required property description -> str;
    required property content -> str;
    constraint exclusive on ((.client, .name));
  }
}
