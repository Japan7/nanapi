#!/usr/bin/env python3
"""
Script to analyze a specific user's characteristic words.

This helps identify words that are particularly used by one person
compared to the rest of the community - their "signature words".

Usage:
    uv run scripts/analyze_user_words.py --user-id "123456789012345678" --guild-id "987654321"
    uv run scripts/analyze_user_words.py --user-id "123456789012345678" --channel-id "111222333" --days 60
"""

import asyncio
import sys
from datetime import datetime, timedelta

from nanapi.database.discord.message_word_frequency import message_word_frequency
from nanapi.utils.clients import get_edgedb
from nanapi.utils.user_word_analysis import analyze_user_words


async def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Analyze characteristic words for a specific user'
    )
    parser.add_argument('--user-id', type=str, required=True, help='Discord user ID to analyze')
    parser.add_argument('--channel-id', type=str, help='Filter by channel ID')
    parser.add_argument('--guild-id', type=str, help='Filter by guild/server ID')
    parser.add_argument('--days', type=int, default=30, help='Number of days to analyze (default: 30)')
    parser.add_argument(
        '--min-user-count', type=int, default=5, help='Minimum times user must use word'
    )
    parser.add_argument(
        '--min-ratio',
        type=float,
        default=2.0,
        help='Minimum ratio of user_freq/community_freq',
    )
    parser.add_argument('--top-n', type=int, default=50, help='Number of top words to show')

    args = parser.parse_args()

    # Calculate date range (timezone-aware)
    from zoneinfo import ZoneInfo
    tz = ZoneInfo('UTC')
    end_date = datetime.now(tz)
    start_date = end_date - timedelta(days=args.days)

    print(f"Analyzing user {args.user_id}")
    print(f"Date range: {start_date.date()} to {end_date.date()}")
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

    print(f"Found {len(messages)} total messages to analyze...")
    print()

    # Analyze
    analysis = analyze_user_words(
        messages,
        user_id=args.user_id,
        min_user_count=args.min_user_count,
        min_ratio=args.min_ratio,
        top_n=args.top_n,
    )

    if analysis.user_messages == 0:
        print(f"User {args.user_id} has no messages in this time period.")
        return

    # Print results
    print("=" * 80)
    print(f"USER WORD ANALYSIS: {args.user_id}")
    print("=" * 80)
    print()

    print("📊 MESSAGE STATISTICS")
    print("-" * 80)
    print(f"User's messages:      {analysis.user_messages:>10}")
    print(f"Community messages:   {analysis.community_messages:>10}")
    print(f"User's total words:   {analysis.user_total_words:>10}")
    print(f"Community words:      {analysis.community_total_words:>10}")
    print()

    summary = analysis.comparison_summary
    print("📖 VOCABULARY COMPARISON")
    print("-" * 80)
    print(f"User vocabulary size:       {summary['user_vocabulary_size']:>10}")
    print(f"Community vocabulary size:  {summary['community_vocabulary_size']:>10}")
    print(f"Shared words:               {summary['shared_words']:>10}")
    print(f"User exclusive words:       {summary['user_exclusive_words']:>10}")
    print(f"Vocabulary overlap:         {summary['vocabulary_overlap_percent']:>9.1f}%")
    print()
    print(f"User avg message length:    {summary['avg_message_length']:>9.2f} words")
    print(
        f"Community avg msg length:   {summary['community_avg_message_length']:>9.2f} words"
    )
    print()

    if analysis.characteristic_words:
        print("🎯 CHARACTERISTIC WORDS (User says these WAY more than others)")
        print("-" * 80)
        print(
            f"{'Word':<25} {'User':>8} {'Others':>8} {'Ratio':>8} {'Score':>8} {'User%':>8}"
        )
        print("-" * 80)

        for word_data in analysis.characteristic_words[:args.top_n]:
            user_pct = word_data['user_frequency'] * 100
            print(
                f"{word_data['word']:<25} "
                f"{word_data['user_count']:>8} "
                f"{word_data['community_count']:>8} "
                f"{word_data['ratio']:>8.2f}x "
                f"{word_data['uniqueness_score']:>8.2f} "
                f"{user_pct:>7.2f}%"
            )

        print()
        print("💡 Interpretation:")
        print(
            "   - Ratio: How many times more frequently this user says the word vs others"
        )
        print("   - Score: Uniqueness metric (higher = more characteristic)")
        print("   - User%: Percentage of user's messages containing this word")
    else:
        print("No characteristic words found with the current thresholds.")
        print(f"Try lowering --min-user-count (currently {args.min_user_count})")
        print(f"or --min-ratio (currently {args.min_ratio})")

    print()

    if analysis.unique_words:
        print("✨ UNIQUE/EXCLUSIVE WORDS (Rarely used by others)")
        print("-" * 80)
        print(f"{'Word':<25} {'User Count':>12} {'Others Count':>14} {'User%':>8}")
        print("-" * 80)

        for word_data in analysis.unique_words[:30]:
            user_pct = word_data['user_frequency'] * 100
            print(
                f"{word_data['word']:<25} "
                f"{word_data['user_count']:>12} "
                f"{word_data['community_count']:>14} "
                f"{user_pct:>7.2f}%"
            )

        print()
        print("💡 These words are almost exclusive to this user!")

    print()
    print("=" * 80)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        sys.exit(1)

