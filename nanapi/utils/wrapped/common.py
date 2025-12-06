import random
from collections import Counter
from datetime import datetime
from typing import Callable, Iterable, TypeVar

from nanapi.settings import TZ

T = TypeVar('T')

# Common embed colors
COLOR_BLURPLE = 0x5865F2  # Discord blurple
COLOR_YELLOW = 0xFEE75C  # Gold/yellow
COLOR_BLUE = 0x3498DB  # Blue
COLOR_TWITTER = 0x1DA1F2  # Twitter blue
COLOR_PURPLE = 0x9B59B6  # Gacha purple
COLOR_WORDLE = 0x538D4E  # Wordle green

# Medal emojis for rankings (0-indexed)
MEDALS = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣']
MEDALS_EXTENDED = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
MEDAL_DEFAULT = '▫️'

# Rank order for display (best to worst)
RANK_ORDER = ['S', 'A', 'B', 'C', 'D', 'E']

# Rank emojis for waicolle
RANK_EMOJIS = {
    'S': '🟨',
    'A': '🟩',
    'B': '🟦',
    'C': '🟪',
    'D': '⬜',
    'E': '⬛',
}


def get_medal(index: int) -> str:
    """Get medal emoji for a ranking position (0-indexed).

    Args:
        index: 0-indexed position (0 = first place, 1 = second place, etc.)

    Returns:
        Medal emoji or default marker for positions beyond the medal list
    """
    if index < len(MEDALS):
        return MEDALS[index]
    return MEDAL_DEFAULT


def get_timezone_name() -> str:
    """Get the timezone name string for EdgeDB queries."""
    return str(TZ)


def get_year_bounds(year: int) -> tuple[datetime, datetime]:
    """Get the start and end datetime for a year in the configured timezone."""
    year_start = datetime(year, 1, 1, tzinfo=TZ)
    year_end = datetime(year + 1, 1, 1, tzinfo=TZ)
    return year_start, year_end


def get_hours_in_year(year: int) -> int:
    """Get the number of hours elapsed in a year.

    If the year is the current year, returns hours elapsed until now.
    Otherwise returns total hours in the year.
    """
    year_start = datetime(year, 1, 1, tzinfo=TZ)
    year_end = datetime(year + 1, 1, 1, tzinfo=TZ)
    now = datetime.now(TZ)

    if now < year_end:
        # Year not finished, use hours until now
        elapsed = now - year_start
    else:
        # Year finished, use total hours
        elapsed = year_end - year_start

    return int(elapsed.total_seconds() // 3600)


def pick_template(
    count: int,
    thresholds: list[tuple[int, list[str]]],
    default: list[str],
) -> str:
    """Pick a random template based on count thresholds.

    Args:
        count: The value to compare against thresholds
        thresholds: List of (threshold, templates) tuples in ascending order
        default: Templates to use if count exceeds all thresholds

    Returns:
        A randomly selected template string
    """
    for threshold, templates in thresholds:
        if count < threshold:
            return random.choice(templates)
    return random.choice(default)


def format_bar_graph(
    data: list[tuple[str, int]],
    max_count: int,
    bar_width: int = 10,
) -> str:
    """Format labeled data as a monospace bar graph.

    Args:
        data: List of (label, count) tuples
        max_count: Maximum count for scaling bars
        bar_width: Width of the bar in characters

    Returns:
        Formatted bar graph string with one line per item
    """
    lines: list[str] = []
    for label, count in data:
        bar_len = int((count / max_count) * bar_width) if max_count > 0 else 0
        bar = '█' * bar_len + '░' * (bar_width - bar_len)
        lines.append(f'`{label} {bar} {count:>5,}`')
    return '\n'.join(lines)


def build_rank_distribution(
    ranks: Iterable[T],
    get_value: Callable[[T], str] | None = None,
) -> tuple[Counter[str], list[str], float]:
    """Build rank distribution stats from a collection of rank values.

    Args:
        ranks: Iterable of rank objects or strings
        get_value: Optional function to extract rank string from objects.
                   If None, assumes ranks are already strings.

    Returns:
        Tuple of (rank_counts, dist_lines, sa_rate)
        - rank_counts: Counter of rank -> count
        - dist_lines: Formatted distribution lines for display
        - sa_rate: S+A percentage rate
    """
    if get_value is not None:
        rank_counts: Counter[str] = Counter(get_value(r) for r in ranks)
    else:
        rank_counts = Counter(ranks)  # type: ignore[arg-type]

    total = sum(rank_counts.values())

    # Build distribution lines
    dist_lines: list[str] = []
    for rank in RANK_ORDER:
        count = rank_counts.get(rank, 0)
        pct = (count / total * 100) if total > 0 else 0
        emoji = RANK_EMOJIS.get(rank, '▫️')
        dist_lines.append(f'{emoji} **{rank}**: {count} ({pct:.1f}%)')

    # Calculate S+A rate (luck indicator)
    s_count = rank_counts.get('S', 0)
    a_count = rank_counts.get('A', 0)
    sa_rate = ((s_count + a_count) / total * 100) if total > 0 else 0

    return rank_counts, dist_lines, sa_rate


def format_with_comment(base: str, comment: str) -> str:
    """Format a base string with an optional comment.

    Args:
        base: The main text
        comment: Additional comment (can be empty)

    Returns:
        Base string with comment appended if non-empty
    """
    if comment:
        return f'{base} {comment}'
    return base


def get_wrapped_footer(year: int) -> str:
    """Get the standard footer for wrapped embeds."""
    return f'Your {year} Wrapped'


def format_rate_line(
    label: str,
    rate: float,
    success: int,
    total: int,
    comment: str = '',
) -> str:
    """Format a rate statistic line.

    Args:
        label: The statistic label (e.g., "Success rate")
        rate: The percentage rate
        success: Number of successes
        total: Total attempts
        comment: Optional comment to append

    Returns:
        Formatted rate line
    """
    base = f'🎯 **{label}**: {rate:.1f}% ({success}/{total})'
    return format_with_comment(base, comment)
