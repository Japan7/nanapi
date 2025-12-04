#!/usr/bin/env python3
"""
Create t-SNE visualization of users based on their message history.

This tool analyzes message content to create a 2D visualization showing how similar
users are in their communication patterns using TF-IDF and t-SNE dimensionality reduction.

Users who use similar vocabulary and writing styles will appear closer together in the
visualization, while users with distinctive communication patterns will be farther apart.

Usage:
    uv run scripts/visualize_user_tsne.py --guild-id "123456789"
    uv run scripts/visualize_user_tsne.py --guild-id "123456789" --min-messages 100
    uv run scripts/visualize_user_tsne.py --days 90 --output user_tsne.html
"""

import asyncio
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

import numpy as np
import plotly.graph_objects as go
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.manifold import TSNE

from nanapi.database.discord.message_word_frequency import message_word_frequency
from nanapi.utils.clients import get_edgedb
from nanapi.utils.word_frequency import extract_words, compute_user_signatures


def prepare_user_documents(messages: List, min_user_messages: int = 50) -> Dict[str, Dict]:
    """
    Prepare user documents for TF-IDF vectorization.
    
    Args:
        messages: List of message objects with content and author_id
        min_user_messages: Minimum messages a user must have
        
    Returns:
        Dictionary mapping user_id to their data:
        {
            'user_id': {
                'document': str,  # All messages concatenated
                'message_count': int,
                'messages': list,
            }
        }
    """
    # Group messages by user
    user_messages = defaultdict(list)
    for msg in messages:
        user_messages[msg.author_id].append(msg)
    
    # Prepare documents
    user_documents = {}
    for user_id, msgs in user_messages.items():
        if len(msgs) < min_user_messages:
            continue
        
        # Concatenate all user messages into a single document
        # Extract words to normalize the text (lowercase, remove stopwords, etc.)
        all_words = []
        for msg in msgs:
            words = extract_words(msg.content)
            all_words.extend(words)
        
        # Create document as space-separated words
        document = ' '.join(all_words)
        
        user_documents[user_id] = {
            'document': document,
            'message_count': len(msgs),
            'messages': msgs,
        }
    
    return user_documents


def compute_tfidf_features(user_documents: Dict[str, Dict]) -> tuple:
    """
    Compute TF-IDF feature vectors for each user.
    
    Args:
        user_documents: Dictionary of user documents from prepare_user_documents
        
    Returns:
        Tuple of (user_ids, tfidf_matrix, feature_names)
    """
    user_ids = list(user_documents.keys())
    documents = [user_documents[uid]['document'] for uid in user_ids]
    
    # Create TF-IDF vectorizer
    vectorizer = TfidfVectorizer(
        max_features=500,  # Limit to top 500 words to avoid sparse matrix issues
        min_df=2,  # Word must appear in at least 2 users
        max_df=0.8,  # Ignore words that appear in more than 80% of users
        token_pattern=r'\b\w+\b',  # Simple word matching
    )
    
    # Fit and transform
    tfidf_matrix = vectorizer.fit_transform(documents)
    feature_names = vectorizer.get_feature_names_out()
    
    return user_ids, tfidf_matrix, feature_names


def apply_tsne(tfidf_matrix, user_ids: List[str], perplexity: int = None) -> np.ndarray:
    """
    Apply t-SNE dimensionality reduction to TF-IDF features.
    
    Args:
        tfidf_matrix: TF-IDF feature matrix
        user_ids: List of user IDs (for determining perplexity)
        perplexity: t-SNE perplexity parameter (auto-calculated if None)
        
    Returns:
        2D numpy array of t-SNE coordinates
    """
    n_users = len(user_ids)
    
    # Adjust perplexity based on number of users
    if perplexity is None:
        # Perplexity should be less than n_samples
        # Common rule: perplexity between 5 and 50
        perplexity = min(30, max(5, n_users - 1))
    
    print(f"Applying t-SNE with perplexity={perplexity} to {n_users} users...", file=sys.stderr)
    
    # Apply t-SNE
    tsne = TSNE(
        n_components=2,
        perplexity=perplexity,
        random_state=42,
        metric='cosine',
        init='random',
        learning_rate='auto',
        max_iter=1000,
    )
    
    # Convert sparse matrix to dense for t-SNE
    tfidf_dense = tfidf_matrix.toarray()
    tsne_coords = tsne.fit_transform(tfidf_dense)
    
    return tsne_coords


def create_plotly_visualization(
    user_ids: List[str],
    tsne_coords: np.ndarray,
    user_documents: Dict[str, Dict],
    user_signatures: Dict = None,
    output_file: str = 'user_tsne_visualization.html',
) -> None:
    """
    Create interactive Plotly visualization of t-SNE results.
    
    Args:
        user_ids: List of user IDs
        tsne_coords: 2D t-SNE coordinates
        user_documents: User document data
        user_signatures: Optional user signature data for enrichment
        output_file: Output HTML file path
    """
    # Prepare hover text and colors
    hover_texts = []
    colors = []
    
    for i, user_id in enumerate(user_ids):
        user_data = user_documents[user_id]
        msg_count = user_data['message_count']
        
        # Build hover text
        hover_parts = [
            f"User: {user_id}",
            f"Messages: {msg_count:,}",
        ]
        
        # Add signature words if available
        if user_signatures and user_id in user_signatures['users']:
            sig_data = user_signatures['users'][user_id]
            distinctiveness = sig_data.get('distinctiveness_score', 0)
            hover_parts.append(f"Distinctiveness: {distinctiveness:.2f}/10")
            
            # Add top 3 signature words
            sig_words = sig_data.get('signature_words', [])[:3]
            if sig_words:
                top_words = ', '.join([w['word'] for w in sig_words])
                hover_parts.append(f"Top words: {top_words}")
            
            # Use distinctiveness for color
            colors.append(distinctiveness)
        else:
            # Use message count for color
            colors.append(msg_count)
        
        hover_texts.append('<br>'.join(hover_parts))
    
    # Create scatter plot
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=tsne_coords[:, 0],
        y=tsne_coords[:, 1],
        mode='markers+text',
        marker=dict(
            size=10,
            color=colors,
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(
                title=dict(
                    text='Distinctiveness' if user_signatures else 'Messages',
                    side='right'
                )
            ),
            line=dict(width=0.5, color='white')
        ),
        text=[uid[:8] for uid in user_ids],  # Short user ID for labels
        textposition='top center',
        textfont=dict(size=8),
        hovertext=hover_texts,
        hoverinfo='text',
    ))
    
    # Update layout
    fig.update_layout(
        title=dict(
            text='User Communication Patterns - t-SNE Visualization',
            font=dict(size=20)
        ),
        xaxis=dict(
            title='t-SNE Dimension 1',
            showgrid=True,
            zeroline=True
        ),
        yaxis=dict(
            title='t-SNE Dimension 2',
            showgrid=True,
            zeroline=True
        ),
        hovermode='closest',
        width=1200,
        height=800,
        plot_bgcolor='rgba(240, 240, 240, 0.9)',
        showlegend=False,
    )
    
    # Save to HTML
    fig.write_html(output_file, include_plotlyjs='cdn')
    print(f"\n✓ Visualization saved to: {output_file}", file=sys.stderr)


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Create t-SNE visualization of users based on message history',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --guild-id "123456789"
  %(prog)s --guild-id "123456789" --min-messages 100 --output user_tsne.html
  %(prog)s --days 90 --perplexity 20
        """
    )
    
    parser.add_argument('--guild-id', type=str, help='Guild/server ID to analyze')
    parser.add_argument('--channel-id', type=str, help='Specific channel ID (optional)')
    parser.add_argument('--days', type=int, default=90, help='Number of days to analyze (default: 90)')
    parser.add_argument('--min-messages', type=int, default=50,
                       help='Minimum messages per user (default: 50)')
    parser.add_argument('--perplexity', type=int, default=None,
                       help='t-SNE perplexity parameter (auto-calculated if not specified)')
    parser.add_argument('--output', '-o', default='user_tsne_visualization.html',
                       help='Output HTML file (default: user_tsne_visualization.html)')
    parser.add_argument('--no-signatures', action='store_true',
                       help='Skip signature word analysis (faster but less informative)')
    
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
    
    # Prepare user documents
    print(f"Preparing user documents (min {args.min_messages} messages)...", file=sys.stderr)
    user_documents = prepare_user_documents(messages, min_user_messages=args.min_messages)
    
    if len(user_documents) < 2:
        print(f"Error: Need at least 2 users with {args.min_messages}+ messages. Found: {len(user_documents)}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Found {len(user_documents)} users with sufficient messages", file=sys.stderr)
    
    # Compute TF-IDF features
    print("Computing TF-IDF features...", file=sys.stderr)
    user_ids, tfidf_matrix, feature_names = compute_tfidf_features(user_documents)
    print(f"Feature matrix shape: {tfidf_matrix.shape} ({len(feature_names)} features)", file=sys.stderr)
    
    # Apply t-SNE
    tsne_coords = apply_tsne(tfidf_matrix, user_ids, perplexity=args.perplexity)
    print("✓ t-SNE complete", file=sys.stderr)
    
    # Optionally compute user signatures for enriched visualization
    user_signatures = None
    if not args.no_signatures:
        print("\nComputing user signatures for enriched visualization...", file=sys.stderr)
        user_signatures = compute_user_signatures(
            messages,
            min_user_messages=args.min_messages,
            min_word_occurrences=5,
            top_n_per_user=5,
        )
        print("✓ Signatures computed", file=sys.stderr)
    
    # Create visualization
    print("\nCreating interactive visualization...", file=sys.stderr)
    create_plotly_visualization(
        user_ids,
        tsne_coords,
        user_documents,
        user_signatures,
        output_file=args.output,
    )
    
    # Print summary
    print("\n" + "=" * 80, file=sys.stderr)
    print("SUMMARY", file=sys.stderr)
    print("=" * 80, file=sys.stderr)
    print(f"Total messages: {len(messages):,}", file=sys.stderr)
    print(f"Users visualized: {len(user_ids)}", file=sys.stderr)
    print(f"Features used: {len(feature_names)}", file=sys.stderr)
    print(f"Output file: {args.output}", file=sys.stderr)
    print("\nOpen the HTML file in a browser to explore the visualization!", file=sys.stderr)
    print("Users closer together have similar communication patterns.", file=sys.stderr)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user.", file=sys.stderr)
        sys.exit(1)

