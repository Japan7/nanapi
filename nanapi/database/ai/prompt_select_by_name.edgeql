select ai::Prompt {
  name,
  description,
  prompt,
  arguments: { name, description }
}
filter .client = global client
and .name = <str>$name
