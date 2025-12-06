from gel import AsyncIOClient

from nanapi.database.wrapped.wrapped_get_command_stats import (
    WrappedGetCommandStatsResult,
    wrapped_get_command_stats,
)
from nanapi.models.wrapped import WrappedEmbed
from nanapi.utils.wrapped.common import (
    COLOR_BLURPLE,
    get_medal,
    get_wrapped_footer,
    get_year_bounds,
)


def build_command_stats_embeds(
    stats: WrappedGetCommandStatsResult,
    year: int,
) -> list[WrappedEmbed]:
    """Build embeds for command usage statistics."""
    if not stats.command_distribution:
        return []

    lines: list[str] = []
    for i, cmd in enumerate(stats.command_distribution):
        medal = get_medal(i)
        lines.append(f'{medal} `/{cmd.command_name}` — **{cmd.count:,}** uses')

    total_commands = sum(cmd.count for cmd in stats.command_distribution)

    return [
        WrappedEmbed(
            title=f'🤖 Top Commands in {year}',
            description=f'You used **{total_commands:,}** bot commands:\n\n' + '\n'.join(lines),
            color=COLOR_BLURPLE,
            footer=get_wrapped_footer(year),
        )
    ]


async def get_command_stats_embeds(
    edgedb: AsyncIOClient,
    discord_id: str,
    year: int,
) -> list[WrappedEmbed]:
    """Fetch command stats from database and build embeds for a user's yearly wrapped."""
    year_start, year_end = get_year_bounds(year)

    stats = await wrapped_get_command_stats(
        edgedb,
        discord_id=discord_id,
        year_start=year_start,
        year_end=year_end,
    )

    return build_command_stats_embeds(stats, year)
