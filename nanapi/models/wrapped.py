from pydantic import BaseModel


class WrappedEmbedField(BaseModel):
    name: str
    value: str
    inline: bool = True


class WrappedEmbed(BaseModel):
    title: str | None = None
    description: str | None = None
    color: int | None = None
    fields: list[WrappedEmbedField] = []
    footer: str | None = None
    image_url: str | None = None


class WrappedResponse(BaseModel):
    embeds: list[WrappedEmbed]
