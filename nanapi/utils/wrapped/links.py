from gel import AsyncIOClient

from nanapi.database.wrapped.wrapped_get_link_stats import (
    WrappedGetLinkStatsResult,
    wrapped_get_link_stats,
)
from nanapi.models.wrapped import WrappedEmbed
from nanapi.utils.wrapped.common import COLOR_TWITTER, get_wrapped_footer, get_year_bounds

# ============================================================================
# Constants
# ============================================================================

# Platform info: (field_name, emoji, display_name, sarcastic_comment)
PLATFORMS = [
    ('twitter_count', '🐦', 'Twitter/X', ':nicolas: certified'),
    ('youtube_count', '📺', 'YouTube', 'YouTube addict detected. Your recs must be wild. 📺'),
    ('tenor_count', '🎭', 'Tenor GIFs', 'GIF spammer extraordinaire. Words are overrated. 🎭'),
    ('reddit_count', '🟠', 'Reddit', 'Redditor moment :jeanjean:. Upvotes to the left. 🟠'),
    ('bluesky_count', '🦋', 'Bluesky', 'Early Bluesky adopter. Very avant-garde. 🦋'),
    ('discord_count', '💬', 'Discord', 'Sharing Discord links on Discord. Meta. 💬'),
    ('github_count', '🐙', 'GitHub', 'Open source enthusiast or just flexing your commits? 🐙'),
    ('anilist_count', '📊', 'AniList', 'Weeb credentials verified. Your taste is... unique. 📊'),
    ('instagram_count', '📷', 'Instagram', 'Instagram in a Discord server? Bold move. 📷'),
    ('wikipedia_count', '📚', 'Wikipedia', 'The intellectual. Actually reads sources. 📚'),
    ('steam_count', '🎮', 'Steam', 'Gamer alert. Your backlog must be massive. 🎮'),
]


# ============================================================================
# Embed Builders
# ============================================================================


def build_link_stats_embed(
    stats: WrappedGetLinkStatsResult,
    year: int,
) -> WrappedEmbed | None:
    """Build embed showing link sharing statistics."""
    if stats.total_link_count == 0:
        return None

    # Collect platforms with non-zero counts
    platform_stats: list[tuple[str, str, int, str]] = []
    for field_name, emoji, display_name, platform_comment in PLATFORMS:
        count = getattr(stats, field_name)
        if count > 0:
            platform_stats.append((emoji, display_name, count, platform_comment))

    # Sort by count descending
    platform_stats.sort(key=lambda x: x[2], reverse=True)

    # Build description
    lines: list[str] = [f'You shared **{stats.total_link_count:,}** links this year.']

    if platform_stats:
        lines.append('\n**Your link diet:**')
        # Show top 5 platforms
        for emoji, name, count, _ in platform_stats[:5]:
            pct = count / stats.total_link_count * 100
            lines.append(f'{emoji} **{name}**: {count:,} ({pct:.1f}%)')

    # Add sarcastic comment based on top platform
    if platform_stats:
        top_count = platform_stats[0][2]
        top_comment = platform_stats[0][3]
        top_pct = top_count / stats.total_link_count * 100

        if top_pct > 50:
            comment = top_comment
        else:
            comment = 'A diverse link portfolio. You have range. 📈'

        lines.append(f'\n_{comment}_')

    return WrappedEmbed(
        title=f'🔗 Links Shared in {year}',
        description='\n'.join(lines),
        color=COLOR_TWITTER,
        footer=get_wrapped_footer(year),
    )


# ============================================================================
# Public API
# ============================================================================


async def get_link_stats_embeds(
    edgedb: AsyncIOClient,
    discord_id: str,
    year: int,
) -> list[WrappedEmbed]:
    """Fetch link statistics and build embeds for a user's wrapped."""
    year_start, year_end = get_year_bounds(year)

    stats = await wrapped_get_link_stats(
        edgedb,
        discord_id=discord_id,
        year_start=year_start,
        year_end=year_end,
    )

    embeds: list[WrappedEmbed] = []

    embed = build_link_stats_embed(stats, year)
    if embed:
        embeds.append(embed)

    return embeds
