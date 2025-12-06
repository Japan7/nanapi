from gel import AsyncIOClient

from nanapi.database.wrapped.wrapped_get_emote_stats import wrapped_get_emote_stats
from nanapi.models.wrapped import WrappedEmbed, WrappedEmbedField
from nanapi.utils.wrapped.common import (
    COLOR_YELLOW,
    get_medal,
    get_wrapped_footer,
    get_year_bounds,
    pick_template,
)

# Thresholds for emote usage
# 2025 data (excluding bot messages): N=42, P10=2, P25=13, P50=217, P75=1082, P90=1943
EMOTE_THRESHOLD_LOW = 13  # ~P25
EMOTE_THRESHOLD_MODERATE = 217  # ~P50
EMOTE_THRESHOLD_HIGH = 1082  # ~P75

# Sarcastic comments for emote usage
EMOTE_LURKER = [
    'You used **0 emotes**. No personality? :OkayuSad:',
    'Zero emotes. Do you communicate via telepathy or are you just sad? :pepeLoser:',
]

EMOTE_LOW = [
    '**{count}** emotes. Are you typing with mittens or what?',
    "**{count}** emotes. That's shy.",
]

EMOTE_MODERATE = [
    "**{count}** emotes this year. You're a normal user, congratulations.",
    '**{count}** emotes. Not bad, not bad.',
]

EMOTE_HIGH = [
    '**{count}** emotes. You speak in hieroglyphics. :hype:',
    '**{count}** emotes. You like expressing yourself visually. :FubukiGO:',
]

EMOTE_VERY_HIGH = [
    (
        '**{count}** emotes. You communicate mainly '
        'via pictograms like a modern caveman. :Jeanjean:'
    ),
    '**{count}** emotes. We need to talk about your addiction. :NotLikeHikari:',
]

# Emote thresholds with their templates (in ascending order)
EMOTE_THRESHOLDS = [
    (1, EMOTE_LURKER),
    (EMOTE_THRESHOLD_LOW, EMOTE_LOW),
    (EMOTE_THRESHOLD_MODERATE, EMOTE_MODERATE),
    (EMOTE_THRESHOLD_HIGH, EMOTE_HIGH),
]


def build_emote_stats_embeds(
    total_count: int,
    top_emotes: list[tuple[str, int]],
    year: int,
) -> list[WrappedEmbed]:
    """Build embeds for emote stats with sarcastic comments."""
    # Build main description from template
    template = pick_template(total_count, EMOTE_THRESHOLDS, EMOTE_VERY_HIGH)
    description = template.format(count=total_count)

    fields: list[WrappedEmbedField] = []

    # Add top emotes field
    if top_emotes:
        top_lines: list[str] = []
        for i, (name, count) in enumerate(top_emotes[:5]):
            medal = get_medal(i)
            top_lines.append(f'{medal} :{name}: × **{count}**')

        fields.append(
            WrappedEmbedField(
                name='🏆 Top emotes',
                value='\n'.join(top_lines),
                inline=False,
            )
        )

        # Add a comment about the favorite emote
        fav_name, fav_count = top_emotes[0]
        if total_count > 0:
            fav_pct = fav_count / total_count * 100
            if fav_pct > 50:
                comment = f':{fav_name}: = **{fav_pct:.0f}%** of your emotes. Obsessed?'
            elif fav_pct > 30:
                comment = f':{fav_name}: = **{fav_pct:.0f}%** of your emotes. Fan.'
            else:
                comment = f':{fav_name}: ({fav_pct:.0f}%)'
            fields.append(
                WrappedEmbedField(
                    name='❤️ Favorite',
                    value=comment,
                    inline=True,
                )
            )

    return [
        WrappedEmbed(
            title=f'✨ Emotes in {year}',
            description=description,
            color=COLOR_YELLOW,
            footer=get_wrapped_footer(year),
            fields=fields,
        )
    ]


async def get_emote_stats_embeds(
    edgedb: AsyncIOClient,
    discord_id: str,
    year: int,
) -> list[WrappedEmbed]:
    """Get emote stats for a user and build the embeds."""
    year_start, year_end = get_year_bounds(year)

    stats = await wrapped_get_emote_stats(
        edgedb,
        discord_id=discord_id,
        year_start=year_start,
        year_end=year_end,
    )

    # Get top emotes from pre-aggregated counts (sorted by count descending)
    top_emotes: list[tuple[str, int]] = []
    if stats.emote_counts:
        sorted_emotes = sorted(stats.emote_counts, key=lambda e: e.count, reverse=True)
        top_emotes = [(e.name, e.count) for e in sorted_emotes[:5]]

    return build_emote_stats_embeds(stats.total_emote_count, top_emotes, year)
