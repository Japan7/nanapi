from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  message_id := <str>$message_id,
select poll::Poll {
  message_id,
  channel_id,
  question,
  options: {
    rank,
    text,
    votes: {
      user: {
        discord_id,
      }
    }
  }
}
filter .message_id = message_id
"""


class PollGetByMessageIdResultOptionsVotesUser(BaseModel):
    discord_id: str


class PollGetByMessageIdResultOptionsVotes(BaseModel):
    user: PollGetByMessageIdResultOptionsVotesUser


class PollGetByMessageIdResultOptions(BaseModel):
    rank: int
    text: str
    votes: list[PollGetByMessageIdResultOptionsVotes]


class PollGetByMessageIdResult(BaseModel):
    message_id: str
    channel_id: str
    question: str
    options: list[PollGetByMessageIdResultOptions]


adapter = TypeAdapter(PollGetByMessageIdResult | None)


async def poll_get_by_message_id(
    executor: AsyncIOExecutor,
    *,
    message_id: str,
) -> PollGetByMessageIdResult | None:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        message_id=message_id,
    )
    return adapter.validate_json(resp, strict=False)
