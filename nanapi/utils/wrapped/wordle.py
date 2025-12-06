import re
from collections import Counter
from dataclasses import dataclass

from gel import AsyncIOClient

from nanapi.database.wrapped.wrapped_get_wordle_stats import (
    WrappedGetWordleStatsResult,
    wrapped_get_wordle_stats,
)
from nanapi.models.wrapped import WrappedEmbed
from nanapi.utils.wrapped.common import (
    COLOR_WORDLE,
    format_bar_graph,
    get_wrapped_footer,
    get_year_bounds,
)


@dataclass
class WordleStats:
    """Parsed wordle statistics for a user."""

    games_played: int
    wins: int
    crowns: int
    avg_score: float
    fail_count: int
    scores: list[int]


def _parse_wordle_stats(
    stats: WrappedGetWordleStatsResult,
    discord_id: str,
) -> WordleStats:
    """Parse wordle messages and extract stats for a specific user."""
    user_pattern = f'<@{discord_id}>'

    games_played = 0
    wins = 0  # Games completed (not X/6)
    crowns = 0  # Games where user had 👑
    scores: list[int] = []  # List of scores (1-6, excluding X)

    for msg in stats.messages:
        content = msg.content
        if user_pattern not in content:
            continue

        games_played += 1

        # Check for crown
        lines = content.split('\n')
        for line in lines:
            if user_pattern in line:
                # Check if this line has crown
                if '👑' in line:
                    crowns += 1

                # Extract score
                match = re.search(r'(\d|X)/6:', line)
                if match:
                    score_str = match.group(1)
                    if score_str != 'X':
                        score = int(score_str)
                        scores.append(score)
                        wins += 1
                break

    avg_score = sum(scores) / len(scores) if scores else 0.0
    fail_count = games_played - wins

    return WordleStats(
        games_played=games_played,
        wins=wins,
        crowns=crowns,
        avg_score=avg_score,
        fail_count=fail_count,
        scores=scores,
    )


def build_wordle_stats_embeds(
    stats: WrappedGetWordleStatsResult,
    discord_id: str,
    year: int,
) -> list[WrappedEmbed]:
    """Build embeds for wordle statistics."""
    parsed = _parse_wordle_stats(stats, discord_id)

    if parsed.games_played == 0:
        return []

    # Build score distribution using shared format_bar_graph
    score_counts: Counter[int] = Counter(parsed.scores)
    max_count = max(score_counts.values()) if score_counts else 0

    data = [(f'{score}/6', score_counts.get(score, 0)) for score in range(1, 7)]
    dist_graph = format_bar_graph(data, max_count, bar_width=8)

    # Win rate
    win_rate = (parsed.wins / parsed.games_played) * 100

    # Sarcastic comments based on stats
    # 2025 data: N=15, P10=3.87, P25=4.11, P50=4.22, P75=4.44, P90=4.89
    if parsed.avg_score <= 4.0 and parsed.games_played >= 10:
        comment = "You're a Wordle god. Bow down, mortals. 🏆"
    elif parsed.avg_score <= 4.22:
        comment = 'Above average! Your vocabulary is... adequate. 📚'
    elif parsed.avg_score <= 4.44:
        comment = 'Solidly mediocre. You are the median. 📊'
    elif parsed.avg_score <= 4.89:
        comment = 'You get there eventually. Persistence is a virtue. 🐢'
    else:
        comment = 'Have you considered playing something easier? 😅'

    # Crown thresholds based on 2025 data:
    # N=17, P10=1, P25=5, P50=7, P75=9, P90=33
    if parsed.crowns >= 33:
        crown_comment = f'\n\n👑 **{parsed.crowns}** crowns — You dominated the group!'
    elif parsed.crowns >= 9:
        crown_comment = f'\n\n👑 **{parsed.crowns}** crowns — Competitive spirit!'
    elif parsed.crowns >= 5:
        crown_comment = f'\n\n👑 **{parsed.crowns}** crowns — Making your mark.'
    elif parsed.crowns >= 1:
        crown_comment = (
            f'\n\n👑 **{parsed.crowns}** crown{"s" if parsed.crowns > 1 else ""}'
            ' — A taste of victory.'
        )
    else:
        crown_comment = '\n\n👑 No crowns. Always the bridesmaid. 💔'

    description = (
        f'You played **{parsed.games_played}** Wordle games!\n\n'
        f'### Score Distribution\n'
        + dist_graph
        + f'\n\n📊 **Average**: {parsed.avg_score:.2f}/6\n'
        f'✅ **Win rate**: {win_rate:.0f}% ({parsed.wins}/{parsed.games_played})\n'
        f'❌ **Fails**: {parsed.fail_count}' + crown_comment + f'\n\n{comment}'
    )

    return [
        WrappedEmbed(
            title=f'🟩 Wordle Stats in {year}',
            description=description,
            color=COLOR_WORDLE,
            footer=get_wrapped_footer(year),
        )
    ]


async def get_wordle_stats_embeds(
    edgedb: AsyncIOClient,
    discord_id: str,
    year: int,
) -> list[WrappedEmbed]:
    """Fetch wordle stats from database and build embeds for a user's yearly wrapped."""
    year_start, year_end = get_year_bounds(year)

    stats = await wrapped_get_wordle_stats(
        edgedb,
        discord_id=discord_id,
        year_start=year_start,
        year_end=year_end,
    )

    return build_wordle_stats_embeds(stats, discord_id, year)
