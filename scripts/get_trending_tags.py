"""
scripts/get_trending_tags.py — Google Trends Tag Injector

Fetches trending search topics in the USA for self-improvement/motivation
and returns a list of tags to mix into every video upload.

Uses pytrends (unofficial Google Trends API wrapper).
Falls back to a curated evergreen list if Trends is unavailable or rate-limited.

Usage:
    from scripts.get_trending_tags import get_trending_tags
    trending = get_trending_tags(category="mindset")
    tags = base_tags + trending
"""

import json
import os
import time
from datetime import datetime, timedelta

# Cache file — avoid hammering Google Trends on every run
CACHE_FILE  = "trending_tags_cache.json"
CACHE_HOURS = 6  # Refresh every 6 hours


# ── Evergreen fallback list ───────────────────────────────────────────
# High-performing self-improvement keywords that consistently trend on YT Shorts.
# Updated for 2024-2025 niche trends.

EVERGREEN_TAGS = {
    "discipline_habits": [
        "atomic habits", "james clear", "75 hard challenge",
        "morning routine 2024", "discipline over motivation",
        "jocko willink discipline", "no zero days", "habit stacking",
    ],
    "mental_strength": [
        "david goggins", "cant hurt me", "mental toughness training",
        "stoic mindset", "jordan peterson mindset", "emotional resilience",
        "overcome anxiety naturally", "inner peace mindset",
    ],
    "success_mindset": [
        "alex hormozi", "100m offers", "billionaire morning routine",
        "andrew huberman", "dopamine detox", "delayed gratification",
        "robert kiyosaki mindset", "think and grow rich",
    ],
    "life_philosophy": [
        "marcus aurelius", "meditations stoicism", "epictetus stoicism",
        "ryan holiday", "the obstacle is the way", "stoicism 2024",
        "modern stoicism", "stoic daily habits",
    ],
    "overcoming_failure": [
        "david goggins 4x4x48", "comeback mindset", "reset and restart",
        "starting over at 30", "failure is not final", "grit angela duckworth",
        "rising strong brene brown", "resilience mindset 2024",
    ],
    "focus_productivity": [
        "cal newport deep work", "flow state secrets", "dopamine detox tips",
        "andrew huberman focus", "brain rewiring habits", "digital minimalism",
        "focus without distraction", "productivity 2024",
    ],
    "general": [
        "atomic habits", "david goggins", "stoicism", "self improvement 2024",
        "alex hormozi", "james clear", "morning routine", "discipline mindset",
        "mental toughness", "success secrets 2024", "financial freedom mindset",
        "jocko willink", "andrew huberman", "ryan holiday",
    ],
}


def _load_cache():
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_cache(data):
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def _cache_is_fresh(cache, category):
    """Return True if cached data for category is less than CACHE_HOURS old."""
    entry = cache.get(category, {})
    ts_str = entry.get("timestamp")
    if not ts_str:
        return False
    try:
        ts = datetime.fromisoformat(ts_str)
        return datetime.now() - ts < timedelta(hours=CACHE_HOURS)
    except Exception:
        return False


def _fetch_from_pytrends(category="general"):
    """
    Use pytrends to fetch trending USA searches related to self-improvement.
    Returns a list of relevant trending terms (max 10).
    Raises ImportError if pytrends not installed, Exception on API errors.
    """
    from pytrends.request import TrendReq

    # Map our categories to Google Trends topic keywords
    seed_keywords = {
        "discipline_habits":  ["discipline", "morning routine", "daily habits"],
        "mental_strength":    ["mental strength", "mindset", "mental health"],
        "success_mindset":    ["success mindset", "wealth", "billionaire habits"],
        "life_philosophy":    ["stoicism", "life philosophy", "purpose"],
        "overcoming_failure": ["overcoming failure", "resilience", "bounce back"],
        "focus_productivity": ["focus", "productivity", "deep work"],
        "general":            ["self improvement", "motivation", "mindset"],
    }
    seeds = seed_keywords.get(category, seed_keywords["general"])

    pytrends = TrendReq(hl="en-US", tz=300, timeout=(10, 25), retries=2, backoff_factor=0.5)
    pytrends.build_payload(seeds, cat=0, timeframe="now 7-d", geo="US")

    # Get related queries (rising = trending now)
    related = pytrends.related_queries()

    tags = []
    for kw in seeds:
        try:
            rising_df = related.get(kw, {}).get("rising")
            if rising_df is not None and not rising_df.empty:
                for term in rising_df["query"].head(4).tolist():
                    term_clean = term.lower().strip()
                    if len(term_clean) < 50 and term_clean not in tags:
                        tags.append(term_clean)
        except Exception:
            continue
        if len(tags) >= 10:
            break

    return tags[:10]


def get_trending_tags(category="general"):
    """
    Return a list of 8-10 trending keyword tags for the given content category.

    Strategy:
    1. Check cache — if fresh (< 6h), return cached tags
    2. Try pytrends Google Trends API for live trending data
    3. Fall back to curated evergreen list if pytrends fails or isn't installed

    Args:
        category: One of discipline_habits, mental_strength, success_mindset,
                  life_philosophy, overcoming_failure, focus_productivity, general

    Returns:
        List of 8-10 lowercase tag strings
    """
    cache = _load_cache()

    # 1 — Cache hit
    if _cache_is_fresh(cache, category):
        tags = cache[category].get("tags", [])
        if tags:
            print(f"  Trending tags: loaded from cache ({len(tags)} tags)")
            return tags

    # 2 — Try pytrends
    try:
        print(f"  Trending tags: fetching from Google Trends (category: {category})...")
        tags = _fetch_from_pytrends(category)
        if tags:
            cache[category] = {"tags": tags, "timestamp": datetime.now().isoformat()}
            _save_cache(cache)
            print(f"  Trending tags: {tags[:5]}...")
            return tags
    except ImportError:
        print("  Trending tags: pytrends not installed — using evergreen list")
    except Exception as e:
        print(f"  Trending tags: pytrends failed ({type(e).__name__}) — using evergreen list")

    # 3 — Evergreen fallback
    fallback = EVERGREEN_TAGS.get(category, EVERGREEN_TAGS["general"])
    # Rotate through fallback list to add variety
    import random
    selected = random.sample(fallback, min(8, len(fallback)))

    # Cache the fallback too (shorter TTL implicitly — only 6h)
    cache[category] = {"tags": selected, "timestamp": datetime.now().isoformat()}
    _save_cache(cache)

    print(f"  Trending tags: using evergreen list ({len(selected)} tags)")
    return selected


if __name__ == "__main__":
    # Quick test
    for cat in ["discipline_habits", "success_mindset", "general"]:
        print(f"\nCategory: {cat}")
        tags = get_trending_tags(cat)
        print(f"Tags: {tags}")
