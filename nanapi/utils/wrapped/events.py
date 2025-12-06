from gel import AsyncIOClient

from nanapi.database.wrapped.wrapped_get_event_stats import (
    WrappedGetEventStatsResult,
    wrapped_get_event_stats,
)
from nanapi.models.wrapped import WrappedEmbed
from nanapi.utils.wrapped.common import (
    COLOR_BLURPLE,
    get_medal,
    get_wrapped_footer,
    get_year_bounds,
)

# ============================================================================
# Helper Functions
# ============================================================================


def _format_runtime(minutes: int) -> str:
    """Format runtime in hours and minutes."""
    hours = minutes // 60
    remaining_mins = minutes % 60
    if hours > 0:
        return f'{hours}h {remaining_mins}min'
    return f'{remaining_mins}min'


# ============================================================================
# Embed Builders
# ============================================================================


def build_event_stats_embeds(
    stats: WrappedGetEventStatsResult,
    year: int,
) -> list[WrappedEmbed]:
    """Build embeds for event statistics."""
    if stats.total_events == 0:
        return []

    embeds: list[WrappedEmbed] = []

    # Main events embed
    embeds.append(_build_main_events_embed(stats, year))

    # BFFs embed if we have co-participants
    if stats.top_bffs:
        embeds.append(_build_bffs_embed(stats, year))

    return embeds


def _build_main_events_embed(
    stats: WrappedGetEventStatsResult,
    year: int,
) -> WrappedEmbed:
    """Build the main events statistics embed."""
    # Event thresholds based on 2025 data:
    # N=46, P10=2, P25=4, P50=9, P75=18, P90=50
    if stats.total_events >= 50:
        event_comment = "You're basically living at the Discord events! 🏠"
    elif stats.total_events >= 18:
        event_comment = 'A true community pillar. Respect. 🫡'
    elif stats.total_events >= 9:
        event_comment = 'Solid attendance! You actually show up. 📅'
    elif stats.total_events >= 4:
        event_comment = 'You poke your head in occasionally. 👀'
    else:
        event_comment = 'A rare sighting indeed. 🦄'

    # Projection stats
    projection_section = ''
    if stats.projection_count > 0:
        runtime_str = _format_runtime(stats.projection_runtime)
        projection_section = (
            f'\n\n### Projections\n'
            f'You registered for **{stats.projection_count}** projection sessions!\n'
            f'Total runtime: **{runtime_str}** of anime watched together.\n'
        )

        # Runtime thresholds based on 2025 data:
        # N=18, P10=35, P25=48, P50=228, P75=915, P90=1259
        if stats.projection_runtime >= 1259:  # ~21 hours (P90)
            projection_section += "\nThat's a lot of couch time. Your back okay? 🛋️"
        elif stats.projection_runtime >= 915:  # ~15 hours (P75)
            projection_section += '\nA dedicated projection enjoyer! 🍿'
        elif stats.projection_runtime >= 228:  # ~4 hours (P50)
            projection_section += '\nA healthy amount of group watching! 📺'

    description = (
        f'You registered for **{stats.total_events}** events this year!\n\n'
        f'{event_comment}'
        f'{projection_section}'
    )

    return WrappedEmbed(
        title=f'📅 Event Stats in {year}',
        description=description,
        color=COLOR_BLURPLE,
        footer=get_wrapped_footer(year),
    )


def _build_bffs_embed(
    stats: WrappedGetEventStatsResult,
    year: int,
) -> WrappedEmbed:
    """Build the BFFs (people you attended events with most) embed."""
    bff_lines: list[str] = []

    for i, bff in enumerate(stats.top_bffs):
        medal = get_medal(i)
        # Use Discord mention format
        bff_lines.append(f'{medal} <@{bff.discord_id}> — **{bff.count}** events together')

    # BFF thresholds based on 2025 data:
    # P50=7, P75=13, P90=35
    if stats.top_bffs and stats.top_bffs[0].count >= 35:
        comment = '\nYou are basically inseparable. Get a room (or a watch party). 💕'
    elif stats.top_bffs and stats.top_bffs[0].count >= 13:
        comment = '\nA strong friendship forged in Discord events! 🤝'
    elif stats.top_bffs and stats.top_bffs[0].count >= 7:
        comment = '\nYou have solid event buddies! 👯'
    else:
        comment = '\nYour event crew is forming! 🌱'

    description = (
        '### Your Event BFFs\n'
        'The people you hung out with the most at events:\n\n' + '\n'.join(bff_lines) + comment
    )

    return WrappedEmbed(
        title=f'👥 Your Event BFFs in {year}',
        description=description,
        color=COLOR_BLURPLE,
        footer=get_wrapped_footer(year),
    )


# ============================================================================
# Public API
# ============================================================================


async def get_event_stats_embeds(
    edgedb: AsyncIOClient,
    discord_id: str,
    year: int,
) -> list[WrappedEmbed]:
    """Fetch event stats from database and build embeds for a user's yearly wrapped."""
    year_start, year_end = get_year_bounds(year)

    stats = await wrapped_get_event_stats(
        edgedb,
        discord_id=discord_id,
        year_start=year_start,
        year_end=year_end,
    )

    return build_event_stats_embeds(stats, year)
