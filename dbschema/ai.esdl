using extension ai;

module ai {
  type Prompt extending default::ClientObject {
    required property name -> str;
    required property prompt -> str;
    property description -> str;
    multi link arguments -> PromptArgument {
      constraint exclusive;
      on source delete delete target;
    }
    constraint exclusive on ((.client, .name));
  }

  type PromptArgument extending default::ClientObject {
    required property name -> str;
    property description -> str;
  }
}
