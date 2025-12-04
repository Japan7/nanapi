"""
User-specific word analysis to identify characteristic words.

This module provides analysis to find words that are particularly used by
a specific user compared to the rest of the community.
"""

from collections import Counter
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel

from nanapi.utils.word_frequency import STOPWORDS, extract_words


@dataclass
class UserWordScore:
    """Score for how characteristic a word is to a user."""
    word: str
    user_count: int  # Times the user said it
    user_frequency: float  # User's frequency
    community_count: int  # Times others said it
    community_frequency: float  # Others' frequency
    ratio: float  # user_freq / community_freq (higher = more characteristic)
    uniqueness_score: float  # Combined metric


class UserWordAnalysis(BaseModel):
    """Results of user-specific word analysis."""
    user_id: str
    user_messages: int
    community_messages: int
    user_total_words: int
    community_total_words: int
    characteristic_words: list[dict[str, Any]]  # Words characteristic of this user
    unique_words: list[dict[str, Any]]  # Words only (or mostly) this user uses
    comparison_summary: dict[str, Any]


def analyze_user_words(
    messages: list[Any],
    user_id: str,
    min_user_count: int = 5,
    min_ratio: float = 2.0,
    top_n: int = 50,
) -> UserWordAnalysis:
    """
    Analyze words characteristic to a specific user.
    
    Identifies words that this user uses significantly more than the rest
    of the community, revealing their unique speech patterns.
    
    Args:
        messages: List of message objects with 'content' and 'author_id'
        user_id: The user ID to analyze
        min_user_count: Minimum times the user must use a word
        min_ratio: Minimum ratio of user_freq/community_freq to be considered characteristic
        top_n: Number of top words to return
    
    Returns:
        UserWordAnalysis with the user's characteristic words
    """
    # Separate user messages from community messages
    user_messages_list = [m for m in messages if m.author_id == user_id]
    community_messages_list = [m for m in messages if m.author_id != user_id]
    
    if not user_messages_list:
        return UserWordAnalysis(
            user_id=user_id,
            user_messages=0,
            community_messages=len(community_messages_list),
            user_total_words=0,
            community_total_words=0,
            characteristic_words=[],
            unique_words=[],
            comparison_summary={},
        )
    
    # Extract words from user's messages
    user_word_counts: Counter[str] = Counter()
    user_total_words = 0
    
    for msg in user_messages_list:
        words = extract_words(msg.content)
        user_total_words += len(words)
        for word in words:
            user_word_counts[word] += 1
    
    # Extract words from community messages
    community_word_counts: Counter[str] = Counter()
    community_total_words = 0
    
    for msg in community_messages_list:
        words = extract_words(msg.content)
        community_total_words += len(words)
        for word in words:
            community_word_counts[word] += 1
    
    # Calculate scores for each word
    word_scores: list[UserWordScore] = []
    
    for word, user_count in user_word_counts.items():
        if user_count < min_user_count:
            continue
        
        community_count = community_word_counts.get(word, 0)
        
        # Calculate frequencies
        user_freq = user_count / len(user_messages_list) if user_messages_list else 0
        community_freq = (
            community_count / len(community_messages_list) 
            if community_messages_list else 0.0001
        )
        
        # Avoid division by zero
        if community_freq == 0:
            community_freq = 0.0001
        
        ratio = user_freq / community_freq
        
        # Calculate a uniqueness score that balances frequency and ratio
        # Higher score = more characteristic of this user
        # Formula: log(ratio) * user_count
        # This favors words used often by the user with high ratio
        import math
        uniqueness_score = math.log(ratio + 1) * user_count
        
        word_scores.append(UserWordScore(
            word=word,
            user_count=user_count,
            user_frequency=user_freq,
            community_count=community_count,
            community_frequency=community_freq,
            ratio=ratio,
            uniqueness_score=uniqueness_score,
        ))
    
    # Sort by uniqueness score
    word_scores.sort(key=lambda x: x.uniqueness_score, reverse=True)
    
    # Separate into characteristic (high ratio) and unique (exclusive) words
    characteristic = [
        ws for ws in word_scores 
        if ws.ratio >= min_ratio
    ]
    
    unique = [
        ws for ws in word_scores
        if ws.community_count <= 2  # Used by very few others
    ]
    
    # Convert to dict for JSON serialization
    characteristic_words = [
        {
            'word': ws.word,
            'user_count': ws.user_count,
            'user_frequency': round(ws.user_frequency, 4),
            'community_count': ws.community_count,
            'community_frequency': round(ws.community_frequency, 4),
            'ratio': round(ws.ratio, 2),
            'uniqueness_score': round(ws.uniqueness_score, 2),
        }
        for ws in characteristic[:top_n]
    ]
    
    unique_words = [
        {
            'word': ws.word,
            'user_count': ws.user_count,
            'user_frequency': round(ws.user_frequency, 4),
            'community_count': ws.community_count,
        }
        for ws in unique[:top_n]
    ]
    
    # Calculate vocabulary overlap
    user_vocab = set(user_word_counts.keys())
    community_vocab = set(community_word_counts.keys())
    shared_vocab = user_vocab & community_vocab
    exclusive_vocab = user_vocab - community_vocab
    
    comparison_summary = {
        'user_vocabulary_size': len(user_vocab),
        'community_vocabulary_size': len(community_vocab),
        'shared_words': len(shared_vocab),
        'user_exclusive_words': len(exclusive_vocab),
        'vocabulary_overlap_percent': round(
            len(shared_vocab) / len(user_vocab) * 100 if user_vocab else 0, 
            2
        ),
        'avg_message_length': round(
            user_total_words / len(user_messages_list) if user_messages_list else 0,
            2
        ),
        'community_avg_message_length': round(
            community_total_words / len(community_messages_list) if community_messages_list else 0,
            2
        ),
    }
    
    return UserWordAnalysis(
        user_id=user_id,
        user_messages=len(user_messages_list),
        community_messages=len(community_messages_list),
        user_total_words=user_total_words,
        community_total_words=community_total_words,
        characteristic_words=characteristic_words,
        unique_words=unique_words,
        comparison_summary=comparison_summary,
    )


def compare_users(
    messages: list[Any],
    user_ids: list[str],
    min_count: int = 5,
) -> dict[str, Any]:
    """
    Compare word usage across multiple users.
    
    Args:
        messages: List of message objects
        user_ids: List of user IDs to compare
        min_count: Minimum word count to include
    
    Returns:
        Dictionary with comparison data for each user
    """
    results = {}
    
    for user_id in user_ids:
        analysis = analyze_user_words(
            messages,
            user_id,
            min_user_count=min_count,
        )
        results[user_id] = analysis
    
    return results

