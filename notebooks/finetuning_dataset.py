import json
from typing import cast

import gel
from pydantic import BaseModel, TypeAdapter
from settings import NANAPI_CLIENT_ID

client = cast(
    gel.Client,
    gel.create_client().with_globals(client_id=NANAPI_CLIENT_ID),  # pyright: ignore[reportUnknownMemberType]
)


class MessageData(BaseModel):
    referenced_content: str
    content: str


def load_messages():
    resp = client.query_json(  # pyright: ignore[reportUnknownMemberType]
        r"""
        select discord::Message {
            referenced_content := .data['referenced_message']['content'],
            content,
        }
        filter not exists .noindex
        and .author_id = '168753518386216960'
        and exists json_get(.data, 'referenced_message', 'content')
        and not (<bool>json_get(.data, 'referenced_message', 'author', 'bot') ?? false)
        order by .timestamp desc
        """,
    )
    return TypeAdapter(list[MessageData]).validate_json(resp, strict=False)


def chatml_format(messages: list[MessageData]):
    chatml_data = [
        {
            'messages': [
                {
                    'role': 'user',
                    'content': [
                        {'type': 'text', 'text': msg.referenced_content},
                    ],
                },
                {
                    'role': 'assistant',
                    'content': [
                        {'type': 'text', 'text': msg.content},
                    ],
                },
            ]
        }
        for msg in messages
        if msg.referenced_content and msg.content
    ]
    return chatml_data


if __name__ == '__main__':
    messages = load_messages()
    chatml_data = chatml_format(messages)
    with open('finetuning_dataset.jsonl', 'w') as f:
        for entry in chatml_data:
            f.write(json.dumps(entry) + '\n')
