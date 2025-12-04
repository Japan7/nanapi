#!/usr/bin/env python3
"""
Find words with the highest discrepancy between server frequency and IRL frequency.

This script compares word usage on your Discord server against standard French/English
word frequency lists to identify:
- Words overused on the server (server-specific slang, inside jokes)
- Words underused on the server (formal words not used in casual chat)

Usage:
    uv run scripts/find_frequency_discrepancy.py --guild-id "123456789"
    uv run scripts/find_frequency_discrepancy.py --guild-id "123456789" --top 100
    uv run scripts/find_frequency_discrepancy.py --days 90 --min-occurrences 20
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

from nanapi.database.discord.message_word_frequency import message_word_frequency
from nanapi.utils.clients import get_edgedb
from nanapi.utils.word_frequency import analyze_word_frequency, extract_words


def load_irl_frequencies(language: str = 'french') -> Dict[str, float]:
    """
    Load IRL word frequencies from reference files.
    
    Returns a dictionary mapping word -> frequency rank (normalized 0-1).
    Rank 1 (most common) = 1.0, Rank 5000 (least common) = 0.0001
    """
    if language == 'french':
        filename = 'french_common_words.txt'
    else:
        filename = 'english_common_words.txt'
    
    # Try workspace root first, then script directory
    filepath = Path('/workspace') / filename
    if not filepath.exists():
        filepath = Path(__file__).parent.parent.parent / filename
    
    if not filepath.exists():
        print(f"Warning: {filename} not found", file=sys.stderr)
        return {}
    
    frequencies = {}
    total_words = 0
    
    with open(filepath, 'r', encoding='utf-8') as f:
        rank = 1
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            word = line.lower()
            # Normalize rank to 0-1 scale (inverse rank for frequency)
            # Most common word (rank 1) gets highest score
            # Use log scale for more meaningful distribution
            frequency_score = 1.0 / (rank ** 0.5)  # Square root dampening
            frequencies[word] = frequency_score
            rank += 1
            total_words += 1
    
    # Normalize to 0-1 range
    max_score = max(frequencies.values()) if frequencies else 1.0
    frequencies = {k: v / max_score for k, v in frequencies.items()}
    
    print(f"Loaded {total_words} IRL {language} word frequencies", file=sys.stderr)
    return frequencies


def compute_server_frequencies(messages: List) -> Dict[str, float]:
    """
    Compute normalized word frequencies from server messages.
    
    Returns dictionary mapping word -> normalized frequency (0-1).
    """
    from collections import Counter
    
    word_counts = Counter()
    
    for msg in messages:
        words = extract_words(msg.content)
        for word in words:
            word_counts[word] += 1
    
    if not word_counts:
        return {}
    
    # Normalize to 0-1 range
    max_count = max(word_counts.values())
    frequencies = {word: count / max_count for word, count in word_counts.items()}
    
    return frequencies


def calculate_discrepancy_scores(
    server_freq: Dict[str, float],
    irl_freq: Dict[str, float],
    min_server_occurrences: int = 10,
    server_word_counts: Dict[str, int] = None,
) -> List[Tuple[str, float, float, float, str]]:
    """
    Calculate discrepancy scores between server and IRL frequencies.
    
    Returns list of (word, server_freq, irl_freq, discrepancy_score, type).
    - Positive scores: overused on server (server-specific)
    - Negative scores: underused on server (avoided words)
    
    Discrepancy types:
    - 'server_exclusive': Used on server but not in IRL top 5000
    - 'server_heavy': Used much more on server than IRL
    - 'balanced': Similar usage
    - 'irl_heavy': Used much more IRL than on server
    - 'irl_exclusive': Common IRL but not used on server
    """
    results = []
    
    # Words used on server
    for word, s_freq in server_freq.items():
        # Skip if below minimum occurrences
        if server_word_counts and server_word_counts.get(word, 0) < min_server_occurrences:
            continue
        
        irl_freq_value = irl_freq.get(word, 0.0)
        
        if irl_freq_value == 0:
            # Server exclusive - not in IRL top 5000
            discrepancy = s_freq * 10.0  # Amplify server-only words
            results.append((word, s_freq, 0.0, discrepancy, 'server_exclusive'))
        else:
            # Calculate ratio (with smoothing to avoid division issues)
            ratio = (s_freq + 0.0001) / (irl_freq_value + 0.0001)
            
            # Log scale for better distribution
            import math
            discrepancy = math.log10(ratio)
            
            if discrepancy > 1.0:
                type_label = 'server_heavy'
            elif discrepancy < -1.0:
                type_label = 'irl_heavy'
            else:
                type_label = 'balanced'
            
            results.append((word, s_freq, irl_freq_value, discrepancy, type_label))
    
    # Common IRL words not used on server
    for word, irl_freq_value in irl_freq.items():
        if word not in server_freq and irl_freq_value > 0.1:  # Only very common IRL words
            # Calculate negative discrepancy for missing common words
            discrepancy = -5.0 * irl_freq_value  # More common = more negative
            results.append((word, 0.0, irl_freq_value, discrepancy, 'irl_exclusive'))
    
    # Sort by absolute discrepancy (most different first)
    results.sort(key=lambda x: abs(x[3]), reverse=True)
    
    return results


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Find words with highest server vs IRL frequency discrepancy',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --guild-id "123456789"
  %(prog)s --guild-id "123456789" --language english
  %(prog)s --days 90 --top 100 --output discrepancy_report.txt
        """
    )
    
    parser.add_argument('--guild-id', type=str, help='Filter by guild/server ID')
    parser.add_argument('--channel-id', type=str, help='Filter by channel ID')
    parser.add_argument('--days', type=int, default=90, help='Number of days to analyze (default: 90)')
    parser.add_argument('--language', choices=['french', 'english'], default='french',
                       help='Reference language for IRL frequencies (default: french)')
    parser.add_argument('--min-occurrences', type=int, default=10,
                       help='Minimum word occurrences on server (default: 10)')
    parser.add_argument('--top', type=int, default=100, help='Number of top results to show (default: 100)')
    parser.add_argument('--output', '-o', help='Output file (default: stdout)')
    parser.add_argument('--show-balanced', action='store_true',
                       help='Show balanced words too (similar server and IRL usage)')
    
    args = parser.parse_args()
    
    # Calculate date range
    from zoneinfo import ZoneInfo
    tz = ZoneInfo('UTC')
    end_date = datetime.now(tz)
    start_date = end_date - timedelta(days=args.days)
    
    print(f"Analyzing messages from {start_date.date()} to {end_date.date()}")
    if args.channel_id:
        print(f"Channel: {args.channel_id}")
    if args.guild_id:
        print(f"Guild: {args.guild_id}")
    print(f"Reference language: {args.language}")
    print()
    
    # Fetch messages
    print("Fetching messages from server...", file=sys.stderr)
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
    
    print(f"Found {len(messages):,} messages", file=sys.stderr)
    print()
    
    # Compute server frequencies
    print("Computing server word frequencies...", file=sys.stderr)
    from collections import Counter
    word_counts = Counter()
    for msg in messages:
        words = extract_words(msg.content)
        for word in words:
            word_counts[word] += 1
    
    server_freq = compute_server_frequencies(messages)
    print(f"Found {len(server_freq):,} unique words on server", file=sys.stderr)
    print()
    
    # Load IRL frequencies
    print(f"Loading IRL {args.language} word frequencies...", file=sys.stderr)
    irl_freq = load_irl_frequencies(args.language)
    print()
    
    # Calculate discrepancies
    print("Calculating discrepancy scores...", file=sys.stderr)
    results = calculate_discrepancy_scores(
        server_freq,
        irl_freq,
        min_server_occurrences=args.min_occurrences,
        server_word_counts=word_counts,
    )
    print()
    
    # Generate report
    report_lines = []
    report_lines.append("=" * 100)
    report_lines.append("WORD FREQUENCY DISCREPANCY ANALYSIS: SERVER vs IRL")
    report_lines.append("=" * 100)
    report_lines.append(f"Server messages analyzed: {len(messages):,}")
    report_lines.append(f"Date range: {start_date.date()} to {end_date.date()}")
    report_lines.append(f"Reference language: {args.language}")
    report_lines.append(f"Unique words on server: {len(server_freq):,}")
    report_lines.append(f"IRL reference words: {len(irl_freq):,}")
    report_lines.append("")
    report_lines.append("Discrepancy Score:")
    report_lines.append("  - Positive = Used more on server than IRL (server-specific vocabulary)")
    report_lines.append("  - Negative = Used less on server than IRL (avoided or formal words)")
    report_lines.append("  - Zero = Similar usage patterns")
    report_lines.append("")
    
    # Categorize results
    server_exclusive = [r for r in results if r[4] == 'server_exclusive']
    server_heavy = [r for r in results if r[4] == 'server_heavy']
    irl_heavy = [r for r in results if r[4] == 'irl_heavy']
    irl_exclusive = [r for r in results if r[4] == 'irl_exclusive']
    balanced = [r for r in results if r[4] == 'balanced']
    
    # Top overused words (server-specific)
    report_lines.append("=" * 100)
    report_lines.append(f"TOP {min(args.top, len(server_exclusive))} SERVER-EXCLUSIVE WORDS")
    report_lines.append("=" * 100)
    report_lines.append("These words are used on your server but NOT in the top 5000 IRL words.")
    report_lines.append("Perfect candidates for server-specific trigger words!")
    report_lines.append("")
    report_lines.append(f"{'Word':<25} {'Server Count':>12} {'Server Freq':>12} {'Discrepancy':>12}")
    report_lines.append("-" * 100)
    
    for word, s_freq, i_freq, disc, _ in server_exclusive[:args.top]:
        count = word_counts.get(word, 0)
        report_lines.append(f"{word:<25} {count:>12,} {s_freq:>12.4f} {disc:>12.2f}")
    
    report_lines.append("")
    report_lines.append("=" * 100)
    report_lines.append(f"TOP {min(args.top, len(server_heavy))} OVERUSED WORDS ON SERVER")
    report_lines.append("=" * 100)
    report_lines.append("These words exist IRL but are used MUCH MORE on your server.")
    report_lines.append("")
    report_lines.append(f"{'Word':<25} {'Server Freq':>12} {'IRL Freq':>12} {'Discrepancy':>12}")
    report_lines.append("-" * 100)
    
    for word, s_freq, i_freq, disc, _ in server_heavy[:args.top]:
        report_lines.append(f"{word:<25} {s_freq:>12.4f} {i_freq:>12.4f} {disc:>12.2f}")
    
    report_lines.append("")
    report_lines.append("=" * 100)
    report_lines.append(f"TOP {min(args.top // 2, len(irl_exclusive))} UNDERUSED COMMON IRL WORDS")
    report_lines.append("=" * 100)
    report_lines.append("These are common IRL words that your server rarely/never uses.")
    report_lines.append("Often formal or written language not used in casual Discord chat.")
    report_lines.append("")
    report_lines.append(f"{'Word':<25} {'IRL Freq':>12} {'Discrepancy':>12}")
    report_lines.append("-" * 100)
    
    for word, s_freq, i_freq, disc, _ in irl_exclusive[:args.top // 2]:
        report_lines.append(f"{word:<25} {i_freq:>12.4f} {disc:>12.2f}")
    
    if args.show_balanced:
        report_lines.append("")
        report_lines.append("=" * 100)
        report_lines.append(f"BALANCED WORDS (Similar Usage)")
        report_lines.append("=" * 100)
        report_lines.append("")
        report_lines.append(f"{'Word':<25} {'Server Freq':>12} {'IRL Freq':>12} {'Discrepancy':>12}")
        report_lines.append("-" * 100)
        
        for word, s_freq, i_freq, disc, _ in balanced[:50]:
            report_lines.append(f"{word:<25} {s_freq:>12.4f} {i_freq:>12.4f} {disc:>12.2f}")
    
    report_lines.append("")
    report_lines.append("=" * 100)
    report_lines.append("SUMMARY STATISTICS")
    report_lines.append("=" * 100)
    report_lines.append(f"Server-exclusive words: {len(server_exclusive):,}")
    report_lines.append(f"Server-heavy words: {len(server_heavy):,}")
    report_lines.append(f"Balanced words: {len(balanced):,}")
    report_lines.append(f"IRL-heavy words: {len(irl_heavy):,}")
    report_lines.append(f"IRL-exclusive (not used on server): {len(irl_exclusive):,}")
    report_lines.append("")
    report_lines.append("💡 TIP: Server-exclusive and server-heavy words make the best")
    report_lines.append("   trigger words for your WaiColle conditional drops!")
    report_lines.append("=" * 100)
    
    report = "\n".join(report_lines)
    
    # Output
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"Report written to: {args.output}", file=sys.stderr)
    else:
        print(report)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user.", file=sys.stderr)
        sys.exit(1)

