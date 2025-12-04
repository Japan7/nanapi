"""
Word frequency analysis for finding potential trigger words.

This module provides statistical analysis of message content to identify
words that are used significantly more often in the community compared
to typical usage patterns.
"""

import re
from collections import Counter
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel

# Common French/English stopwords and very common words to exclude
STOPWORDS = {
    # French
    'le', 'la', 'les', 'un', 'une', 'des', 'de', 'du', 'et', 'ou', 'mais',
    'est', 'sont', 'a', 'ai', 'as', 'ont', 'eu', 'été', 'être', 'avoir',
    'pour', 'par', 'sur', 'dans', 'avec', 'sans', 'sous', 'ce', 'cet',
    'cette', 'ces', 'mon', 'ton', 'son', 'ma', 'ta', 'sa', 'mes', 'tes',
    'ses', 'notre', 'votre', 'leur', 'nos', 'vos', 'leurs', 'je', 'tu',
    'il', 'elle', 'nous', 'vous', 'ils', 'elles', 'qui', 'que', 'quoi',
    'dont', 'où', 'si', 'oui', 'non', 'ne', 'pas', 'plus', 'moins',
    'très', 'trop', 'peu', 'beaucoup', 'tout', 'toute', 'tous', 'toutes',
    'ça', 'cela', 'là', 'ici', 'alors', 'donc', 'car', 'comme', 'quand',
    'y', 'en', 'se', "c'est", 'cest', 'il y a', 'y a', 'ya',
    # English
    'the', 'be', 'to', 'of', 'and', 'in', 'that', 'have', 'it', 'for',
    'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at', 'this', 'but',
    'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she', 'or', 'an',
    'will', 'my', 'one', 'all', 'would', 'there', 'their', 'what', 'so',
    'up', 'out', 'if', 'about', 'who', 'get', 'which', 'go', 'me', 'when',
    'make', 'can', 'like', 'time', 'no', 'just', 'him', 'know', 'take',
    'people', 'into', 'year', 'your', 'good', 'some', 'could', 'them',
    'see', 'other', 'than', 'then', 'now', 'look', 'only', 'come', 'its',
    'over', 'think', 'also', 'back', 'after', 'use', 'two', 'how', 'our',
    'work', 'first', 'well', 'way', 'even', 'new', 'want', 'because',
    'any', 'these', 'give', 'day', 'most', 'us', 'is', 'was', 'are',
    'been', 'has', 'had', 'were', 'am', 'did', 'does', "don't", 'didnt',
    'doesnt', 'dont', 'im', 'ive', 'youre', 'wont', 'cant', 'isnt',
}

# Discord-specific patterns to ignore
DISCORD_PATTERNS = [
    r'<@!?\d+>',  # User mentions
    r'<#\d+>',  # Channel mentions
    r'<@&\d+>',  # Role mentions
    r'<a?:\w+:\d+>',  # Custom emojis
    r'https?://\S+',  # URLs
]


@dataclass
class WordStats:
    """Statistics for a single word."""
    word: str
    count: int
    message_count: int  # Number of messages containing this word
    frequency: float  # Occurrences per message
    unique_users: int  # Number of unique users who used this word


class WordFrequencyAnalysis(BaseModel):
    """Results of word frequency analysis."""
    total_messages: int
    total_words: int
    unique_words: int
    top_words: list[dict[str, Any]]  # Top words with their stats
    suggested_triggers: list[dict[str, Any]]  # Words that might make good triggers


def clean_content(content: str) -> str:
    """Clean message content by removing Discord-specific patterns."""
    text = content
    for pattern in DISCORD_PATTERNS:
        text = re.sub(pattern, '', text)
    return text


def extract_words(content: str, min_length: int = 2) -> list[str]:
    """
    Extract words from message content.
    
    Handles:
    - Regular words
    - Discord emoji patterns (e.g., :emoji:)
    - Removes punctuation except in emojis
    """
    cleaned = clean_content(content)
    
    # Extract Discord emoji patterns separately
    emojis = re.findall(r':\w+:', cleaned)
    
    # Remove emoji patterns and extract regular words
    text_without_emojis = re.sub(r':\w+:', ' ', cleaned)
    words = re.findall(r'\b\w+\b', text_without_emojis.lower())
    
    # Filter words
    filtered_words = [
        w for w in words 
        if len(w) >= min_length 
        and w not in STOPWORDS
        and not w.isdigit()
    ]
    
    # Add emojis back
    filtered_emojis = [e.lower() for e in emojis if len(e) > 2]
    
    return filtered_words + filtered_emojis


def analyze_word_frequency(
    messages: list[Any],
    min_occurrences: int = 10,
    min_users: int = 2,
    top_n: int = 100,
) -> WordFrequencyAnalysis:
    """
    Analyze word frequency in messages to find community-specific words.
    
    Args:
        messages: List of message objects with 'content' attribute
        min_occurrences: Minimum number of times a word must appear
        min_users: Minimum number of unique users who must use the word
        top_n: Number of top words to return
    
    Returns:
        WordFrequencyAnalysis with statistics and suggestions
    """
    if not messages:
        return WordFrequencyAnalysis(
            total_messages=0,
            total_words=0,
            unique_words=0,
            top_words=[],
            suggested_triggers=[],
        )
    
    # Track word occurrences
    word_counts: Counter[str] = Counter()
    word_message_counts: Counter[str] = Counter()
    word_users: dict[str, set[str]] = {}
    total_words = 0
    
    for msg in messages:
        words_in_message = set()
        words = extract_words(msg.content)
        total_words += len(words)
        
        for word in words:
            word_counts[word] += 1
            words_in_message.add(word)
            
            # Track unique users (using author_id if available)
            author_id = getattr(msg, 'author_id', None)
            if author_id:
                if word not in word_users:
                    word_users[word] = set()
                word_users[word].add(author_id)
        
        # Count messages containing each word
        for word in words_in_message:
            word_message_counts[word] += 1
    
    # Calculate statistics for each word
    word_stats_list: list[WordStats] = []
    for word, count in word_counts.items():
        if count < min_occurrences:
            continue
        
        unique_users = len(word_users.get(word, set()))
        if unique_users < min_users:
            continue
        
        stats = WordStats(
            word=word,
            count=count,
            message_count=word_message_counts[word],
            frequency=count / len(messages),
            unique_users=unique_users,
        )
        word_stats_list.append(stats)
    
    # Sort by frequency
    word_stats_list.sort(key=lambda x: x.frequency, reverse=True)
    
    # Convert to dict for JSON serialization
    top_words = [
        {
            'word': ws.word,
            'count': ws.count,
            'message_count': ws.message_count,
            'frequency': round(ws.frequency, 4),
            'unique_users': ws.unique_users,
        }
        for ws in word_stats_list[:top_n]
    ]
    
    # Suggest potential triggers
    # Good trigger words are:
    # - Used frequently enough to be interesting
    # - Used by multiple people (not just one person's catchphrase)
    # - Not in the existing triggers (would need to check against conditions.py)
    suggested_triggers = [
        {
            'word': ws.word,
            'count': ws.count,
            'frequency': round(ws.frequency, 4),
            'unique_users': ws.unique_users,
            'score': round(ws.frequency * ws.unique_users, 2),  # Simple scoring
        }
        for ws in word_stats_list
        if 0.05 <= ws.frequency <= 2.0  # Sweet spot: not too rare, not too common
        and ws.unique_users >= 3  # Used by at least 3 people
        and len(ws.word) >= 3  # At least 3 characters
    ]
    
    # Sort suggested triggers by score
    suggested_triggers.sort(key=lambda x: x['score'], reverse=True)
    suggested_triggers = suggested_triggers[:50]  # Top 50 suggestions
    
    return WordFrequencyAnalysis(
        total_messages=len(messages),
        total_words=total_words,
        unique_words=len(word_counts),
        top_words=top_words,
        suggested_triggers=suggested_triggers,
    )


def compute_frequency_discrepancy(
    server_word_counts: dict[str, int],
    irl_frequencies: dict[str, float],
    min_server_occurrences: int = 10,
) -> list[dict[str, any]]:
    """
    Calculate discrepancy between server and IRL word frequencies.
    
    Identifies words that are used significantly more (or less) on the server
    compared to standard language usage patterns.
    
    Args:
        server_word_counts: Dictionary mapping words to occurrence counts on server
        irl_frequencies: Dictionary mapping words to normalized IRL frequencies (0-1)
        min_server_occurrences: Minimum times a word must appear on server
        
    Returns:
        List of dicts with word statistics, sorted by absolute discrepancy.
        Each dict contains:
        - word: The word
        - server_count: Number of times used on server
        - server_freq: Normalized server frequency (0-1)
        - irl_freq: Normalized IRL frequency (0-1)
        - discrepancy: Log ratio of server vs IRL frequency
        - discrepancy_type: Category (server_exclusive, server_heavy, balanced, etc.)
    """
    import math
    
    # Normalize server frequencies
    max_count = max(server_word_counts.values()) if server_word_counts else 1
    server_freq = {word: count / max_count for word, count in server_word_counts.items()}
    
    results = []
    
    # Analyze words used on server
    for word, count in server_word_counts.items():
        if count < min_server_occurrences:
            continue
        
        s_freq = server_freq[word]
        i_freq = irl_frequencies.get(word, 0.0)
        
        if i_freq == 0:
            # Server exclusive - not in IRL top words
            discrepancy = s_freq * 10.0  # Amplify server-only words
            disc_type = 'server_exclusive'
        else:
            # Calculate log ratio
            ratio = (s_freq + 0.0001) / (i_freq + 0.0001)
            discrepancy = math.log10(ratio)
            
            if discrepancy > 1.0:
                disc_type = 'server_heavy'
            elif discrepancy < -1.0:
                disc_type = 'irl_heavy'
            else:
                disc_type = 'balanced'
        
        results.append({
            'word': word,
            'server_count': count,
            'server_freq': round(s_freq, 6),
            'irl_freq': round(i_freq, 6),
            'discrepancy': round(discrepancy, 4),
            'discrepancy_type': disc_type,
        })
    
    # Add common IRL words not used on server
    for word, i_freq in irl_frequencies.items():
        if word not in server_freq and i_freq > 0.1:  # Only very common IRL words
            discrepancy = -5.0 * i_freq
            results.append({
                'word': word,
                'server_count': 0,
                'server_freq': 0.0,
                'irl_freq': round(i_freq, 6),
                'discrepancy': round(discrepancy, 4),
                'discrepancy_type': 'irl_exclusive',
            })
    
    # Sort by absolute discrepancy
    results.sort(key=lambda x: abs(x['discrepancy']), reverse=True)
    
    return results


def compute_user_signatures(
    messages: list[Any],
    min_user_messages: int = 50,
    min_word_occurrences: int = 5,
    top_n_per_user: int = 20,
) -> dict[str, any]:
    """
    Compute signature words for each user by comparing against community average.
    
    Identifies words that are uniquely characteristic of individual users - their
    catchphrases, favorite expressions, and distinctive language patterns.
    
    Args:
        messages: List of message objects with content and author_id attributes
        min_user_messages: Minimum messages a user must have to be analyzed
        min_word_occurrences: Minimum times a word must appear for a user
        top_n_per_user: Number of top signature words to return per user
        
    Returns:
        Dictionary with community stats and per-user signature words:
        {
            'community_stats': {
                'total_messages': int,
                'total_words': int,
                'unique_words': int,
                'users_analyzed': int,
            },
            'users': {
                'user_id': {
                    'message_count': int,
                    'total_words': int,
                    'unique_words': int,
                    'signature_words': [
                        {
                            'word': str,
                            'user_count': int,
                            'user_freq': float,
                            'community_freq': float,
                            'discrepancy': float,
                        },
                        ...
                    ],
                    'distinctiveness_score': float,  # 0-10 scale
                },
                ...
            }
        }
    """
    import math
    from collections import defaultdict
    
    # Group messages by user
    user_messages = defaultdict(list)
    for msg in messages:
        author_id = getattr(msg, 'author_id', None)
        if author_id:
            user_messages[author_id].append(msg)
    
    # Calculate community average frequencies
    community_word_counts: Counter[str] = Counter()
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
        user_word_counts: Counter[str] = Counter()
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
                    'user_freq': round(user_freq, 6),
                    'community_freq': round(comm_freq, 6),
                    'discrepancy': round(discrepancy, 4),
                })
        
        # Sort by discrepancy score
        signature_words.sort(key=lambda x: x['discrepancy'], reverse=True)
        
        # Calculate distinctiveness score (0-10)
        if signature_words:
            avg_discrepancy = sum(w['discrepancy'] for w in signature_words[:10]) / min(10, len(signature_words))
            distinctiveness = min(10.0, avg_discrepancy * 2)
        else:
            distinctiveness = 0.0
        
        user_signatures[user_id] = {
            'user_id': user_id,
            'message_count': len(msgs),
            'total_words': user_total_words,
            'unique_words': len(user_word_counts),
            'signature_words': signature_words[:top_n_per_user],
            'distinctiveness_score': round(distinctiveness, 2),
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

