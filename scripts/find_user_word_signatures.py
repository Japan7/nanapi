#!/usr/bin/env python3
"""
Find each user's signature words by comparing their vocabulary against community average.

Identifies words that are uniquely characteristic of individual users - their
catchphrases, favorite expressions, and distinctive language patterns.

Usage:
    uv run scripts/find_user_word_signatures.py --guild-id "123456789"
    uv run scripts/find_user_word_signatures.py --guild-id "123456789" --min-messages 100
    uv run scripts/find_user_word_signatures.py --top-users 20 --output user_signatures.txt
"""

import asyncio
import math
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

from nanapi.database.discord.message_word_frequency import message_word_frequency
from nanapi.utils.clients import get_edgedb
from nanapi.utils.word_frequency import extract_words


def compute_user_signatures(
    messages: List,
    min_user_messages: int = 50,
    min_word_occurrences: int = 5,
    top_n_per_user: int = 20,
) -> Dict:
    """
    Compute signature words for each user.
    
    Args:
        messages: List of message objects with content and author_id
        min_user_messages: Minimum messages a user must have to be analyzed
        min_word_occurrences: Minimum times a word must appear for a user
        top_n_per_user: Number of top signature words per user
        
    Returns:
        Dictionary with user statistics and signature words
    """
    # Group messages by user
    user_messages = defaultdict(list)
    for msg in messages:
        user_messages[msg.author_id].append(msg)
    
    # Calculate community average frequencies
    community_word_counts = Counter()
    community_total_words = 0
    
    for msg in messages:
        words = extract_words(msg.content)
        community_word_counts.update(words)
        community_total_words += len(words)
    
    # Calculate community frequencies
    community_freq = {
        word: count / community_total_words 
        for word, count in community_word_counts.items()
    }
    
    # Analyze each user
    user_signatures = {}
    
    for user_id, msgs in user_messages.items():
        if len(msgs) < min_user_messages:
            continue
        
        # Count user's words
        user_word_counts = Counter()
        user_total_words = 0
        
        for msg in msgs:
            words = extract_words(msg.content)
            user_word_counts.update(words)
            user_total_words += len(words)
        
        if user_total_words < 50:  # Skip users with very few words
            continue
        
        # Calculate discrepancies
        signature_words = []
        
        for word, count in user_word_counts.items():
            if count < min_word_occurrences:
                continue
            
            user_freq = count / user_total_words
            comm_freq = community_freq.get(word, 0.0001)  # Small default for unseen words
            
            # Calculate log ratio (discrepancy)
            ratio = user_freq / comm_freq
            discrepancy = math.log10(ratio)
            
            # Only include words user says more than average
            if discrepancy > 0.3:  # At least 2x more than average
                signature_words.append({
                    'word': word,
                    'user_count': count,
                    'user_freq': user_freq,
                    'community_freq': comm_freq,
                    'discrepancy': discrepancy,
                })
        
        # Sort by discrepancy score
        signature_words.sort(key=lambda x: x['discrepancy'], reverse=True)
        
        # Calculate distinctiveness score (0-10)
        avg_discrepancy = sum(w['discrepancy'] for w in signature_words[:10]) / min(10, len(signature_words)) if signature_words else 0
        distinctiveness = min(10, avg_discrepancy * 2)
        
        user_signatures[user_id] = {
            'user_id': user_id,
            'message_count': len(msgs),
            'total_words': user_total_words,
            'unique_words': len(user_word_counts),
            'signature_words': signature_words[:top_n_per_user],
            'distinctiveness_score': distinctiveness,
        }
    
    return {
        'community_stats': {
            'total_messages': len(messages),
            'total_words': community_total_words,
            'unique_words': len(community_word_counts),
            'users_analyzed': len(user_signatures),
        },
        'users': user_signatures,
    }


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Find signature words for each user',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --guild-id "123456789"
  %(prog)s --guild-id "123456789" --min-messages 100 --top-users 20
  %(prog)s --days 90 --output user_signatures.txt
        """
    )
    
    parser.add_argument('--guild-id', type=str, help='Guild/server ID to analyze')
    parser.add_argument('--channel-id', type=str, help='Specific channel ID (optional)')
    parser.add_argument('--days', type=int, default=90, help='Number of days to analyze (default: 90)')
    parser.add_argument('--min-messages', type=int, default=50,
                       help='Minimum messages per user (default: 50)')
    parser.add_argument('--min-word-count', type=int, default=5,
                       help='Minimum word occurrences for user (default: 5)')
    parser.add_argument('--top-users', type=int, default=30,
                       help='Number of top users to show in detail (default: 30)')
    parser.add_argument('--top-words', type=int, default=20,
                       help='Signature words per user (default: 20)')
    parser.add_argument('--output', '-o', help='Output file (default: stdout)')
    parser.add_argument('--format', choices=['text', 'json'], default='text',
                       help='Output format (default: text)')
    
    args = parser.parse_args()
    
    # Calculate date range
    from zoneinfo import ZoneInfo
    tz = ZoneInfo('UTC')
    end_date = datetime.now(tz)
    start_date = end_date - timedelta(days=args.days)
    
    print(f"Fetching messages from {start_date.date()} to {end_date.date()}", file=sys.stderr)
    if args.guild_id:
        print(f"Guild: {args.guild_id}", file=sys.stderr)
    print("", file=sys.stderr)
    
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
        print("Error: No messages found", file=sys.stderr)
        sys.exit(1)
    
    print(f"Analyzing {len(messages):,} messages...", file=sys.stderr)
    print("", file=sys.stderr)
    
    # Compute signatures
    results = compute_user_signatures(
        messages,
        min_user_messages=args.min_messages,
        min_word_occurrences=args.min_word_count,
        top_n_per_user=args.top_words,
    )
    
    # Generate report
    if args.format == 'json':
        import json
        output = json.dumps(results, indent=2, ensure_ascii=False)
    else:
        output = generate_text_report(results, args.top_users, args.top_words)
    
    # Write output
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"Report written to: {args.output}", file=sys.stderr)
    else:
        print(output)


def generate_text_report(results: Dict, top_users: int, top_words: int) -> str:
    """Generate formatted text report."""
    lines = []
    
    stats = results['community_stats']
    users = results['users']
    
    lines.append("=" * 100)
    lines.append("USER SIGNATURE WORD ANALYSIS")
    lines.append("=" * 100)
    lines.append(f"Total messages analyzed: {stats['total_messages']:,}")
    lines.append(f"Total words: {stats['total_words']:,}")
    lines.append(f"Unique words: {stats['unique_words']:,}")
    lines.append(f"Users analyzed: {stats['users_analyzed']}")
    lines.append("")
    lines.append("Signature words = words a user says significantly MORE than community average")
    lines.append("Discrepancy score = log10(user_freq / community_freq)")
    lines.append("  +0.5 = 3x more than average")
    lines.append("  +1.0 = 10x more than average")
    lines.append("  +2.0 = 100x more than average")
    lines.append("")
    
    # Sort users by distinctiveness
    sorted_users = sorted(
        users.values(),
        key=lambda x: x['distinctiveness_score'],
        reverse=True
    )
    
    # Overall ranking
    lines.append("=" * 100)
    lines.append("MOST DISTINCTIVE USERS (by signature word strength)")
    lines.append("=" * 100)
    lines.append(f"{'Rank':<6} {'User ID':<30} {'Messages':>10} {'Distinctiveness':>15} {'Top Word':>20}")
    lines.append("-" * 100)
    
    for i, user in enumerate(sorted_users[:top_users], 1):
        top_word = user['signature_words'][0]['word'] if user['signature_words'] else 'N/A'
        lines.append(
            f"{i:<6} "
            f"{user['user_id']:<30} "
            f"{user['message_count']:>10,} "
            f"{user['distinctiveness_score']:>15.2f} "
            f"{top_word:>20}"
        )
    
    lines.append("")
    
    # Detailed per-user analysis
    lines.append("=" * 100)
    lines.append(f"DETAILED USER PROFILES (Top {min(top_users, len(sorted_users))} users)")
    lines.append("=" * 100)
    lines.append("")
    
    for i, user in enumerate(sorted_users[:top_users], 1):
        lines.append("-" * 100)
        lines.append(f"#{i} USER: {user['user_id']}")
        lines.append("-" * 100)
        lines.append(f"Messages: {user['message_count']:,}")
        lines.append(f"Total words: {user['total_words']:,}")
        lines.append(f"Unique words: {user['unique_words']:,}")
        lines.append(f"Distinctiveness score: {user['distinctiveness_score']:.2f}/10")
        lines.append("")
        
        if user['signature_words']:
            lines.append(f"TOP {len(user['signature_words'])} SIGNATURE WORDS:")
            lines.append(f"{'Word':<25} {'Uses':>8} {'User %':>10} {'Comm %':>10} {'Discrepancy':>12}")
            lines.append("-" * 100)
            
            for word_data in user['signature_words']:
                lines.append(
                    f"{word_data['word']:<25} "
                    f"{word_data['user_count']:>8} "
                    f"{word_data['user_freq']*100:>9.3f}% "
                    f"{word_data['community_freq']*100:>9.3f}% "
                    f"{word_data['discrepancy']:>12.2f}"
                )
        else:
            lines.append("No distinctive signature words found (usage matches community average)")
        
        lines.append("")
    
    # Summary statistics
    lines.append("=" * 100)
    lines.append("SUMMARY STATISTICS")
    lines.append("=" * 100)
    
    if sorted_users:
        avg_distinctiveness = sum(u['distinctiveness_score'] for u in sorted_users) / len(sorted_users)
        lines.append(f"Average distinctiveness score: {avg_distinctiveness:.2f}/10")
        lines.append(f"Most distinctive user: {sorted_users[0]['user_id']} ({sorted_users[0]['distinctiveness_score']:.2f}/10)")
        lines.append(f"Least distinctive user: {sorted_users[-1]['user_id']} ({sorted_users[-1]['distinctiveness_score']:.2f}/10)")
        
        # Find most common signature words across users
        all_signature_words = Counter()
        for user in sorted_users:
            for word_data in user['signature_words'][:5]:  # Top 5 per user
                all_signature_words[word_data['word']] += 1
        
        lines.append("")
        lines.append("Most common signature words (appearing in multiple users' top signatures):")
        for word, count in all_signature_words.most_common(20):
            lines.append(f"  {word}: {count} users")
    
    lines.append("")
    lines.append("=" * 100)
    lines.append("💡 TIP: Use signature words for personalized conditional drops!")
    lines.append("   Create user-specific triggers that activate when users say their catchphrases.")
    lines.append("=" * 100)
    
    return "\n".join(lines)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user.", file=sys.stderr)
        sys.exit(1)
