import asyncio

from fastapi import Depends, Query
from gel import AsyncIOClient

from nanapi.models.wrapped import WrappedEmbed, WrappedResponse
from nanapi.utils.fastapi import NanAPIRouter, get_client_edgedb
from nanapi.utils.wrapped.commands import get_command_stats_embeds
from nanapi.utils.wrapped.common import COLOR_BLURPLE, get_wrapped_footer
from nanapi.utils.wrapped.emotes import get_emote_stats_embeds
from nanapi.utils.wrapped.events import get_event_stats_embeds
from nanapi.utils.wrapped.links import get_link_stats_embeds
from nanapi.utils.wrapped.messages import get_message_stats_embeds
from nanapi.utils.wrapped.waicolle import get_waicolle_stats_embeds
from nanapi.utils.wrapped.wordle import get_wordle_stats_embeds
from nanapi.utils.wrapped.words import get_words_stats_embeds

router = NanAPIRouter(prefix='/wrapped', tags=['wrapped'])


@router.oauth2_client.get('/{discord_id}', response_model=WrappedResponse)
async def get_wrapped(
    discord_id: str,
    year: int = Query(default=2025, ge=2020, le=2030),
    edgedb: AsyncIOClient = Depends(get_client_edgedb),
):
    """Get wrapped statistics for a user for a given year.

    Returns a list of embeds with fun statistics and absurdist comparisons.
    """
    embed_lists = await asyncio.gather(
        get_message_stats_embeds(edgedb, discord_id, year),
        get_words_stats_embeds(edgedb, discord_id, year),
        get_emote_stats_embeds(edgedb, discord_id, year),
        get_link_stats_embeds(edgedb, discord_id, year),
        get_command_stats_embeds(edgedb, discord_id, year),
        get_wordle_stats_embeds(edgedb, discord_id, year),
        get_event_stats_embeds(edgedb, discord_id, year),
        get_waicolle_stats_embeds(edgedb, discord_id, year),
    )
    # Flatten the list of lists into a single list
    embeds = [embed for embed_list in embed_lists for embed in embed_list]

    # Add welcome embed at the beginning
    welcome_embed = WrappedEmbed(
        title=f'🎉 Your {year} Wrapped',
        description=(
            f'Hey <@{discord_id}>!\n\n'
            f"Here's your **{year} Wrapped** — a look back at your year on Japan7.\n\n"
            'Swipe through to see your stats! 👉'
        ),
        color=COLOR_BLURPLE,
        footer=get_wrapped_footer(year),
    )
    embeds.insert(0, welcome_embed)

    # Add final embed at the end
    final_embed = WrappedEmbed(
        title=f"🎊 That's a Wrap on {year}!",
        description=(
            f'Thanks for being part of Japan7 this year, <@{discord_id}>!\n\n'
            f"Here's to even more memories in {year + 1}! 🥂\n\n"
            'See you next year! 💜'
        ),
        color=COLOR_BLURPLE,
        footer=get_wrapped_footer(year),
    )
    embeds.append(final_embed)

    return WrappedResponse(embeds=embeds)
