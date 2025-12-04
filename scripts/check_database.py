#!/usr/bin/env python3
"""
Script to check what's in the database.

This displays counts and sample data from all major tables.

Usage:
    uv run scripts/check_database.py
    uv run scripts/check_database.py --details
"""

import asyncio
import sys

from nanapi.utils.clients import get_edgedb


async def main():
    import argparse

    parser = argparse.ArgumentParser(description='Check database contents')
    parser.add_argument('--details', action='store_true', help='Show detailed sample data')
    parser.add_argument('--limit', type=int, default=5, help='Number of sample records to show')

    args = parser.parse_args()

    edgedb = get_edgedb()

    print("=" * 80)
    print("DATABASE CONTENTS CHECK")
    print("=" * 80)
    print()

    # Define tables to check
    tables = [
        ("discord::Message", "Discord messages"),
        ("discord::MessagePage", "Message pages (for AI embeddings)"),
        ("user::User", "Discord users"),
        ("user::Profile", "User profiles"),
        ("default::Client", "API clients"),
        ("waicolle::Player", "WaiColle players"),
        ("waicolle::Waifu", "Waifus owned by players"),
        ("waicolle::Collection", "Waifu collections"),
        ("waicolle::Trade", "Active trades"),
        ("anilist::Media", "Anime/Manga from AniList"),
        ("anilist::Character", "Characters from AniList"),
        ("anilist::Staff", "Staff from AniList"),
        ("calendar::GuildEvent", "Calendar events"),
        ("quizz::Quizz", "Quizzes"),
        ("projection::Projection", "Projections"),
        ("pot::Pot", "Pots"),
        ("reminder::Reminder", "Reminders"),
    ]

    print("📊 TABLE COUNTS")
    print("-" * 80)

    counts = {}
    for table_name, description in tables:
        try:
            result = await edgedb.query_single(f"SELECT count({table_name})")
            counts[table_name] = result
            status = "✓" if result > 0 else "○"
            print(f"{status} {description:<40} {result:>10,} records")
        except Exception as e:
            print(f"✗ {description:<40} Error: {str(e)[:30]}")

    print()
    print("=" * 80)
    print(f"SUMMARY: {sum(counts.values()):,} total records across all tables")
    print("=" * 80)

    # Show details if requested
    if args.details:
        print()
        print("📋 SAMPLE DATA (showing up to {} records per table)".format(args.limit))
        print("=" * 80)

        # Discord Messages
        if counts.get("discord::Message", 0) > 0:
            print()
            print("💬 DISCORD MESSAGES")
            print("-" * 80)
            messages = await edgedb.query(
                """
                SELECT discord::Message {
                    channel_id,
                    author_id,
                    content,
                    timestamp,
                }
                ORDER BY .timestamp DESC
                LIMIT <int64>$limit
                """,
                limit=args.limit,
            )
            for msg in messages:
                content_preview = msg.content[:60] + "..." if len(msg.content) > 60 else msg.content
                print(f"  [{msg.timestamp}] {msg.author_id}: {content_preview}")

        # Users
        if counts.get("user::User", 0) > 0:
            print()
            print("👤 USERS")
            print("-" * 80)
            users = await edgedb.query(
                """
                SELECT user::User {
                    discord_id,
                    discord_username,
                }
                LIMIT <int64>$limit
                """,
                limit=args.limit,
            )
            for user in users:
                print(f"  {user.discord_username} (ID: {user.discord_id})")

        # WaiColle Players
        if counts.get("waicolle::Player", 0) > 0:
            print()
            print("🎮 WAICOLLE PLAYERS")
            print("-" * 80)
            players = await edgedb.query(
                """
                SELECT waicolle::Player {
                    user: {
                        discord_username,
                    },
                    moecoins,
                    blood_shards,
                    game_mode,
                }
                LIMIT <int64>$limit
                """,
                limit=args.limit,
            )
            for player in players:
                print(
                    f"  {player.user.discord_username}: "
                    f"{player.moecoins} coins, {player.blood_shards} shards, "
                    f"mode={player.game_mode}"
                )

        # AniList Media
        if counts.get("anilist::Media", 0) > 0:
            print()
            print("📺 ANILIST MEDIA")
            print("-" * 80)
            media = await edgedb.query(
                """
                SELECT anilist::Media {
                    title_user_preferred,
                    type,
                }
                LIMIT <int64>$limit
                """,
                limit=args.limit,
            )
            for m in media:
                print(f"  [{m.type}] {m.title_user_preferred}")

    else:
        print()
        print("💡 Run with --details flag to see sample data from each table")

    print()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        sys.exit(1)

