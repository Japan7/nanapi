#!/usr/bin/env python3
"""
Demo script to show word frequency analysis with sample data.

This demonstrates what the analysis would look like with real Discord messages.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

from pydantic import BaseModel

from nanapi.utils.word_frequency import analyze_word_frequency


class MockMessage(BaseModel):
    """Mock message for demonstration."""
    content: str
    author_id: str
    channel_id: str = "demo_channel"
    guild_id: str = "demo_guild"
    timestamp: datetime = datetime.now(ZoneInfo('UTC'))


# Sample messages simulating a Discord server
SAMPLE_MESSAGES = [
    # User 1 - The "pog" person
    MockMessage(content="pog that was amazing!", author_id="user1"),
    MockMessage(content="poggers play dude", author_id="user1"),
    MockMessage(content="pog pog pog", author_id="user1"),
    MockMessage(content="that's so pog", author_id="user1"),
    MockMessage(content="mega pog moment", author_id="user1"),
    # User 2 - The "copium" person
    MockMessage(content="inhaling copium right now", author_id="user2"),
    MockMessage(content="pure copium lol", author_id="user2"),
    MockMessage(content="copium overdose", author_id="user2"),
    MockMessage(content="need more copium", author_id="user2"),
    # User 3 - French speaker
    MockMessage(content="du coup on fait quoi ?", author_id="user3"),
    MockMessage(content="en vrai c'est pas mal", author_id="user3"),
    MockMessage(content="genre vraiment ?", author_id="user3"),
    MockMessage(content="du coup oui", author_id="user3"),
    MockMessage(content="en vrai du coup", author_id="user3"),
    # Mixed users
    MockMessage(content="hello everyone!", author_id="user4"),
    MockMessage(content="pog", author_id="user5"),
    MockMessage(content="nice stream today", author_id="user4"),
    MockMessage(content="copium", author_id="user5"),
    MockMessage(content="genre", author_id="user6"),
    MockMessage(content="lol that's funny", author_id="user4"),
    MockMessage(content="based take", author_id="user5"),
    MockMessage(content="cringe moment", author_id="user6"),
    MockMessage(content="hello hello", author_id="user7"),
    MockMessage(content="du coup", author_id="user7"),
    # More variety
    MockMessage(content="anyone wanna play AMQ?", author_id="user4"),
    MockMessage(content="karaoke tonight!", author_id="user5"),
    MockMessage(content="projection at 8pm", author_id="user6"),
    MockMessage(content="waifu roll time", author_id="user7"),
    MockMessage(content="drop drop drop", author_id="user4"),
    MockMessage(content="n7 gang", author_id="user5"),
    MockMessage(content="statistiquement parlant", author_id="user3"),
]


def main():
    print("=" * 80)
    print("WORD FREQUENCY ANALYSIS DEMO")
    print("=" * 80)
    print(f"Sample data: {len(SAMPLE_MESSAGES)} messages from {len(set(m.author_id for m in SAMPLE_MESSAGES))} users")
    print()

    # Run analysis
    analysis = analyze_word_frequency(
        SAMPLE_MESSAGES,
        min_occurrences=2,
        min_users=1,
        top_n=30,
    )

    # Print results
    print(f"Total messages: {analysis.total_messages}")
    print(f"Total words: {analysis.total_words}")
    print(f"Unique words: {analysis.unique_words}")
    print()

    print("-" * 80)
    print("TOP MOST FREQUENT WORDS")
    print("-" * 80)
    print(f"{'Word':<25} {'Count':>8} {'Messages':>10} {'Frequency':>10} {'Users':>8}")
    print("-" * 80)

    for word_data in analysis.top_words[:20]:
        print(
            f"{word_data['word']:<25} "
            f"{word_data['count']:>8} "
            f"{word_data['message_count']:>10} "
            f"{word_data['frequency']:>10.4f} "
            f"{word_data['unique_users']:>8}"
        )

    if analysis.suggested_triggers:
        print()
        print("-" * 80)
        print("SUGGESTED TRIGGER WORDS FOR CONDITIONAL DROPS")
        print("-" * 80)
        print(f"{'Word':<25} {'Count':>8} {'Frequency':>10} {'Users':>8} {'Score':>8}")
        print("-" * 80)

        for word_data in analysis.suggested_triggers[:15]:
            print(
                f"{word_data['word']:<25} "
                f"{word_data['count']:>8} "
                f"{word_data['frequency']:>10.4f} "
                f"{word_data['unique_users']:>8} "
                f"{word_data['score']:>8.2f}"
            )

    print()
    print("=" * 80)
    print("💡 This is what the analysis looks like with real data!")
    print("   To analyze your actual Discord messages:")
    print("   1. Load your database dump with messages")
    print("   2. Or run nanachan to collect live messages")
    print("   3. Then run: uv run scripts/analyze_word_frequency.py --guild-id YOUR_GUILD")
    print("=" * 80)


if __name__ == '__main__':
    main()

