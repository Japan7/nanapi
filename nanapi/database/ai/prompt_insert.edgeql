insert ai::Prompt {
  client := global client,
  name := <str>$name,
  description := <optional str>$description,
  prompt := <str>$prompt,
  arguments := (
    for arg in array_unpack(<array<json>>$arguments) union (
      insert ai::PromptArgument {
        client := global client,
        name := <str>json_get(arg, 'name'),
        description := <optional str>json_get(arg, 'description'),
      }
    )
  )
}
