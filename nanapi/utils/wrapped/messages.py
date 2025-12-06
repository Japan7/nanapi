import asyncio
from datetime import datetime, timedelta

from gel import AsyncIOClient

from nanapi.database.wrapped.wrapped_get_message_stats import (
    WrappedGetMessageStatsResult,
    wrapped_get_message_stats,
)
from nanapi.database.wrapped.wrapped_get_night_silence_stats import (
    WrappedGetNightSilenceStatsResult,
    wrapped_get_night_silence_stats,
)
from nanapi.models.wrapped import WrappedEmbed, WrappedEmbedField
from nanapi.utils.wrapped.common import (
    COLOR_BLURPLE,
    format_bar_graph,
    get_hours_in_year,
    get_medal,
    get_timezone_name,
    get_wrapped_footer,
    get_year_bounds,
    pick_template,
)

###############################################################################
# Constants
###############################################################################

# Weekday names (EdgeDB dow: 0=Sunday, 1=Monday, ...)
WEEKDAY_NAMES = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
WEEKDAY_SHORT = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

# Message count thresholds based on 2025 distribution analysis (excluding bot messages)
# N=110, P10=1, P25=1, P50=8, P75=1053, P90=7620
MSG_THRESHOLD_LOW = 8  # ~P50
MSG_THRESHOLD_MODERATE = 1053  # ~P75
MSG_THRESHOLD_VERY_HIGH = 7620  # ~P90

# Height comparisons for paper-stacked messages (count * 0.1mm)
HEIGHT_COMPARISONS = [
    (1000, 'a 2-liter bottle of soda'),  # 10k messages
    (1200, 'a small cat (curled up)'),  # 12k messages
    (1500, 'a golden retriever'),  # 15k messages
    (1700, 'Danny DeVito'),  # 17k messages
    (2000, "Shaquille O'Neal"),  # 20k messages
]

###############################################################################
# Sarcastic comment templates
###############################################################################

TEMPLATES_LURKER = [
    (
        'You sent exactly **0 messages**. A digital ghost. '
        'The server forgot you existed. :OkayuSad:'
    ),
    '**Zero. Zilch. Nada.** You were so quiet, Discord thought you were a bug. :oof:',
    (
        "You didn't send a single message. Somewhere, "
        'an extrovert is having a panic attack on your behalf. :pepeLoser:'
    ),
]

TEMPLATES_LOW = [
    'Only **{count}** messages? You type like you pay per character. :YuiShrug:',
    (
        '**{count}** messages. Even my grandma texts more than you, '
        'and she thinks "LOL" means "Lots Of Love". :Kek:'
    ),
    (
        "**{count}** messages this year. That's one message every **{days_per_msg:.0f}** days. "
        'Are you okay? Blink twice if you need help. :OkayuSad:'
    ),
]

TEMPLATES_MODERATE = [
    (
        '**{count}** messages. If each one was a raindrop, '
        'you would have made a small puddle. Underwhelming, but wet. :think:'
    ),
    (
        'You sent **{count}** messages — roughly **{tweets:.0f}** tweets worth. '
        'Except yours probably had more than 3 brain cells behind them. :mitosmug:'
    ),
    (
        '**{count}** messages = approximately **{seconds:.0f}** seconds of typing. '
        "You could've learned to juggle instead. But you didn't. :YuiShrug:"
    ),
]

TEMPLATES_HIGH = [
    (
        '**{count}** messages. If printed, that would be about '
        '**{pages:.0f}** pages of pure, unfiltered you. :oof:'
    ),
    (
        'You typed **{count}** messages this year. '
        "That's **{hours:.1f}** hours of typing. You could've binged an anime instead. :hype:"
    ),
    "**{count}** messages sent. Your keyboard's spacebar probably needs therapy. :NanaDed:",
    "**{count}** messages. You're basically writing a novel, but make it chaotic. :FubukiGO:",
]

TEMPLATES_VERY_HIGH = [
    (
        '**{count}** messages. Stacked as paper, that is **{height_mm:.0f}mm** tall — '
        'roughly the height of **{height_comparison}**. '
        'Touch grass? Never heard of it. :Jeanjean:'
    ),
    (
        "You've sent more messages than there are stars visible from Tokyo on a clear night "
        '(**{count}** vs ~2,500). Impressive... or concerning? :NotLikeHikari:'
    ),
    (
        '**{count}** messages = roughly **{co2:.1f}kg** of CO₂ from server energy. '
        'The planet thanks you. (It does not.) :oof:'
    ),
    (
        "**{count}** messages. That's **{per_day:.1f}** messages per day. "
        'Do you even sleep? :peepoShake:'
    ),
]

# Threshold-to-template mapping (ascending order)
MSG_COUNT_TEMPLATES = [
    (1, TEMPLATES_LURKER),
    (MSG_THRESHOLD_LOW, TEMPLATES_LOW),
    (MSG_THRESHOLD_MODERATE, TEMPLATES_MODERATE),
    (MSG_THRESHOLD_VERY_HIGH, TEMPLATES_HIGH),
]

# Peak hour comments by time range (hour < threshold)
COMMENTS_PEAK_HOUR = [
    (6, 'Sleep issues? 🌙'),
    (9, 'Early bird, respect. ☀️'),
    (12, 'Spamming during work hours, clever. 🏢'),
    (14, 'Lunch break = Discord break. Classic. 🍔'),
    (18, 'Productive afternoon (not). 💼'),
    (22, 'Prime time Discord, you are normal. 📺'),
    (24, 'Night owl vibes. 🦉'),
]

# Peak weekday comments (0=Sunday, 1=Monday, ..., 6=Saturday)
COMMENTS_PEAK_WEEKDAY = [
    'Sunday warrior. No rest for the weary. 🛋️',
    'Monday? Really? Some people dread it, you embrace it. 💼',
    'Tuesday, the forgotten day. You gave it purpose. 📅',
    'Hump day hero. 🐫',
    'Thursday enjoyer. Almost Friday energy. ⚡',
    'TGIF spammer. Weekend vibes incoming. 🎉',
    'Saturday superstar. Touch grass? Never heard of it. 🌿',
]


###############################################################################
# Helper functions
###############################################################################


def _format_duration(seconds: float) -> str:
    """Format seconds as a human-readable duration string."""
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)

    if days > 0:
        return f'{days}d {hours}h {minutes}m'
    elif hours > 0:
        return f'{hours}h {minutes}m'
    else:
        return f'{minutes}m'


def _get_height_comparison(height_mm: float) -> str:
    """Get a funny comparison for a height in mm."""
    for threshold, comparison in HEIGHT_COMPARISONS:
        if height_mm <= threshold:
            return comparison
    return "the Eiffel Tower's younger, sadder cousin"


def _get_comment_for_peak_hour(hour: int) -> str:
    """Get a sarcastic comment based on peak activity hour."""
    for threshold, comment in COMMENTS_PEAK_HOUR:
        if hour < threshold:
            return comment
    return COMMENTS_PEAK_HOUR[-1][1]


###############################################################################
# Embed builder functions (in order of appearance)
###############################################################################


def _build_message_count_embed(
    stats: WrappedGetMessageStatsResult,
    year: int,
    days_in_year: int,
) -> WrappedEmbed:
    """Build the main embed showing total message count with sarcastic commentary."""
    count = stats.total_count
    template = pick_template(count, MSG_COUNT_TEMPLATES, TEMPLATES_VERY_HIGH)
    height_mm = count * 0.1

    description = template.format(
        count=count,
        days_per_msg=days_in_year / max(count, 1),
        tweets=count / 3,
        seconds=count * 5,
        pages=count * 10 / 250,
        hours=count * 5 / 3600,
        words=count * 10,
        height_mm=height_mm,
        height_comparison=_get_height_comparison(height_mm),
        co2=count * 0.0002,
        per_day=count / days_in_year,
    )

    return WrappedEmbed(
        title=f'📜 Messages Sent in {year}',
        description=description,
        color=COLOR_BLURPLE,
        footer=get_wrapped_footer(year),
    )


def _build_message_details_fields(
    stats: WrappedGetMessageStatsResult,
    hours_in_year: int,
) -> list[WrappedEmbedField]:
    """Build fields with detailed message statistics (words, length, attachments, etc.)."""
    fields: list[WrappedEmbedField] = []

    # Total words
    if stats.total_words > 0:
        fields.append(
            WrappedEmbedField(
                name='📝 Total Words',
                value=f'**{stats.total_words:,}** words written',
                inline=False,
            )
        )

    # Average message length
    if stats.total_count > 0:
        avg_length = stats.total_length / stats.total_count
        length_comment = (
            'You talk in SMS.'
            if avg_length < 20
            else 'Concise and efficient.'
            if avg_length < 50
            else 'You like writing.'
            if avg_length < 100
            else 'You write walls of text. 📜'
        )
        fields.append(
            WrappedEmbedField(
                name='📏 Avg Length',
                value=f'**{avg_length:.1f}** characters\n{length_comment}',
                inline=False,
            )
        )

    # Average messages per hour (across all hours of the year)
    if stats.total_count > 0 and hours_in_year > 0:
        avg_per_hour = stats.total_count / hours_in_year
        hour_comment = (
            'A rare occurrence.'
            if avg_per_hour < 0.5
            else 'Casual user.'
            if avg_per_hour < 2
            else 'Quite active.'
            if avg_per_hour < 5
            else 'You never shut up. 🗣️'
        )
        fields.append(
            WrappedEmbedField(
                name='💬 Avg/Hour',
                value=f'**{avg_per_hour:.2f}** msgs/hour\n{hour_comment}',
                inline=False,
            )
        )

    # Attachments (images, files, etc.)
    if stats.attachment_count > 0:
        attachment_rate = stats.attachment_count / stats.total_count * 100
        fields.append(
            WrappedEmbedField(
                name='📎 Attachments',
                value=f'**{stats.attachment_count}** files ({attachment_rate:.1f}%)',
                inline=False,
            )
        )

    # Mentions
    if stats.mention_count > 0:
        mention_rate = stats.mention_count / stats.total_count * 100
        comment = 'You ping a lot.' if mention_rate > 20 else ''
        fields.append(
            WrappedEmbedField(
                name='👥 Mentions',
                value=f'**{stats.mention_count}** mentions{" - " + comment if comment else ""}',
                inline=False,
            )
        )

    # @everyone abuse
    if stats.everyone_count > 0:
        comment = (
            'A true terrorist.'
            if stats.everyone_count > 10
            else 'You love attention.'
            if stats.everyone_count > 3
            else 'Was it important?'
        )
        fields.append(
            WrappedEmbedField(
                name='🚨 @everyone',
                value=f'**{stats.everyone_count}** times\n{comment}',
                inline=False,
            )
        )

    return fields


# Month names (1=January, ..., 12=December)
MONTH_NAMES = [
    'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
]

# Peak month comments
COMMENTS_PEAK_MONTH = [
    'January warrior. New year, same Discord addiction. 🎊',
    'February peak? Valentine energy or just lonely? 💔',
    'March madness. Spring cleaning your social life. 🌸',
    'April showers bring... more Discord messages. 🌧️',
    'May flowers and keyboard warriors. 🌺',
    'June peak. Summer break = Discord grind. ☀️',
    'July heat got you staying indoors on Discord. 🏖️',
    'August peak. Touching grass? In this heat? 🥵',
    'September back-to-school energy. Procrastinating already. 📚',
    'October spooky season. Scary how much you type. 🎃',
    'November thanks for the messages. Turkey-induced typing. 🦃',
    'December holiday chaos. Family drama = Discord vent. 🎄',
]


def _build_peak_months_embed(
    stats: WrappedGetMessageStatsResult,
    year: int,
) -> WrappedEmbed | None:
    """Build an embed with a bar graph of activity by month."""
    if not stats.month_distribution:
        return None

    # Build lookup dict from month -> count
    month_counts = {m.month: m.count for m in stats.month_distribution}

    # Fill in all 12 months (EdgeDB month: 1=January, ..., 12=December)
    data = [(MONTH_NAMES[m - 1], month_counts.get(m, 0)) for m in range(1, 13)]
    max_count = max(count for _, count in data)

    if max_count == 0:
        return None

    peak_month = max(range(1, 13), key=lambda m: month_counts.get(m, 0))
    bar_graph = format_bar_graph(data, max_count)
    comment = COMMENTS_PEAK_MONTH[peak_month - 1]

    return WrappedEmbed(
        title=f'📆 Peak Months in {year}',
        description=f'### Activity by Month\n{bar_graph}\n\n{comment}',
        color=COLOR_BLURPLE,
        footer=get_wrapped_footer(year),
    )


def _build_peak_weekdays_embed(
    stats: WrappedGetMessageStatsResult,
    year: int,
) -> WrappedEmbed | None:
    """Build an embed with a bar graph of activity by weekday."""
    if not stats.weekday_distribution:
        return None

    # Build lookup dict from weekday -> count
    weekday_counts = {w.weekday: w.count for w in stats.weekday_distribution}

    # Fill in all 7 weekdays (EdgeDB dow: 0=Sunday, 1=Monday, ..., 6=Saturday)
    data = [(WEEKDAY_SHORT[d], weekday_counts.get(d, 0)) for d in range(7)]
    max_count = max(count for _, count in data)

    if max_count == 0:
        return None

    peak_weekday = max(range(7), key=lambda d: weekday_counts.get(d, 0))
    bar_graph = format_bar_graph(data, max_count)
    comment = COMMENTS_PEAK_WEEKDAY[peak_weekday]

    return WrappedEmbed(
        title=f'📅 Peak Weekdays in {year}',
        description=f'### Activity by Weekday\n{bar_graph}\n\n{comment}',
        color=COLOR_BLURPLE,
        footer=get_wrapped_footer(year),
    )


def _build_peak_hours_embed(
    stats: WrappedGetMessageStatsResult,
    year: int,
) -> WrappedEmbed | None:
    """Build an embed with a bar graph of activity by hour of day."""
    if not stats.hour_distribution:
        return None

    # Build lookup dict from hour -> count
    hour_counts = {h.hour: h.count for h in stats.hour_distribution}

    # Fill in all 24 hours
    data = [(f'{h:02d}', hour_counts.get(h, 0)) for h in range(24)]
    max_count = max(count for _, count in data)

    if max_count == 0:
        return None

    peak_hour = max(range(24), key=lambda h: hour_counts.get(h, 0))
    bar_graph = format_bar_graph(data, max_count)
    comment = _get_comment_for_peak_hour(peak_hour)

    return WrappedEmbed(
        title=f'⏰ Peak Hours in {year}',
        description=f'### Activity by Hour\n{bar_graph}\n\n{comment}',
        color=COLOR_BLURPLE,
        footer=get_wrapped_footer(year),
    )


def _build_peak_days_embed(
    stats: WrappedGetMessageStatsResult,
    year: int,
) -> WrappedEmbed | None:
    """Build an embed showing the top 5 most active days."""
    if not stats.day_distribution:
        return None

    top_days = sorted(stats.day_distribution, key=lambda d: d.count, reverse=True)[:5]
    if not top_days or top_days[0].count == 0:
        return None

    year_start = datetime(year, 1, 1)
    lines: list[str] = []
    for i, day in enumerate(top_days):
        medal = get_medal(i)
        peak_date = year_start + timedelta(days=day.day - 1)
        date_str = peak_date.strftime('%b %d')
        lines.append(f'{medal} **{date_str}** — {day.count:,} msgs')

    return WrappedEmbed(
        title=f'🌟 Peak Days in {year}',
        description='Your most active days:\n\n' + '\n'.join(lines),
        color=COLOR_BLURPLE,
        footer=get_wrapped_footer(year),
    )


def _build_top_channels_embed(
    stats: WrappedGetMessageStatsResult,
    year: int,
) -> WrappedEmbed | None:
    """Build an embed showing the top 5 most active channels."""
    if not stats.channel_distribution:
        return None

    lines: list[str] = []
    for i, channel in enumerate(stats.channel_distribution):
        medal = get_medal(i)
        # Format channel as Discord channel mention
        lines.append(f'{medal} <#{channel.channel_id}> — **{channel.count:,}** msgs')

    return WrappedEmbed(
        title=f'📢 Top Channels in {year}',
        description='Where you spent most of your time:\n\n' + '\n'.join(lines),
        color=COLOR_BLURPLE,
        footer=get_wrapped_footer(year),
    )


def _build_longest_silence_embed(
    stats: WrappedGetMessageStatsResult,
    year: int,
) -> WrappedEmbed | None:
    """Build an embed showing the longest period without messages."""
    if stats.longest_silence_seconds is None or stats.longest_silence_start is None:
        return None

    seconds = stats.longest_silence_seconds
    duration_str = _format_duration(seconds)

    # Convert UTC to local timezone for display
    from nanapi.settings import TZ

    start_local = stats.longest_silence_start.astimezone(TZ)
    end_local = start_local + timedelta(seconds=seconds)
    start_str = start_local.strftime('%b %d, %H:%M')
    end_str = end_local.strftime('%b %d, %H:%M')

    days = seconds // 86400
    comment = (
        'Did you go outside? Touching grass confirmed. 🌳'
        if days >= 7
        else 'Vacation mode activated. 🏖️'
        if days >= 3
        else 'A rare break from the screen. 😌'
        if days >= 1
        else 'You barely took a breath. Impressive dedication. 💪'
    )

    return WrappedEmbed(
        title=f'🤫 Longest Silence in {year}',
        description=f'**{duration_str}** of peace and quiet.\n\n'
        f'From {start_str} to {end_str}\n\n{comment}',
        color=COLOR_BLURPLE,
        footer=get_wrapped_footer(year),
    )


def _format_hour_minute(decimal_hour: float) -> str:
    """Format a decimal hour (e.g., 20.75) as HH:MM."""
    hours = int(decimal_hour)
    minutes = int((decimal_hour - hours) * 60)
    return f'{hours:02d}:{minutes:02d}'


def build_night_silence_embed(
    stats: WrappedGetNightSilenceStatsResult,
    year: int,
) -> WrappedEmbed | None:
    """Build an embed showing average night silence statistics."""
    # Need at least 10 nights of data for meaningful stats
    if stats.night_count < 10:
        return None

    avg_hours = stats.avg_night_silence_seconds / 3600
    last_msg_time = _format_hour_minute(stats.avg_last_msg_hour)
    first_msg_time = _format_hour_minute(stats.avg_first_msg_hour)

    # Sarcastic comments based on sleep duration
    # 2025 data: avg_first_msg_hour P10=4.9, P25=7.0, P50=9.5, P75=13.4, P90=14.6
    # 2025 data: avg_last_msg_hour P10=15.8, P25=17.4, P50=18.7, P75=20.9, P90=21.8
    if avg_hours < 7:
        comment = "You're barely sleeping. Red Bull sponsor when? 🥫"
    elif avg_hours < 9:
        comment = 'Not great, not terrible. Your under-eye bags disagree. 😴'
    elif avg_hours < 11:
        comment = 'A reasonable break. Your body thanks you. 🌙'
    elif avg_hours < 13:
        comment = 'Average Discord break. Nothing special. 💤'
    elif avg_hours < 15:
        comment = 'Long breaks? You might have a life outside Discord. Suspicious. 🤔'
    else:
        comment = 'You disappear for half the day. Touching grass confirmed. 🌳'

    # Comment on last message time
    # 2025 data: avg_last_msg_hour P10=15.8, P25=17.4, P50=18.7, P75=20.9, P90=21.8
    if stats.avg_last_msg_hour >= 0 and stats.avg_last_msg_hour < 4:
        last_comment = 'Night owl? More like insomniac. 🦉'
    elif stats.avg_last_msg_hour >= 21.8 or stats.avg_last_msg_hour < 0:
        last_comment = 'Late night lurker. The night is your kingdom. 🌑'
    elif stats.avg_last_msg_hour >= 18.7:
        last_comment = 'Average bedtime. You blend in with the crowd. 🌃'
    elif stats.avg_last_msg_hour >= 17.4:
        last_comment = 'Early to bed? Grandma energy. 👵'
    else:
        last_comment = 'You clock out before dinner? Respect the boundaries. 🍽️'

    # Comment on first message time
    # 2025 data: avg_first_msg_hour P10=4.9, P25=7.0, P50=9.5, P75=13.4, P90=14.6
    if stats.avg_first_msg_hour < 4.9:
        first_comment = "You don't sleep, do you? ☀️"
    elif stats.avg_first_msg_hour < 7.0:
        first_comment = 'Early bird gets the... Discord notifications. 🐦'
    elif stats.avg_first_msg_hour < 9.5:
        first_comment = 'A normal wake-up time. Boring but healthy. 🌅'
    elif stats.avg_first_msg_hour < 13.4:
        first_comment = 'Late morning energy. Remote worker detected. 💻'
    else:
        first_comment = 'You wake up after noon? Respect the grind. 😎'

    description = (
        f'Based on **{stats.night_count}** nights of data:\n\n'
        f'🛏️ **Average break**: {avg_hours:.1f} hours\n'
        f'{comment}\n\n'
        f'🌙 **Avg last message**: {last_msg_time}\n'
        f'{last_comment}\n\n'
        f'☀️ **Avg first message**: {first_msg_time}\n'
        f'{first_comment}'
    )

    return WrappedEmbed(
        title=f'😴 Sleep Schedule in {year}',
        description=description,
        color=COLOR_BLURPLE,
        footer=get_wrapped_footer(year),
    )


###############################################################################
# Public API
###############################################################################


def build_message_stats_embeds(
    stats: WrappedGetMessageStatsResult,
    year: int,
) -> list[WrappedEmbed]:
    """Build all message statistics embeds for a user's yearly wrapped."""
    days_in_year = 366 if year % 4 == 0 else 365
    hours_in_year = get_hours_in_year(year)

    embeds: list[WrappedEmbed] = []

    # Main message count embed (always shown)
    embeds.append(_build_message_count_embed(stats, year, days_in_year))

    # Detailed stats only for users with enough messages
    if stats.total_count >= MSG_THRESHOLD_MODERATE:
        # Message details (all fields in a single embed)
        detail_fields = _build_message_details_fields(stats, hours_in_year)
        if detail_fields:
            embeds.append(
                WrappedEmbed(
                    title=f'📊 Message Details in {year}',
                    description='A deeper look at your messaging habits.',
                    color=COLOR_BLURPLE,
                    footer=get_wrapped_footer(year),
                    fields=detail_fields,
                )
            )

        # Distribution embeds (each may return None if no data)
        for embed_builder in [
            _build_peak_months_embed,
            _build_peak_weekdays_embed,
            _build_peak_hours_embed,
            _build_peak_days_embed,
            _build_top_channels_embed,
            _build_longest_silence_embed,
        ]:
            embed = embed_builder(stats, year)
            if embed:
                embeds.append(embed)

    return embeds


async def get_message_stats_embeds(
    edgedb: AsyncIOClient,
    discord_id: str,
    year: int,
) -> list[WrappedEmbed]:
    """Fetch message stats from database and build embeds for a user's yearly wrapped."""
    year_start, year_end = get_year_bounds(year)
    timezone = get_timezone_name()

    # Fetch both stats in parallel
    async with asyncio.TaskGroup() as tg:
        stats_task = tg.create_task(
            wrapped_get_message_stats(
                edgedb,
                discord_id=discord_id,
                year_start=year_start,
                year_end=year_end,
                timezone=timezone,
            )
        )
        night_stats_task = tg.create_task(
            wrapped_get_night_silence_stats(
                edgedb,
                discord_id=discord_id,
                year_start=year_start,
                year_end=year_end,
                timezone=timezone,
            )
        )

    stats = stats_task.result()
    night_stats = night_stats_task.result()

    embeds = build_message_stats_embeds(stats, year)

    # Add night silence embed if we have enough data
    night_embed = build_night_silence_embed(night_stats, year)
    if night_embed:
        embeds.append(night_embed)

    return embeds
