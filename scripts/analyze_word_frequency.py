#!/usr/bin/env python3
"""
Script to analyze word frequency in Discord messages.

This helps identify statistically frequent words that could be used as new
trigger words for conditional drops in the WaiColle game.

Usage:
    uv run scripts/analyze_word_frequency.py --guild-id "123456789"
    uv run scripts/analyze_word_frequency.py --channel-id "987654321" --days 30
"""

import asyncio
import sys
from datetime import datetime, timedelta

from nanapi.database.discord.message_word_frequency import message_word_frequency
from nanapi.utils.clients import get_edgedb
from nanapi.utils.word_frequency import analyze_word_frequency


async def main():
    import argparse

    parser = argparse.ArgumentParser(description='Analyze word frequency in Discord messages')
    parser.add_argument('--channel-id', type=str, help='Filter by channel ID')
    parser.add_argument('--guild-id', type=str, help='Filter by guild/server ID')
    parser.add_argument('--days', type=int, default=30, help='Number of days to analyze (default: 30)')
    parser.add_argument('--min-occurrences', type=int, default=10, help='Minimum word occurrences')
    parser.add_argument('--min-users', type=int, default=2, help='Minimum unique users')
    parser.add_argument('--top-n', type=int, default=50, help='Number of top words to show')
    parser.add_argument('--show-suggestions', action='store_true', help='Show suggested trigger words')

    args = parser.parse_args()

    # Calculate date range (timezone-aware)
    from zoneinfo import ZoneInfo
    tz = ZoneInfo('UTC')
    end_date = datetime.now(tz)
    start_date = end_date - timedelta(days=args.days)

    print(f"Analyzing messages from {start_date.date()} to {end_date.date()}")
    if args.channel_id:
        print(f"Channel: {args.channel_id}")
    if args.guild_id:
        print(f"Guild: {args.guild_id}")
    print()

    # Fetch messages
    edgedb = get_edgedb()
    messages = await message_word_frequency(
        edgedb,
        channel_id=args.channel_id,
        guild_id=args.guild_id,
        start_date=start_date,
        end_date=end_date,
    )

    if not messages:
        print("No messages found matching the criteria.")
        return

    print(f"Found {len(messages)} messages to analyze...")
    print()

    # Analyze
    analysis = analyze_word_frequency(
        messages,
        min_occurrences=args.min_occurrences,
        min_users=args.min_users,
        top_n=args.top_n,
    )

    # Print results
    print("=" * 80)
    print("WORD FREQUENCY ANALYSIS")
    print("=" * 80)
    print(f"Total messages: {analysis.total_messages}")
    print(f"Total words: {analysis.total_words}")
    print(f"Unique words: {analysis.unique_words}")
    print()

    print("-" * 80)
    print(f"TOP {len(analysis.top_words)} MOST FREQUENT WORDS")
    print("-" * 80)
    print(f"{'Word':<30} {'Count':>8} {'Messages':>10} {'Frequency':>10} {'Users':>8}")
    print("-" * 80)

    for word_data in analysis.top_words[:args.top_n]:
        print(
            f"{word_data['word']:<30} "
            f"{word_data['count']:>8} "
            f"{word_data['message_count']:>10} "
            f"{word_data['frequency']:>10.4f} "
            f"{word_data['unique_users']:>8}"
        )

    if args.show_suggestions and analysis.suggested_triggers:
        print()
        print("-" * 80)
        print("SUGGESTED TRIGGER WORDS FOR CONDITIONAL DROPS")
        print("-" * 80)
        print(
            "These words are frequent enough to be interesting but not too common.\n"
            "They're used by multiple people, making them good candidates for triggers."
        )
        print()
        print(f"{'Word':<30} {'Count':>8} {'Frequency':>10} {'Users':>8} {'Score':>8}")
        print("-" * 80)

        for word_data in analysis.suggested_triggers[:30]:
            print(
                f"{word_data['word']:<30} "
                f"{word_data['count']:>8} "
                f"{word_data['frequency']:>10.4f} "
                f"{word_data['unique_users']:>8} "
                f"{word_data['score']:>8.2f}"
            )

        print()
        print("To add a new trigger word, edit:")
        print("  /workspace/nanachan/nanachan/utils/conditions.py")
        print("And add to the StringCondition.words list, e.g.:")
        print("  Word.simple('your_word'),")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        sys.exit(1)

