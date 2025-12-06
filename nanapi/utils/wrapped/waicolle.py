import asyncio
import re
from collections import Counter

from gel import AsyncIOClient

from nanapi.database.wrapped.wrapped_get_conditional_stats import (
    WrappedGetConditionalStatsResult,
    wrapped_get_conditional_stats,
)
from nanapi.database.wrapped.wrapped_get_daily_tag_stats import (
    WrappedGetDailyTagStatsResult,
    wrapped_get_daily_tag_stats,
)
from nanapi.database.wrapped.wrapped_get_drop_stats import (
    WrappedGetDropStatsResult,
    wrapped_get_drop_stats,
)
from nanapi.database.wrapped.wrapped_get_free_stats import (
    WrappedGetFreeStatsResult,
    wrapped_get_free_stats,
)
from nanapi.database.wrapped.wrapped_get_reroll_stats import (
    WrappedGetRerollStatsResult,
    wrapped_get_reroll_stats,
)
from nanapi.database.wrapped.wrapped_get_roll_stats import (
    WrappedGetRollStatsResult,
    wrapped_get_roll_stats,
)
from nanapi.database.wrapped.wrapped_get_trade_stats import (
    WrappedGetTradeStatsResult,
    wrapped_get_trade_stats,
)
from nanapi.database.wrapped.wrapped_get_wasabi_messages import (
    WrappedGetWasabiMessagesResult,
    wrapped_get_wasabi_messages,
)
from nanapi.database.wrapped.wrapped_get_wasabi_stats import (
    WrappedGetWasabiStatsResult,
    wrapped_get_wasabi_stats,
)
from nanapi.models.wrapped import WrappedEmbed
from nanapi.utils.wrapped.common import (
    COLOR_PURPLE,
    MEDALS,
    build_rank_distribution,
    format_bar_graph,
    format_rate_line,
    format_with_comment,
    get_wrapped_footer,
    get_year_bounds,
)

# ============================================================================
# Constants
# ============================================================================

# A-H paid roll options + daily (I) / weekly (J)
ROLL_OPTIONS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'daily', 'weekly']

# Display labels for roll options
ROLL_LABELS = {
    'A': 'A',
    'B': 'B',
    'C': 'C',
    'D': 'D',
    'E': 'E',
    'F': 'F',
    'G': 'G',
    'H': 'H',
    'daily': 'I',
    'weekly': 'J',
}

# Regex to parse daily tag from roll message content
# Example: "Rolling **1 S-E (all), Daily tag — Idol** for **75** ..."
DAILY_TAG_PATTERN = re.compile(r'Daily tag — (.+?)\*\*')

# Regex to parse wasabi result from message content
# Example: "<@USER_ID> [**Wasabi**] You received **1** character!"
WASABI_PATTERN = re.compile(r'\[\*\*Wasabi\*\*\] You received \*\*(\d+)\*\* characters?!')

# Regex to parse conditional drop result from message content
# Example: "<@USER_ID> [**Conditional drop: ...**] You received **1** character!"
CONDITIONAL_PATTERN = re.compile(
    r'\[\*\*Conditional drop:.*?\*\*\] You received \*\*(\d+)\*\* characters?!'
)


# ============================================================================
# Embed Builders
# ============================================================================


def build_drop_stats_embeds(
    stats: WrappedGetDropStatsResult,
    year: int,
) -> list[WrappedEmbed]:
    """Build embeds for random drop statistics."""
    if stats.total_drops == 0:
        return []

    # Use shared rank distribution builder
    _, dist_lines, sa_rate = build_rank_distribution(stats.ranks, get_value=lambda r: r.value)

    # Sarcastic comment based on luck
    # 2025 data: N=24, P10=13.6%, P25=16.7%, P50=18.6%, P75=21.7%, P90=24.4%
    if sa_rate >= 24:
        luck_comment = 'Golden banana collector! The jungle gods favor you. 🍌'
    elif sa_rate >= 22:
        luck_comment = 'Lucky monkey! Found some good bananas. 🐒'
    elif sa_rate >= 17:
        luck_comment = 'Average monkey luck. Keep climbing. 🌴'
    elif sa_rate >= 14:
        luck_comment = 'The banana tree was mostly empty for you. 🥀'
    else:
        luck_comment = 'Monkey see, monkey get nothing good. 💀'

    # Comment on number of drops
    # 2025 data: N=27, P10=6, P25=23, P50=72, P75=140, P90=170
    if stats.total_drops >= 170:
        drops_comment = 'Alpha monkey of the jungle! 🦍'
    elif stats.total_drops >= 140:
        drops_comment = 'Hardworking monkey! 🐒'
    elif stats.total_drops >= 23:
        drops_comment = ''  # Average, no comment
    elif stats.total_drops >= 6:
        drops_comment = 'Part-time monkey. 🙈'
    else:
        drops_comment = 'Sleepy monkey this year. 💤'

    drops_line = format_with_comment(
        f'You received **{stats.total_drops}** random drops!', drops_comment
    )

    description = (
        f'{drops_line}\n\n'
        f'### Rank Distribution\n'
        + '\n'.join(dist_lines)
        + f'\n\n📊 **S+A rate**: {sa_rate:.1f}%\n'
        + luck_comment
    )

    return [
        WrappedEmbed(
            title=f'🎲 Random Drops in {year}',
            description=description,
            color=COLOR_PURPLE,
            footer=get_wrapped_footer(year),
        )
    ]


def build_roll_stats_embeds(
    stats: WrappedGetRollStatsResult,
    year: int,
) -> list[WrappedEmbed]:
    """Build embeds for paid roll statistics with bar chart."""
    if stats.total_rolls == 0:
        return []

    # Count rolls by option
    option_counts = Counter(stats.reasons)

    # Build data for bar graph (all options, including zeros)
    data = [(ROLL_LABELS[opt], option_counts.get(opt, 0)) for opt in ROLL_OPTIONS]
    max_count = max(count for _, count in data) if data else 1

    bar_graph = format_bar_graph(data, max_count)

    # Format moecoins with thousands separator
    moecoins_str = f'{stats.total_moecoins:,}'.replace(',', ' ')

    # Comment on moecoins spent
    # 2025 data: N=28, P10=600, P25=3975, P50=10425, P75=18819, P90=23325
    if stats.total_moecoins >= 23000:
        moecoins_comment = 'Whale monkey! 🐋'
    elif stats.total_moecoins >= 18000:
        moecoins_comment = 'Big spender! 💸'
    elif stats.total_moecoins >= 4000:
        moecoins_comment = ''  # Average, no comment
    elif stats.total_moecoins >= 600:
        moecoins_comment = 'Frugal monkey. 🐒'
    else:
        moecoins_comment = 'Saving those bananas! 🍌'

    moecoins_line = format_with_comment(f'💰 Spent **{moecoins_str}** moecoins', moecoins_comment)

    description = (
        f'You did **{stats.total_rolls}** paid rolls!\n'
        f'🎁 Received **{stats.total_waifus}** waifus\n'
        f'{moecoins_line}\n\n'
        f'### Roll Options\n' + bar_graph
    )

    return [
        WrappedEmbed(
            title=f'🎯 Paid Rolls in {year}',
            description=description,
            color=COLOR_PURPLE,
            footer=get_wrapped_footer(year),
        )
    ]


def build_daily_tag_stats_embeds(
    stats: WrappedGetDailyTagStatsResult,
    year: int,
) -> list[WrappedEmbed]:
    """Build embeds for daily tag roll statistics."""
    if stats.total_rolls == 0:
        return []

    # Parse tags from message content
    tags: list[str] = []
    for content in stats.contents:
        match = DAILY_TAG_PATTERN.search(content)
        if match:
            tags.append(match.group(1))

    if not tags:
        return []

    # Get most common tags
    tag_counts = Counter(tags)
    top_tags = tag_counts.most_common(5)

    # Build top tags list
    tag_lines: list[str] = []
    for i, (tag, count) in enumerate(top_tags):
        tag_lines.append(f'{MEDALS[i]} **{tag}** ({count})')

    description = (
        f'You rolled daily tags **{stats.total_rolls}** times!\n\n'
        f'### Your favorite tags\n' + '\n'.join(tag_lines)
    )

    return [
        WrappedEmbed(
            title=f'🏷️ Daily Tags in {year}',
            description=description,
            color=COLOR_PURPLE,
            footer=get_wrapped_footer(year),
        )
    ]


def build_wasabi_stats_embeds(
    messages: WrappedGetWasabiMessagesResult,
    rolls: WrappedGetWasabiStatsResult,
    year: int,
) -> list[WrappedEmbed]:
    """Build embeds for wasabi statistics."""
    if messages.total_wasabi == 0:
        return []

    # Parse success count from message content
    success_count = 0
    for content in messages.contents:
        match = WASABI_PATTERN.search(content)
        if match:
            chars = int(match.group(1))
            if chars > 0:
                success_count += 1

    # Calculate success rate
    success_rate = (
        (success_count / messages.total_wasabi * 100) if messages.total_wasabi > 0 else 0
    )

    # Use shared rank distribution builder
    rank_counts, dist_lines, sa_rate = build_rank_distribution(
        rolls.ranks, get_value=lambda r: r.value
    )
    total_chars = sum(rank_counts.values())

    # Comment on success rate
    # 2025 data: N=25, P10=33%, P25=40%, P50=46%, P75=58%, P90=72%
    if success_rate >= 72:
        rate_comment = 'Wasabi master! 🥷'
    elif success_rate >= 58:
        rate_comment = 'Hot streak! 🔥'
    elif success_rate >= 40:
        rate_comment = ''  # Average, no comment
    elif success_rate >= 33:
        rate_comment = 'The wasabi gods are not with you. 🥀'
    else:
        rate_comment = 'Maybe try touching grass? 🌿'

    # Comment on wasabi count
    # 2025 data: N=27, P10=3, P25=5, P50=11, P75=27, P90=37
    if messages.total_wasabi >= 37:
        count_comment = 'Wasabi addict! 🌶️'
    elif messages.total_wasabi >= 27:
        count_comment = 'Spicy monkey! 🐒'
    elif messages.total_wasabi >= 5:
        count_comment = ''  # Average, no comment
    elif messages.total_wasabi >= 3:
        count_comment = 'Casual wasabi enjoyer. 😌'
    else:
        count_comment = 'One-time wasabi taster. 👀'

    wasabi_line = format_with_comment(
        f'You received wasabi **{messages.total_wasabi}** times!', count_comment
    )
    rate_line = format_rate_line(
        'Success rate', success_rate, success_count, messages.total_wasabi, rate_comment
    )

    description = (
        f'{wasabi_line}\n'
        f'🎁 Received **{total_chars}** characters\n'
        f'{rate_line}\n\n'
        f'### Rank Distribution\n' + '\n'.join(dist_lines) + f'\n\n📊 **S+A rate**: {sa_rate:.1f}%'
    )

    return [
        WrappedEmbed(
            title=f'🌶️ Wasabi in {year}',
            description=description,
            color=COLOR_PURPLE,
            footer=get_wrapped_footer(year),
        )
    ]


def build_reroll_stats_embeds(
    stats: WrappedGetRerollStatsResult,
    year: int,
) -> list[WrappedEmbed]:
    """Build embeds for reroll statistics."""
    if stats.total_rerolls == 0:
        return []

    # Calculate single reroll success rate
    single_rate = (
        (stats.single_success / stats.single_rerolls * 100) if stats.single_rerolls > 0 else 0
    )

    # Comment on reroll count
    # 2025 data: N=20, P10=2, P25=6, P50=17, P75=59, P90=193
    if stats.total_rerolls >= 193:
        count_comment = 'Reroll addict! 🎰'
    elif stats.total_rerolls >= 59:
        count_comment = 'Active reroller! 🔄'
    elif stats.total_rerolls >= 6:
        count_comment = ''  # Average, no comment
    else:
        count_comment = 'Keeping your waifus. 🥰'

    reroll_line = format_with_comment(f'You did **{stats.total_rerolls}** rerolls!', count_comment)

    description = (
        f'{reroll_line}\n'
        f'🗑️ Sacrificed **{stats.total_rerolled}** waifus\n'
        f'🎁 Received **{stats.total_received}** new waifus\n'
    )

    # Add single reroll stats if any
    if stats.single_rerolls > 0:
        # Comment on single reroll success rate
        # 2025 data: single reroll stats not directly available, using general distribution
        if single_rate >= 70:
            rate_comment = 'Lucky monkey! 🍀'
        elif single_rate >= 35:
            rate_comment = ''
        elif single_rate >= 20:
            rate_comment = 'Unlucky... 😢'
        else:
            rate_comment = 'The gacha hates you. 💀'

        rate_line = format_rate_line(
            'Single reroll luck',
            single_rate,
            stats.single_success,
            stats.single_rerolls,
            rate_comment,
        )
        description += f'\n{rate_line}'

    return [
        WrappedEmbed(
            title=f'🔄 Rerolls in {year}',
            description=description,
            color=COLOR_PURPLE,
            footer=get_wrapped_footer(year),
        )
    ]


def build_trade_stats_embeds(
    stats: WrappedGetTradeStatsResult,
    year: int,
) -> list[WrappedEmbed]:
    """Build embeds for trade statistics."""
    if stats.total_trades == 0:
        return []

    # Calculate balance
    balance = stats.total_offered - stats.total_received

    # Comment on trade count
    # 2025 data: N=50, P10=1, P25=2, P50=24, P75=122, P90=385
    if stats.total_trades >= 385:
        count_comment = 'Trade machine! 🏭'
    elif stats.total_trades >= 122:
        count_comment = 'Active trader! 🤝'
    elif stats.total_trades >= 2:
        count_comment = ''
    else:
        count_comment = 'Lonely trader. 😢'

    trade_line = format_with_comment(f'You made **{stats.total_trades}** trades!', count_comment)

    # Balance comment
    if balance > 10:
        balance_comment = 'Generous monkey! 🍌'
    elif balance < -10:
        balance_comment = 'You rat! 🐀'
    else:
        balance_comment = 'Balanced, as all things should be. ⚖️'

    description = (
        f'{trade_line}\n'
        f'📤 Offered **{stats.total_offered}** waifus\n'
        f'📥 Received **{stats.total_received}** waifus\n'
        f'💹 **Balance**: {balance:+d} {balance_comment}\n'
    )

    # Top 5 BFFs
    all_partners = stats.partners_as_author + stats.partners_as_offeree
    if all_partners:
        top_partners = Counter(all_partners).most_common(5)
        bff_lines = ['### Your BFFs']
        for i, (partner_id, count) in enumerate(top_partners):
            bff_lines.append(f'{MEDALS[i]} <@{partner_id}> ({count} trades)')
        description += '\n' + '\n'.join(bff_lines)

    return [
        WrappedEmbed(
            title=f'🤝 Trades in {year}',
            description=description,
            color=COLOR_PURPLE,
            footer=get_wrapped_footer(year),
        )
    ]


def build_conditional_stats_embeds(
    stats: WrappedGetConditionalStatsResult,
    year: int,
) -> list[WrappedEmbed]:
    """Build embeds for conditional drop statistics."""
    if stats.total == 0:
        return []

    # Parse success count from message content
    success_count = 0
    for content in stats.contents:
        match = CONDITIONAL_PATTERN.search(content)
        if match:
            chars = int(match.group(1))
            if chars > 0:
                success_count += 1

    # Calculate success rate
    success_rate = (success_count / stats.total * 100) if stats.total > 0 else 0

    # Comment on count
    # 2025 data: N=27, P10=2, P25=6, P50=14, P75=34, P90=54
    if stats.total >= 54:
        count_comment = 'Active chatter! 💬'
    elif stats.total >= 34:
        count_comment = 'Conditional enjoyer! 🎉'
    elif stats.total >= 6:
        count_comment = ''  # Average, no comment
    else:
        count_comment = 'Quiet monkey. 🙊'

    drop_line = format_with_comment(f'You received **{stats.total}** conditionals!', count_comment)

    # Comment on success rate
    # 2025 data: N=24, P10=85%, P25=93%, P50=97%, P75=100%, P90=100%
    if success_rate >= 100:
        rate_comment = 'Perfect! 🎯'
    elif success_rate >= 97:
        rate_comment = 'Almost perfect! ✨'
    elif success_rate >= 93:
        rate_comment = ''  # Average, no comment
    elif success_rate >= 85:
        rate_comment = 'A few misses... 😢'
    else:
        rate_comment = 'Damn it. 💀'

    rate_line = format_rate_line(
        'Success rate', success_rate, success_count, stats.total, rate_comment
    )

    description = f'{drop_line}\n{rate_line}'

    return [
        WrappedEmbed(
            title=f'🎲 Conditional Drops in {year}',
            description=description,
            color=COLOR_PURPLE,
            footer=get_wrapped_footer(year),
        )
    ]


def build_free_stats_embeds(
    stats: WrappedGetFreeStatsResult,
    year: int,
) -> list[WrappedEmbed]:
    """Build embeds for free drops (events + coupons) statistics."""
    total_rolls = stats.event_count + stats.coupon_count
    if total_rolls == 0:
        return []

    # Use shared rank distribution builder
    rank_counts, dist_lines, sa_rate = build_rank_distribution(
        stats.ranks, get_value=lambda r: r.value
    )
    total_chars = sum(rank_counts.values())

    # Comment on total free drops
    # 2025 data: N=34, P10=1, P25=2, P50=10, P75=18, P90=45
    if total_rolls >= 45:
        count_comment = 'Event hunter! 🎯'
    elif total_rolls >= 18:
        count_comment = 'Active participant! 🎉'
    elif total_rolls >= 2:
        count_comment = ''  # Average, no comment
    else:
        count_comment = 'Missed some free stuff. 😢'

    free_line = format_with_comment(f'You claimed **{total_rolls}** free drops!', count_comment)

    description = (
        f'{free_line}\n'
        f'🎪 **{stats.event_count}** from events\n'
        f'🎟️ **{stats.coupon_count}** from coupons\n'
        f'🎁 Received **{total_chars}** characters\n\n'
        f'### Rank Distribution\n' + '\n'.join(dist_lines) + f'\n\n📊 **S+A rate**: {sa_rate:.1f}%'
    )

    return [
        WrappedEmbed(
            title=f'🎁 Free Drops in {year}',
            description=description,
            color=COLOR_PURPLE,
            footer=get_wrapped_footer(year),
        )
    ]


# ============================================================================
# Public API
# ============================================================================


async def get_waicolle_stats_embeds(
    edgedb: AsyncIOClient,
    discord_id: str,
    year: int,
) -> list[WrappedEmbed]:
    """Fetch waicolle stats from database and build embeds for a user's yearly wrapped."""
    year_start, year_end = get_year_bounds(year)

    # Fetch all stats in parallel
    async with asyncio.TaskGroup() as tg:
        drop_task = tg.create_task(
            wrapped_get_drop_stats(
                edgedb, discord_id=discord_id, year_start=year_start, year_end=year_end
            )
        )
        roll_task = tg.create_task(
            wrapped_get_roll_stats(
                edgedb, discord_id=discord_id, year_start=year_start, year_end=year_end
            )
        )
        daily_tag_task = tg.create_task(
            wrapped_get_daily_tag_stats(
                edgedb, discord_id=discord_id, year_start=year_start, year_end=year_end
            )
        )
        wasabi_messages_task = tg.create_task(
            wrapped_get_wasabi_messages(
                edgedb, discord_id=discord_id, year_start=year_start, year_end=year_end
            )
        )
        wasabi_rolls_task = tg.create_task(
            wrapped_get_wasabi_stats(
                edgedb, discord_id=discord_id, year_start=year_start, year_end=year_end
            )
        )
        free_task = tg.create_task(
            wrapped_get_free_stats(
                edgedb, discord_id=discord_id, year_start=year_start, year_end=year_end
            )
        )
        reroll_task = tg.create_task(
            wrapped_get_reroll_stats(
                edgedb, discord_id=discord_id, year_start=year_start, year_end=year_end
            )
        )
        trade_task = tg.create_task(
            wrapped_get_trade_stats(
                edgedb, discord_id=discord_id, year_start=year_start, year_end=year_end
            )
        )
        conditional_task = tg.create_task(
            wrapped_get_conditional_stats(
                edgedb, discord_id=discord_id, year_start=year_start, year_end=year_end
            )
        )

    # Build embeds in order
    embeds: list[WrappedEmbed] = []
    embeds.extend(build_drop_stats_embeds(drop_task.result(), year))
    embeds.extend(build_free_stats_embeds(free_task.result(), year))
    embeds.extend(
        build_wasabi_stats_embeds(wasabi_messages_task.result(), wasabi_rolls_task.result(), year)
    )
    embeds.extend(build_roll_stats_embeds(roll_task.result(), year))
    embeds.extend(build_daily_tag_stats_embeds(daily_tag_task.result(), year))
    embeds.extend(build_reroll_stats_embeds(reroll_task.result(), year))
    embeds.extend(build_trade_stats_embeds(trade_task.result(), year))
    embeds.extend(build_conditional_stats_embeds(conditional_task.result(), year))

    return embeds
