"""
competitor_analysis.py — YouTube Shorts Competitor Analyzer

Scrapes top-performing Shorts in your niche using the YouTube Data API,
analyzes winning patterns (titles, hooks, tags, descriptions),
and saves insights that feed into the script generation prompt.

What it does:
  1. Searches YouTube for top Shorts in motivation/mindset niche
  2. Pulls title, views, likes, description, tags from top 50 Shorts
  3. Uses Gemini to analyze winning patterns
  4. Saves insights to output/competitor_insights.json
  5. Script generation (02_write_script.py) reads these insights

Usage:
  python scripts/competitor_analysis.py

Requires: GEMINI_API_KEY in .env, credentials.json for YouTube API
"""

import os
import sys
import json
import datetime
from dotenv import load_dotenv

load_dotenv()

try:
    from google import genai
    gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    GEMINI_AVAILABLE = True
except Exception:
    GEMINI_AVAILABLE = False

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]
TEXT_MODEL = "gemini-2.5-flash"

# Search queries for finding top Shorts in our niche
SEARCH_QUERIES = [
    "motivation shorts",
    "self improvement shorts",
    "mindset shorts",
    "discipline motivation",
    "stoic mindset shorts",
    "book summary shorts",
    "success habits shorts",
    "mental strength motivation",
]

INSIGHTS_FILE = "output/competitor_insights.json"


def get_youtube_client():
    creds = None
    if os.path.exists("output/token.json"):
        creds = Credentials.from_authorized_user_file("output/token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                os.getenv("YOUTUBE_CLIENT_SECRET", "credentials.json"),
                SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open("output/token.json", "w") as f:
            f.write(creds.to_json())
    return build("youtube", "v3", credentials=creds)


def search_top_shorts(youtube, query, max_results=10):
    """Search for top Shorts matching a query, sorted by view count."""
    try:
        response = youtube.search().list(
            part="snippet",
            q=query,
            type="video",
            videoDuration="short",    # Under 4 minutes (Shorts are < 60s)
            order="viewCount",
            maxResults=max_results,
            publishedAfter=(
                datetime.datetime.now(datetime.timezone.utc)
                - datetime.timedelta(days=30)
            ).strftime("%Y-%m-%dT%H:%M:%SZ"),
        ).execute()

        video_ids = [item["id"]["videoId"] for item in response.get("items", [])]
        return video_ids
    except Exception as e:
        print(f"    Search failed for '{query}': {e}")
        return []


def get_video_details(youtube, video_ids):
    """Get detailed stats for a batch of video IDs."""
    if not video_ids:
        return []

    videos = []
    # Process in batches of 50 (API limit)
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i+50]
        try:
            response = youtube.videos().list(
                part="snippet,statistics",
                id=",".join(batch)
            ).execute()

            for item in response.get("items", []):
                stats = item.get("statistics", {})
                snippet = item.get("snippet", {})
                views = int(stats.get("viewCount", 0))
                likes = int(stats.get("likeCount", 0))

                videos.append({
                    "id": item["id"],
                    "title": snippet.get("title", ""),
                    "description": snippet.get("description", "")[:300],
                    "tags": snippet.get("tags", [])[:10],
                    "channel": snippet.get("channelTitle", ""),
                    "views": views,
                    "likes": likes,
                    "like_rate": round(likes / max(views, 1) * 100, 2),
                    "published": snippet.get("publishedAt", ""),
                })
        except Exception as e:
            print(f"    Video details fetch failed: {e}")

    return videos


def analyze_with_gemini(videos):
    """Use Gemini to analyze winning patterns from top-performing Shorts."""
    if not GEMINI_AVAILABLE:
        print("  Gemini not available — skipping AI analysis")
        return None

    # Prepare data summary for Gemini
    top_videos = sorted(videos, key=lambda v: v["views"], reverse=True)[:30]

    video_summaries = []
    for v in top_videos:
        video_summaries.append(
            f"Title: {v['title']}\n"
            f"Views: {v['views']:,} | Likes: {v['likes']:,} | Like rate: {v['like_rate']}%\n"
            f"Tags: {', '.join(v['tags'][:5])}\n"
            f"Channel: {v['channel']}"
        )

    data_block = "\n---\n".join(video_summaries)

    prompt = f"""Analyze these top-performing YouTube Shorts in the motivation/mindset niche.
Identify specific, actionable patterns that make them successful.

{data_block}

Return a JSON object with these keys:
1. "title_patterns" — array of 5 specific title formulas that get the most views (e.g., "X things that Y", "Why Z will change your life")
2. "hook_words" — array of 10 power words that appear in top titles
3. "optimal_title_length" — number (average word count of top titles)
4. "trending_topics" — array of 5 specific topics getting views right now
5. "description_patterns" — array of 3 description opening line formulas
6. "tag_patterns" — array of 10 most effective tags across top videos
7. "avoid" — array of 3 patterns that underperform

Return ONLY valid JSON. No markdown, no explanations."""

    try:
        response = gemini_client.models.generate_content(
            model=TEXT_MODEL,
            contents=prompt,
        )
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        return json.loads(text.strip())
    except Exception as e:
        print(f"  Gemini analysis failed: {e}")
        return None


def main():
    print("=" * 50)
    print("  Competitor Analysis — YouTube Shorts")
    print("  Niche: Motivation / Mindset / Self-Improvement")
    print("=" * 50)

    os.makedirs("output", exist_ok=True)

    # Step 1 — Authenticate
    print("\n[1/4] Authenticating with YouTube API...")
    youtube = get_youtube_client()
    print("  Authenticated!")

    # Step 2 — Search for top Shorts
    print(f"\n[2/4] Searching {len(SEARCH_QUERIES)} queries for top Shorts...")
    all_video_ids = []
    for query in SEARCH_QUERIES:
        ids = search_top_shorts(youtube, query, max_results=10)
        print(f"    '{query}' → {len(ids)} results")
        all_video_ids.extend(ids)

    # Deduplicate
    all_video_ids = list(dict.fromkeys(all_video_ids))
    print(f"  Total unique videos: {len(all_video_ids)}")

    # Step 3 — Get detailed stats
    print(f"\n[3/4] Fetching video details...")
    videos = get_video_details(youtube, all_video_ids)
    print(f"  Got details for {len(videos)} videos")

    if not videos:
        print("  ERROR: No video data retrieved. Check API quota.")
        return

    # Sort by views and print top 10
    videos.sort(key=lambda v: v["views"], reverse=True)
    print("\n  TOP 10 SHORTS IN YOUR NICHE:")
    print("  " + "-" * 45)
    for v in videos[:10]:
        print(f"  {v['views']:>10,} views | {v['like_rate']:>5.1f}% likes | {v['title'][:50]}")
    print("  " + "-" * 45)

    # Step 4 — Gemini analysis
    print(f"\n[4/4] Analyzing winning patterns with Gemini...")
    insights = analyze_with_gemini(videos)

    # Build final output
    output = {
        "generated_at": datetime.datetime.now().isoformat(),
        "videos_analyzed": len(videos),
        "top_video": {
            "title": videos[0]["title"],
            "views": videos[0]["views"],
            "channel": videos[0]["channel"],
        },
        "avg_views": int(sum(v["views"] for v in videos) / len(videos)),
        "avg_like_rate": round(sum(v["like_rate"] for v in videos) / len(videos), 2),
        "insights": insights or {},
        "raw_top_titles": [v["title"] for v in videos[:20]],
        "raw_top_tags": list(set(
            tag for v in videos[:20] for tag in v.get("tags", [])
        ))[:30],
    }

    with open(INSIGHTS_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n  Saved: {INSIGHTS_FILE}")

    # Print key insights
    if insights:
        print("\n  KEY INSIGHTS:")
        print("  " + "-" * 45)
        if "title_patterns" in insights:
            print("  Title formulas that work:")
            for p in insights["title_patterns"][:3]:
                print(f"    → {p}")
        if "trending_topics" in insights:
            print("  Trending topics right now:")
            for t in insights["trending_topics"][:3]:
                print(f"    → {t}")
        if "hook_words" in insights:
            print(f"  Power words: {', '.join(insights['hook_words'][:6])}")
        if "avoid" in insights:
            print("  Patterns to AVOID:")
            for a in insights["avoid"]:
                print(f"    x {a}")
        print("  " + "-" * 45)

    print(f"""
  HOW THIS FEEDS INTO YOUR PIPELINE:
  - 02_write_script.py reads {INSIGHTS_FILE}
  - Gemini uses these patterns to write better titles/hooks
  - Run this weekly to stay current with trends

  Recommendation: Run this BEFORE batch_main.py each week
""")


if __name__ == "__main__":
    main()
