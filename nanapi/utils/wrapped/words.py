"""
Word analysis for Wrapped statistics.

Identifies user's top words and characteristic words compared to community.
No external NLP libraries required - uses simple frequency analysis.
"""

import asyncio
import math
import re
from collections import Counter

from gel import AsyncIOClient

from nanapi.database.wrapped.wrapped_get_community_words import (
    wrapped_get_community_words,
)
from nanapi.database.wrapped.wrapped_get_user_words import wrapped_get_user_words
from nanapi.models.wrapped import WrappedEmbed
from nanapi.utils.wrapped.common import (
    COLOR_BLUE,
    MEDALS_EXTENDED,
    get_wrapped_footer,
    get_year_bounds,
)

# Common French/English stopwords to exclude
STOPWORDS = {
    # French
    'le',
    'la',
    'les',
    'un',
    'une',
    'des',
    'de',
    'du',
    'et',
    'ou',
    'mais',
    'est',
    'sont',
    'a',
    'ai',
    'as',
    'ont',
    'eu',
    'été',
    'être',
    'avoir',
    'pour',
    'par',
    'sur',
    'dans',
    'avec',
    'sans',
    'sous',
    'ce',
    'cet',
    'cette',
    'ces',
    'mon',
    'ton',
    'son',
    'ma',
    'ta',
    'sa',
    'mes',
    'tes',
    'ses',
    'notre',
    'votre',
    'leur',
    'nos',
    'vos',
    'leurs',
    'je',
    'tu',
    'il',
    'elle',
    'nous',
    'vous',
    'ils',
    'elles',
    'qui',
    'que',
    'quoi',
    'dont',
    'où',
    'si',
    'oui',
    'non',
    'ne',
    'pas',
    'plus',
    'moins',
    'très',
    'trop',
    'peu',
    'beaucoup',
    'tout',
    'toute',
    'tous',
    'toutes',
    'ça',
    'cela',
    'là',
    'ici',
    'alors',
    'donc',
    'car',
    'comme',
    'quand',
    'y',
    'en',
    'se',
    'moi',
    'toi',
    'lui',
    'eux',
    'soi',
    'fait',
    'faire',
    'peut',
    'faut',
    'vais',
    'va',
    'vont',
    'aller',
    'dit',
    'dire',
    'bien',
    'bon',
    'aussi',
    'encore',
    'même',
    'autre',
    'autres',
    'nan',
    'ouais',
    'bah',
    'ben',
    'ah',
    'oh',
    'eh',
    'hein',
    'mdr',
    'lol',
    'ptdr',
    'xd',
    'jsp',
    'jsais',
    'chais',
    'genre',
    'truc',
    'trucs',
    'coup',
    'fois',
    'rien',
    'jamais',
    'toujours',
    'après',
    'avant',
    'juste',
    'vraiment',
    'déjà',
    'tellement',
    'parce',
    'pourquoi',
    'comment',
    'depuis',
    'pendant',
    'entre',
    'vers',
    'chez',
    # English
    'the',
    'be',
    'to',
    'of',
    'and',
    'in',
    'that',
    'have',
    'it',
    'for',
    'not',
    'on',
    'with',
    'he',
    'you',
    'do',
    'at',
    'this',
    'but',
    'his',
    'by',
    'from',
    'they',
    'we',
    'say',
    'her',
    'she',
    'or',
    'an',
    'will',
    'my',
    'one',
    'all',
    'would',
    'there',
    'their',
    'what',
    'so',
    'up',
    'out',
    'if',
    'about',
    'who',
    'get',
    'which',
    'go',
    'me',
    'when',
    'make',
    'can',
    'like',
    'time',
    'no',
    'him',
    'know',
    'take',
    'people',
    'into',
    'year',
    'your',
    'good',
    'some',
    'could',
    'them',
    'see',
    'other',
    'than',
    'then',
    'now',
    'look',
    'only',
    'come',
    'its',
    'over',
    'think',
    'also',
    'back',
    'after',
    'use',
    'two',
    'how',
    'our',
    'work',
    'first',
    'well',
    'way',
    'even',
    'new',
    'want',
    'because',
    'any',
    'these',
    'give',
    'day',
    'most',
    'us',
    'is',
    'was',
    'are',
    'been',
    'has',
    'had',
    'were',
    'am',
    'did',
    'does',
    'im',
    'ive',
    'youre',
    'wont',
    'cant',
    'isnt',
    'yeah',
    'yes',
    'ok',
    'okay',
    'got',
    'thing',
    'things',
    'really',
    'very',
    'much',
    'more',
    'too',
    'here',
    'still',
    'actually',
    'pretty',
}

# Discord-specific patterns to remove
DISCORD_PATTERNS = [
    r'<@!?\d+>',  # User mentions
    r'<#\d+>',  # Channel mentions
    r'<@&\d+>',  # Role mentions
    r'<a?:\w+:\d+>',  # Custom emojis
    r'https?://\S+',  # URLs
]


# ============================================================================
# Word Extraction
# ============================================================================


def _clean_content(content: str) -> str:
    """Remove Discord-specific patterns from content."""
    text = content
    for pattern in DISCORD_PATTERNS:
        text = re.sub(pattern, '', text)
    return text


def _extract_words(content: str, min_length: int = 3) -> list[str]:
    """Extract meaningful words from message content."""
    cleaned = _clean_content(content)

    # Extract words (letters and accented characters)
    words = re.findall(r'\b[a-zA-ZÀ-ÿ]+\b', cleaned.lower())

    # Filter stopwords and short words
    return [w for w in words if len(w) >= min_length and w not in STOPWORDS]


def _count_words(contents: list[str]) -> Counter[str]:
    """Count word frequencies across all messages."""
    counter: Counter[str] = Counter()
    for content in contents:
        words = _extract_words(content)
        counter.update(words)
    return counter


# ============================================================================
# Embed Builders
# ============================================================================


def build_top_words_embed(
    user_words: Counter[str],
    year: int,
) -> WrappedEmbed | None:
    """Build embed showing user's most used words."""
    if not user_words:
        return None

    top_10 = user_words.most_common(10)
    if not top_10:
        return None

    # Build word cloud-style display
    lines: list[str] = []
    for i, (word, count) in enumerate(top_10):
        lines.append(f'{MEDALS_EXTENDED[i]} **{word}** ({count:,})')

    description = 'Your most used words this year:\n\n' + '\n'.join(lines)

    return WrappedEmbed(
        title=f'💬 Your Vocabulary in {year}',
        description=description,
        color=COLOR_BLUE,
        footer=get_wrapped_footer(year),
    )


def build_characteristic_words_embed(
    user_words: Counter[str],
    community_words: Counter[str],
    user_msg_count: int,
    community_msg_count: int,
    year: int,
) -> WrappedEmbed | None:
    """Build embed showing words characteristic to the user.

    Uses TF-IDF-like scoring: words the user uses more than the community average.
    """
    if not user_words or not community_words:
        return None

    # Calculate word scores (user frequency / community frequency ratio)
    scores: list[tuple[str, float, int]] = []

    for word, user_count in user_words.items():
        if user_count < 3:  # Minimum usage threshold
            continue

        community_count = community_words.get(word, 0)

        # Calculate per-message frequencies
        user_freq = user_count / user_msg_count if user_msg_count > 0 else 0
        community_freq = (
            community_count / community_msg_count if community_msg_count > 0 else 0.0001
        )

        # Avoid division by zero
        if community_freq < 0.0001:
            community_freq = 0.0001

        ratio = user_freq / community_freq

        # Only include words with significant ratio (user uses it more)
        if ratio >= 2.0:
            # Score: log(ratio) * count to balance frequency and uniqueness
            score = math.log(ratio + 1) * user_count
            scores.append((word, score, user_count))

    if not scores:
        return None

    # Sort by score and take top 10
    scores.sort(key=lambda x: x[1], reverse=True)
    top_10 = scores[:10]

    lines: list[str] = []
    for i, (word, _score, count) in enumerate(top_10):
        emoji = '⭐' if i < 3 else '•'
        lines.append(f'{emoji} **{word}** ({count:,}×)')

    description = (
        'Words that define YOUR style:\n\n'
        + '\n'.join(lines)
        + '\n\n_These are words you use way more than others!_'
    )

    return WrappedEmbed(
        title=f'✨ Your Signature Words in {year}',
        description=description,
        color=COLOR_BLUE,
        footer=get_wrapped_footer(year),
    )


# ============================================================================
# Public API
# ============================================================================


async def get_words_stats_embeds(
    edgedb: AsyncIOClient,
    discord_id: str,
    year: int,
) -> list[WrappedEmbed]:
    """Fetch word statistics and build embeds for a user's wrapped."""
    year_start, year_end = get_year_bounds(year)

    # Fetch user and community messages in parallel
    async with asyncio.TaskGroup() as tg:
        user_task = tg.create_task(
            wrapped_get_user_words(
                edgedb,
                discord_id=discord_id,
                year_start=year_start,
                year_end=year_end,
            )
        )
        community_task = tg.create_task(
            wrapped_get_community_words(
                edgedb,
                discord_id=discord_id,
                year_start=year_start,
                year_end=year_end,
            )
        )

    user_result = user_task.result()
    community_result = community_task.result()

    user_contents = user_result.user_contents
    community_contents = community_result.community_contents

    if not user_contents:
        return []

    # Count words
    user_words = _count_words(user_contents)
    community_words = _count_words(community_contents)

    embeds: list[WrappedEmbed] = []

    # Top words embed
    top_embed = build_top_words_embed(user_words, year)
    if top_embed:
        embeds.append(top_embed)

    # Characteristic words embed
    char_embed = build_characteristic_words_embed(
        user_words,
        community_words,
        len(user_contents),
        len(community_contents),
        year,
    )
    if char_embed:
        embeds.append(char_embed)

    return embeds
