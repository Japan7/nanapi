# Word Frequency Analysis Guide

A comprehensive guide to understanding and using the word frequency analysis system for Discord message analysis.

## Table of Contents

1. [Overview](#overview)
2. [Core Concepts](#core-concepts)
3. [System Architecture](#system-architecture)
4. [Analysis Types](#analysis-types)
5. [How It Works](#how-it-works)
6. [Usage Examples](#usage-examples)
7. [Understanding the Results](#understanding-the-results)

---

## Overview

The word frequency analysis system analyzes Discord message history to identify statistically significant patterns in word usage. It's designed to:

- **Find community-specific vocabulary** (server slang, inside jokes)
- **Identify user-specific speech patterns** (catchphrases, signature words)
- **Compare server language to real-world usage** (formal vs casual)
- **Suggest trigger words** for conditional game mechanics (e.g., WaiColle drops)

---

## Core Concepts

### 1. Word Extraction & Normalization

**What it does:**
- Extracts individual words from Discord messages
- Cleans and normalizes text for analysis
- Removes noise while preserving meaningful content

**How it works:**

```python
def extract_words(content: str, min_length: int = 2) -> list[str]:
    """
    Extracts meaningful words from message content.
    """
```

**Processing steps:**

1. **Clean Discord-specific patterns:**
   - User mentions: `<@123456789>` → removed
   - Channel mentions: `<#123456789>` → removed
   - Custom emojis: `<:emoji:123456789>` → removed
   - URLs: `https://example.com` → removed

2. **Extract words:**
   - Discord text emojis: `:thinking:` → kept as-is
   - Regular words: lowercased and extracted
   - Minimum length filter (default: 2 characters)

3. **Filter stopwords:**
   - Common words removed (le, la, the, and, etc.)
   - ~50 French stopwords
   - ~50 English stopwords
   - Numbers excluded

**Example:**
```
Input:  "Hey @user check this https://example.com :thinking: c'est super cool!"
Output: ["hey", "check", ":thinking:", "super", "cool"]
         (removed: @user, URL, "c'est")
```

---

### 2. Frequency Metrics

The system calculates several frequency metrics:

#### **Raw Count**
Number of times a word appears in all messages.
```
"pog" appears 1,234 times
```

#### **Message Frequency**
Occurrences per message (normalized).
```
frequency = word_count / total_messages
"pog": 1234 / 10000 = 0.1234 (appears in ~12% of messages)
```

#### **User Frequency**
For individual users, frequency per their messages.
```
user_frequency = user_word_count / user_messages
User A says "pog" 50 times in 100 messages = 0.50
```

#### **Unique Users**
Number of different users who used the word.
```
"pog" used by 25 unique users
```

---

### 3. Statistical Comparison

The system compares frequencies across different contexts:

#### **User vs Community**
Compares one user's usage to everyone else's usage.
```
User says "pog" 0.50 times per message
Community says "pog" 0.05 times per message
Ratio: 10x (user says it 10 times more often)
```

#### **Server vs IRL**
Compares server usage to real-world language frequency.
```
Server: "mdr" appears with frequency 0.80
IRL French: "mdr" not in top 5000 words (0.0)
Discrepancy: +10.0 (server-exclusive slang)
```

---

## System Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Data Layer                              │
│  ┌──────────────────┐         ┌──────────────────┐        │
│  │  EdgeDB Query    │────────▶│  Message Objects │        │
│  │  (message_word_  │         │  - content       │        │
│  │   frequency.py)  │         │  - author_id     │        │
│  └──────────────────┘         │  - timestamp     │        │
│                                └──────────────────┘        │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  Processing Layer                           │
│  ┌──────────────────────────────────────────────┐          │
│  │         word_frequency.py                    │          │
│  │  - extract_words()                          │          │
│  │  - analyze_word_frequency()                 │          │
│  │  - compute_frequency_discrepancy()          │          │
│  └──────────────────────────────────────────────┘          │
│  ┌──────────────────────────────────────────────┐          │
│  │       user_word_analysis.py                  │          │
│  │  - analyze_user_words()                     │          │
│  │  - compare_users()                          │          │
│  └──────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Analysis Scripts                          │
│  ┌────────────────────────────────────────┐                │
│  │  analyze_word_frequency.py             │                │
│  │  → Basic frequency analysis            │                │
│  └────────────────────────────────────────┘                │
│  ┌────────────────────────────────────────┐                │
│  │  analyze_user_words.py                 │                │
│  │  → User-specific patterns              │                │
│  └────────────────────────────────────────┘                │
│  ┌────────────────────────────────────────┐                │
│  │  find_frequency_discrepancy.py         │                │
│  │  → Server vs IRL comparison            │                │
│  └────────────────────────────────────────┘                │
│  ┌────────────────────────────────────────┐                │
│  │  find_user_word_signatures.py          │                │
│  │  → Multi-user signature analysis       │                │
│  └────────────────────────────────────────┘                │
│  ┌────────────────────────────────────────┐                │
│  │  visualize_user_tsne.py                │                │
│  │  → Visual clustering with t-SNE        │                │
│  └────────────────────────────────────────┘                │
└─────────────────────────────────────────────────────────────┘
```

### Database Query

**File:** `nanapi/database/discord/message_word_frequency.edgeql`

```edgeql
with
  channel_id := <optional str>$channel_id,
  guild_id := <optional str>$guild_id,
  start_date := <optional datetime>$start_date,
  end_date := <optional datetime>$end_date,
select discord::Message {
  content,
  channel_id,
  guild_id,
  author_id,
  timestamp,
}
filter
  (.channel_id = channel_id if exists channel_id else true) and
  (.guild_id = guild_id if exists guild_id else true) and
  (.timestamp >= start_date if exists start_date else true) and
  (.timestamp <= end_date if exists end_date else true) and
  not exists .deleted_at and
  not exists .noindex and
  len(.content) > 0
order by .timestamp desc
```

**Purpose:** Efficiently fetches messages from the database with flexible filtering options.

---

## Analysis Types

### 1. Basic Frequency Analysis

**Script:** `analyze_word_frequency.py`

**What it finds:**
- Most frequently used words on the server
- Words used by multiple people (not just one person's spam)
- Suggested trigger words for game mechanics

**Algorithm:**

```python
1. Extract all words from messages
2. Count occurrences:
   - word_counts[word] += 1
   - word_message_counts[word] += 1 (per unique message)
   - word_users[word].add(author_id)
3. Filter by thresholds:
   - min_occurrences (default: 10)
   - min_users (default: 2)
4. Calculate frequency = count / total_messages
5. Rank by frequency
6. Suggest triggers in "sweet spot" range (0.05-2.0 frequency)
```

**Output:**
```
Word                      Count  Messages  Frequency  Users
─────────────────────────────────────────────────────────────
pog                       1,234     1,150     0.1234    25
copium                      856       820     0.0856    18
genre                       743       702     0.0743    31
```

---

### 2. User-Specific Analysis

**Script:** `analyze_user_words.py`

**What it finds:**
- Words that define an individual user's speech patterns
- "Signature words" that are characteristic of one person
- User's linguistic uniqueness

**Algorithm:**

```python
1. Split messages into:
   - user_messages (messages from target user)
   - community_messages (messages from everyone else)

2. Calculate frequencies for both groups:
   - user_freq = user_word_count / user_messages
   - community_freq = community_word_count / community_messages

3. Calculate ratio:
   - ratio = user_freq / community_freq
   - Higher ratio = more characteristic of user

4. Calculate uniqueness score:
   - uniqueness_score = log(ratio + 1) * user_count
   - Balances frequency with exclusivity

5. Categorize words:
   - characteristic: ratio >= 2.0 (2x more than others)
   - unique: community_count <= 2 (almost exclusive to user)

6. Sort by uniqueness_score
```

**Example:**
```
User A says "pog" in 30% of their messages
Community says "pog" in 3% of messages
Ratio: 10x
Uniqueness score: log(10) * 150 = 150.0
→ "pog" is highly characteristic of User A
```

---

### 3. Server vs IRL Comparison

**Script:** `find_frequency_discrepancy.py`

**What it finds:**
- Server-exclusive vocabulary (slang, inside jokes)
- Overused words (compared to standard language)
- Underused words (formal language avoided in chat)

**Algorithm:**

```python
1. Load IRL reference frequencies:
   - Top 5000 most common French/English words
   - Normalized to 0-1 scale

2. Compute server frequencies:
   - Same normalization (0-1)

3. Calculate discrepancy for each word:
   
   If word not in IRL list:
     discrepancy = server_freq * 10.0
     type = 'server_exclusive'
   
   If word in both:
     ratio = server_freq / irl_freq
     discrepancy = log10(ratio)
     
     if discrepancy > 1.0:
       type = 'server_heavy'
     elif discrepancy < -1.0:
       type = 'irl_heavy'
     else:
       type = 'balanced'
   
   If common IRL word not on server:
     discrepancy = -5.0 * irl_freq
     type = 'irl_exclusive'

4. Sort by absolute discrepancy
```

**Discrepancy Score Interpretation:**

```
+10.0: Server-exclusive (not in IRL top 5000)
 +2.0: 100x more common on server
 +1.0: 10x more common on server
 +0.5: 3x more common on server
  0.0: Similar usage
 -0.5: 3x less common on server
 -1.0: 10x less common on server
 -5.0: Common IRL but not used on server
```

**Example Output:**
```
Word          Server Freq  IRL Freq  Discrepancy  Type
────────────────────────────────────────────────────────────
qu               1.0000      0.0000      10.00    server_exclusive
ouais            0.5438      0.0000       5.44    server_exclusive
fait             0.8300      0.0237       1.54    server_heavy
le               0.0000      1.0000      -5.00    irl_exclusive
```

---

### 4. User Signature Analysis (Multi-User)

**Script:** `find_user_word_signatures.py`

**What it finds:**
- Signature words for ALL active users
- Distinctiveness ranking (who has the most unique vocabulary)
- Community linguistic diversity

**Algorithm:**

```python
1. Group messages by user_id

2. Calculate community average:
   - community_freq[word] = count / total_community_words

3. For each user:
   - Calculate user_freq[word] = count / user_total_words
   - Compare to community_freq
   - discrepancy = log10(user_freq / community_freq)
   - Keep words with discrepancy > 0.3 (2x more than average)

4. Calculate distinctiveness score (0-10):
   - Average of top 10 word discrepancies * 2
   - Measures overall linguistic uniqueness

5. Rank users by distinctiveness
```

**Distinctiveness Score:**

```
0-2:   Very generic (matches community average)
2-4:   Slightly distinctive
4-6:   Moderately distinctive
6-8:   Highly distinctive
8-10:  Extremely distinctive (very unique vocabulary)
```

---

### 5. Visual Clustering (t-SNE)

**Script:** `visualize_user_tsne.py`

**What it finds:**
- Visual representation of user similarity
- Clusters of users with similar communication styles
- Outliers with unique patterns

**Algorithm:**

```python
1. Create user documents:
   - Concatenate all messages per user
   - Extract and normalize words

2. TF-IDF Vectorization:
   - TF (Term Frequency): How often word appears in user's messages
   - IDF (Inverse Document Frequency): Rarity across all users
   - TF-IDF = TF * IDF (balances frequency with uniqueness)
   
   Parameters:
   - max_features: 500 (top 500 words)
   - min_df: 2 (must appear in 2+ users)
   - max_df: 0.8 (ignore if in >80% of users)

3. t-SNE Dimensionality Reduction:
   - Reduces 500 dimensions → 2 dimensions
   - Preserves local structure (similar users stay close)
   - perplexity: controls cluster density (auto: 5-30)

4. Visualization:
   - Interactive scatter plot
   - Color by distinctiveness or message count
   - Hover shows user info and top words
```

**t-SNE Parameters:**

```
perplexity: 5-50 (higher = looser clusters)
- Small datasets: 5-15
- Medium datasets: 15-30
- Large datasets: 30-50

metric: cosine (measures angle between vectors)
- Good for text analysis
- Ignores magnitude, focuses on direction
```

---

## How It Works: Step-by-Step

### Example: Finding Server-Exclusive Words

Let's walk through a complete analysis:

**Step 1: Fetch Messages**
```python
messages = await message_word_frequency(
    edgedb,
    guild_id="297436883883917312",
    start_date=datetime(2024, 11, 11),
    end_date=datetime(2025, 11, 11),
)
# Result: 197,305 messages
```

**Step 2: Extract Words**
```python
# Message: "du coup on fait quoi mdr"
words = extract_words("du coup on fait quoi mdr")
# Result: ["coup", "fait", "quoi", "mdr"]
#         (removed: "du", "on" - stopwords)
```

**Step 3: Count Frequencies**
```python
word_counts = Counter()
for msg in messages:
    words = extract_words(msg.content)
    word_counts.update(words)

# Results:
word_counts["mdr"] = 3,373
word_counts["pog"] = 1,234
word_counts["genre"] = 743
```

**Step 4: Normalize Frequencies**
```python
total_messages = 197,305
server_freq["mdr"] = 3373 / 197305 = 0.0171
# "mdr" appears in 1.71% of messages
```

**Step 5: Compare to IRL**
```python
irl_freq["mdr"] = 0.0  # Not in French top 5000

discrepancy = server_freq["mdr"] * 10.0
            = 0.0171 * 10.0 
            = 0.171

# But normalize to most common server word:
max_server = word_counts["qu"] = 13,262
normalized = 3373 / 13262 = 0.2543
discrepancy = 0.2543 * 10.0 = 2.54

type = 'server_exclusive'
```

**Step 6: Rank & Report**
```
TOP SERVER-EXCLUSIVE WORDS
───────────────────────────────────────
Word         Server Count  Discrepancy
───────────────────────────────────────
qu                13,262        10.00
ouais              7,212         5.44
mdr                3,373         2.54
pog                1,234         0.93
...
```

---

## Usage Examples

### Example 1: Basic Word Frequency

```bash
# Analyze last 30 days for a guild
uv run scripts/analyze_word_frequency.py --guild-id "123456789"

# Show trigger word suggestions
uv run scripts/analyze_word_frequency.py \
    --guild-id "123456789" \
    --show-suggestions

# Adjust sensitivity
uv run scripts/analyze_word_frequency.py \
    --guild-id "123456789" \
    --min-occurrences 20 \
    --min-users 5 \
    --top-n 100
```

### Example 2: User Analysis

```bash
# Analyze a specific user
uv run scripts/analyze_user_words.py \
    --user-id "987654321" \
    --guild-id "123456789"

# More sensitive detection
uv run scripts/analyze_user_words.py \
    --user-id "987654321" \
    --min-user-count 3 \
    --min-ratio 1.5 \
    --top-n 100
```

### Example 3: Server vs IRL

```bash
# Find server-specific vocabulary
uv run scripts/find_frequency_discrepancy.py \
    --guild-id "123456789" \
    --language french

# Save detailed report
uv run scripts/find_frequency_discrepancy.py \
    --guild-id "123456789" \
    --days 365 \
    --output server_analysis.txt

# Show all categories
uv run scripts/find_frequency_discrepancy.py \
    --guild-id "123456789" \
    --show-balanced \
    --top 200
```

### Example 4: Multi-User Signatures

```bash
# Analyze all active users
uv run scripts/find_user_word_signatures.py \
    --guild-id "123456789"

# Higher thresholds for quality
uv run scripts/find_user_word_signatures.py \
    --guild-id "123456789" \
    --min-messages 100 \
    --min-word-count 10

# JSON output for processing
uv run scripts/find_user_word_signatures.py \
    --guild-id "123456789" \
    --format json \
    --output signatures.json
```

### Example 5: Visual Clustering

```bash
# Create interactive visualization
uv run scripts/visualize_user_tsne.py \
    --guild-id "123456789"

# Adjust clustering
uv run scripts/visualize_user_tsne.py \
    --guild-id "123456789" \
    --perplexity 20 \
    --min-messages 200

# Fast version (skip signatures)
uv run scripts/visualize_user_tsne.py \
    --guild-id "123456789" \
    --no-signatures \
    --output quick_viz.html
```

---

## Understanding the Results

### Frequency Analysis Output

```
WORD FREQUENCY ANALYSIS
═══════════════════════════════════════════════════════════
Total messages: 197,305
Total words: 3,456,789
Unique words: 61,278

TOP MOST FREQUENT WORDS
───────────────────────────────────────────────────────────
Word            Count  Messages  Frequency  Users
───────────────────────────────────────────────────────────
pog             1,234     1,150     0.1234    25
copium            856       820     0.0856    18
genre             743       702     0.0743    31
```

**Interpreting:**
- **Count:** Total occurrences (1,234 times "pog" was said)
- **Messages:** Unique messages containing word (1,150 different messages)
- **Frequency:** Occurrences per message (12.34% of messages have "pog")
- **Users:** Unique users (25 people say "pog")

**Good trigger words:**
- Frequency 0.05-2.0 (not too rare, not too common)
- Users ≥ 3 (multiple people use it)
- Length ≥ 3 (not too short)

---

### User Analysis Output

```
USER WORD ANALYSIS: 987654321
═══════════════════════════════════════════════════════════

📊 MESSAGE STATISTICS
───────────────────────────────────────────────────────────
User's messages:           1,234
Community messages:      196,071
User's total words:       15,678
Community words:       3,441,111

📖 VOCABULARY COMPARISON
───────────────────────────────────────────────────────────
User vocabulary size:          2,345
Community vocabulary size:    61,234
Shared words:                  2,100
User exclusive words:            245
Vocabulary overlap:            89.5%
User avg message length:      12.7 words
Community avg msg length:     17.5 words

🎯 CHARACTERISTIC WORDS
───────────────────────────────────────────────────────────
Word           User  Others  Ratio   Score   User%
───────────────────────────────────────────────────────────
pog             150      84   10.0x  150.0   12.2%
based            45      12   15.0x   67.5    3.6%
```

**Interpreting:**

- **Ratio:** How much more the user says this word
  - 10.0x = User says it 10 times more than community average
  - Higher = more characteristic

- **Score:** Uniqueness metric (higher = more defining)
  - Balances frequency with exclusivity
  - Formula: log(ratio + 1) * user_count

- **User%:** Percentage of user's messages with this word
  - 12.2% = "pog" in 12.2% of their messages

---

### Server vs IRL Output

```
TOP SERVER-EXCLUSIVE WORDS
───────────────────────────────────────────────────────────
These words are used on your server but NOT in top 5000 IRL.
Perfect candidates for server-specific trigger words!

Word           Server Count  Server Freq  Discrepancy
───────────────────────────────────────────────────────────
qu                  13,262       1.0000        10.00
ouais                7,212       0.5438         5.44
mdr                  3,373       0.2543         2.54
pog                  1,234       0.0930         0.93
```

**Interpreting:**

- **Server Freq:** Normalized 0-1 (1.0 = most common)
- **Discrepancy:** Strength of server-exclusivity
  - 10.00 = Maximum (completely server-specific)
  - 5.00+ = Very strong server slang
  - 2.00+ = Notable server vocabulary
  - 0.50+ = Slightly overused

**Categories:**

```
server_exclusive:  Not in IRL top 5000 (slang, inside jokes)
server_heavy:      Used 10x+ more than IRL (overused words)
balanced:          Similar usage (normal vocabulary)
irl_heavy:         Used 10x+ less than IRL (avoided words)
irl_exclusive:     Common IRL but not on server (formal words)
```

---

### Signature Analysis Output

```
MOST DISTINCTIVE USERS
───────────────────────────────────────────────────────────
Rank  User ID        Messages  Distinctiveness  Top Word
───────────────────────────────────────────────────────────
1     user123           1,234            8.45  pog
2     user456             987            7.23  copium
3     user789             856            6.91  based
```

**Distinctiveness Score (0-10):**

```
0-2:   Generic speaker (matches community)
2-4:   Slightly distinctive
4-6:   Moderately distinctive (noticeable patterns)
6-8:   Highly distinctive (clear personal style)
8-10:  Extremely distinctive (very unique vocabulary)
```

---

### t-SNE Visualization

The visualization shows users as points in 2D space:

**Interpretation:**

- **Close points:** Similar communication styles
  - Same vocabulary, similar patterns
  - May form friend groups or communities

- **Distant points:** Different communication styles
  - Unique vocabulary, distinct patterns
  - May be outliers or niche interests

- **Clusters:** Groups with shared language
  - Gaming communities might cluster together
  - French speakers vs English speakers
  - Different activity types (casual chat, technical discussion)

- **Color intensity:** Distinctiveness score
  - Brighter = more unique vocabulary
  - Darker = more generic patterns

**Use cases:**

1. **Find similar users:** Users close together might enjoy similar content
2. **Detect outliers:** Isolated points have very unique styles
3. **Discover communities:** Clusters reveal sub-groups
4. **Track evolution:** Re-run over time to see pattern changes

---

## Advanced Topics

### Customizing Stopwords

Add server-specific stopwords to filter out:

```python
# In word_frequency.py
STOPWORDS.update({
    'bot',  # Your bot's name
    'command',  # Common bot commands
    'help',
})
```

### Adjusting Thresholds

**For rare slang:**
```python
min_occurrences = 5  # Lower threshold
min_users = 1        # Allow one person's words
```

**For common patterns:**
```python
min_occurrences = 50  # Higher threshold
min_users = 10        # Must be widespread
```

### Custom Discrepancy Calculation

Modify the scoring formula:

```python
# More sensitive to server exclusivity
if irl_freq == 0:
    discrepancy = server_freq * 20.0  # Increased from 10.0

# Less sensitive to small differences
threshold = 1.5  # Changed from 1.0 for 'server_heavy'
```

---

## Practical Applications

### 1. Game Trigger Words

Use server-exclusive words for WaiColle conditional drops:

```python
# From analysis results
suggested_triggers = ["pog", "copium", "mdr", "based"]

# Add to conditions.py
Word.simple("pog"),
Word.simple("copium"),
```

### 2. User Profiling

Use signature words for personalization:

```python
user_signature = {
    "user123": ["pog", "based", "gaming"],
    "user456": ["copium", "rip", "sadge"],
}

# Create user-specific triggers or content
```

### 3. Community Health

Monitor linguistic diversity:

```python
# High distinctiveness = diverse community
# Low distinctiveness = echo chamber

avg_distinctiveness = 6.5  # Healthy diversity
```

### 4. Content Moderation

Detect emerging slang or problematic language:

```python
# Sudden spike in new server-exclusive words
# May indicate new trends or issues
```

---

## Troubleshooting

### "No messages found"

**Problem:** Query returns empty results

**Solutions:**
1. Check guild_id is correct
2. Verify date range includes messages
3. Ensure messages aren't deleted/noindexed
4. Try without filters first

### "Insufficient users"

**Problem:** Not enough users for analysis

**Solutions:**
1. Lower `min-messages` threshold
2. Increase date range with `--days`
3. Remove channel filter
4. Check if most users are inactive

### "Poor clustering in t-SNE"

**Problem:** All users clumped together

**Solutions:**
1. Increase `perplexity` (try 30-50)
2. Increase `min-messages` for better user profiles
3. Check if community is linguistically homogeneous
4. Try different `max_features` in TF-IDF

### "Stopwords in results"

**Problem:** Common words like "the" appearing

**Solutions:**
1. Add to STOPWORDS set
2. Check `extract_words()` is being used
3. Verify stopword list is loaded
4. May be language mismatch (French vs English)

---

## Performance Tips

### Large Datasets

**For 1M+ messages:**

1. **Filter early:**
   ```python
   # Use database filters
   --days 30  # Instead of 365
   --channel-id "specific"  # Instead of whole guild
   ```

2. **Limit query results:**
   ```edgeql
   limit 100000  # In EdgeDB query
   ```

3. **Process in batches:**
   ```python
   batch_size = 10000
   for i in range(0, len(messages), batch_size):
       batch = messages[i:i+batch_size]
       process_batch(batch)
   ```

### Memory Optimization

**For limited RAM:**

1. **Stream processing:**
   ```python
   # Process messages as they arrive
   # Don't load all into memory
   ```

2. **Reduce feature space:**
   ```python
   max_features = 100  # Instead of 500
   ```

3. **Filter aggressively:**
   ```python
   min_occurrences = 50  # Higher threshold
   ```

---

## Conclusion

The word frequency analysis system provides powerful tools for understanding Discord community language patterns. By analyzing word usage statistically, it reveals:

- **Community culture** through server-specific vocabulary
- **Individual identity** through user signature words
- **Social structure** through linguistic clustering
- **Engagement opportunities** through trigger word suggestions

**Key takeaways:**

1. **Frequency ≠ Importance:** Most common words may be noise; look for distinctive patterns
2. **Context matters:** Compare against baselines (IRL, community, etc.)
3. **Multiple angles:** Combine different analyses for complete picture
4. **Iterate:** Re-run analyses over time to track evolution

**Next steps:**

1. Run basic frequency analysis on your server
2. Identify top 20 server-exclusive words
3. Analyze most active users' signatures
4. Create visualization to understand community structure
5. Implement findings in game mechanics or content

---

## Reference

### Key Files

```
nanapi/
  database/discord/
    message_word_frequency.edgeql  # Database query
    message_word_frequency.py      # Generated query wrapper
  utils/
    word_frequency.py              # Core frequency analysis
    user_word_analysis.py          # User-specific analysis
  scripts/
    analyze_word_frequency.py      # Basic analysis script
    analyze_user_words.py          # User analysis script
    find_frequency_discrepancy.py  # Server vs IRL script
    find_user_word_signatures.py   # Multi-user script
    visualize_user_tsne.py         # Visualization script
```

### Parameters Quick Reference

```python
# Word extraction
min_length = 2              # Minimum word length

# Frequency analysis
min_occurrences = 10        # Minimum total occurrences
min_users = 2               # Minimum unique users
top_n = 100                 # Number of results

# User analysis
min_user_count = 5          # Minimum per-user occurrences
min_ratio = 2.0             # Minimum user/community ratio

# Discrepancy analysis
min_server_occurrences = 10 # Server word threshold

# Signature analysis
min_user_messages = 50      # Minimum messages per user
min_word_occurrences = 5    # Word occurrence threshold
top_n_per_user = 20         # Signatures per user

# t-SNE visualization
perplexity = 30             # Clustering density (5-50)
max_features = 500          # TF-IDF features
min_df = 2                  # Minimum document frequency
max_df = 0.8                # Maximum document frequency (80%)
```

---

**Version:** 1.0  
**Last Updated:** December 2025  
**Author:** Word Frequency Analysis System
