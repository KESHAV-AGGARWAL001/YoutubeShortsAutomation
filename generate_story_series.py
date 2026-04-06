"""
generate_story_series.py — Multi-Part Story Series Generator

Generates a 2–5 part serialized Instagram Reel story series using Gemini AI.
Each part is designed to end with a cliffhanger to drive engagement.

Usage:
  python generate_story_series.py                              # random category
  python generate_story_series.py --category mental_strength   # specific category
  python generate_story_series.py --parts 4                    # custom part count
  python generate_story_series.py --list-categories            # show categories

Output:
  story_series/{series_id}/
    ├── series_meta.json
    ├── part_1/script.json
    ├── part_2/script.json
    └── ...
"""

import os
import sys
import json
import random
import argparse
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
from google import genai

load_dotenv()

# API key is read automatically from GEMINI_API_KEY environment variable
client = genai.Client()
MODEL  = "gemini-2.5-flash"

SERIES_DIR  = "story_series"
REGISTRY    = os.path.join(SERIES_DIR, "series_registry.json")

# ── Categories (same as 02_write_script.py) ─────────────────────
CATEGORIES = {
    "discipline_habits": {
        "name":        "Discipline & Habits",
        "description": "daily routines, morning habits, consistency, self-discipline, willpower",
        "title_style": "habit or routine angle — practical and direct",
        "avoid":       "avoid generic 5 morning habits titles"
    },
    "mental_strength": {
        "name":        "Mental Strength",
        "description": "overcoming fear, anxiety, self-doubt, building resilience, mental toughness",
        "title_style": "emotional and deep — speaks to inner struggle",
        "avoid":       "avoid surface-level positivity"
    },
    "success_mindset": {
        "name":        "Success Mindset",
        "description": "billionaire habits, wealth psychology, career growth, thinking like winners",
        "title_style": "aspirational with a contrarian twist",
        "avoid":       "avoid get rich quick or basic tips"
    },
    "life_philosophy": {
        "name":        "Life Philosophy",
        "description": "stoicism, finding purpose, meaning, living intentionally, deep life questions",
        "title_style": "philosophical and thought-provoking",
        "avoid":       "avoid religious or political angles"
    },
    "overcoming_failure": {
        "name":        "Overcoming Failure",
        "description": "bounce back from failure, rejection, starting over, resilience stories",
        "title_style": "story-driven, emotional journey",
        "avoid":       "avoid toxic positivity"
    },
    "focus_productivity": {
        "name":        "Focus & Productivity",
        "description": "deep work, eliminating distraction, getting more done, flow state",
        "title_style": "specific and practical with urgency",
        "avoid":       "avoid generic productivity lists"
    }
}


# ── AI Generation ───────────────────────────────────────────────

def ask_gemini(prompt, max_tokens=4096):
    """Send prompt to Gemini and return cleaned text."""
    response = client.models.generate_content(model=MODEL, contents=prompt)
    text = response.text.strip()
    # Strip markdown code fences
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    return text


def parse_json_safe(text, retries=2, prompt=None):
    """Parse JSON with repair attempts and retries."""
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"  ⚠️  JSON parse failed: {e}")
        # Try to repair
        repaired = text.rstrip()
        if repaired.count('"') % 2 != 0:
            repaired += '"'
        open_braces   = repaired.count('{') - repaired.count('}')
        open_brackets = repaired.count('[') - repaired.count(']')
        if open_brackets > 0:
            repaired += ']' * open_brackets
        if open_braces > 0:
            repaired += '}' * open_braces
        try:
            return json.loads(repaired)
        except json.JSONDecodeError:
            pass
        if retries > 0 and prompt:
            print(f"  Retrying... ({retries} attempts left)")
            new_text = ask_gemini(prompt, max_tokens=4096)
            return parse_json_safe(new_text, retries - 1, prompt)
        raise ValueError(f"Failed to parse JSON after retries. Raw:\n{text[:500]}")


def generate_story(category_key, num_parts):
    """Generate a multi-part story series using Gemini."""
    cat = CATEGORIES[category_key]

    prompt = f"""You are a viral Instagram Reels scriptwriter for the account @nextlevelmind_km.
Your job is to write a multi-part serialized story series optimized for maximum
suspense, retention, and "Part 2?" comments.

CATEGORY: {cat['name']}
CATEGORY DESCRIPTION: {cat['description']}
TITLE STYLE: {cat['title_style']}
AVOID: {cat['avoid']}
NUMBER OF PARTS: {num_parts}

RULES:
- Each part must be 45–75 seconds when read aloud (roughly 120–180 words)
- Every part EXCEPT the last must end with a cliffhanger or open loop
- Every part EXCEPT the first must open with a "Previously..." one-liner recap
- Part 1 must hook the viewer in the FIRST 3 SECONDS — start with a shocking statement or question
- Write in second-person ("you") or story-driven third-person — never lecture
- Vary the vibe: some parts are intense, some reflective, some shocking
- The series must feel like a Netflix mini-series, not a YouTube video list
- Each part stands alone but is INCOMPLETE without the next part

OUTPUT FORMAT (strict JSON, no markdown, no extra text):
{{
  "series_title": "The night I decided to burn everything down",
  "category": "{category_key}",
  "total_parts": {num_parts},
  "parts": [
    {{
      "part_number": 1,
      "title": "Part 1: The Night Everything Collapsed",
      "script": "Full narration script here. 120-180 words. Starts with a shocking hook.",
      "hook": "First 1-2 sentences used as the visual text overlay",
      "cliffhanger": "Last line that creates suspense — shown as end card text",
      "caption": "Instagram caption for this part (150-200 chars max)",
      "hashtags": "#nextlevelmind #motivation #mentalstrength #storytime #part1",
      "cta": "Comment 'PART 2' if you want to know what happened next 👇",
      "mood": "intense"
    }}
  ]
}}

Generate exactly {num_parts} parts. Only JSON output, no other text."""

    print(f"  Generating {num_parts}-part story series...")
    print(f"  Category: {cat['name']}")
    print(f"  Model: {MODEL}")

    text   = ask_gemini(prompt, max_tokens=4096)
    result = parse_json_safe(text, retries=2, prompt=prompt)

    # Validate structure
    if "parts" not in result or not isinstance(result["parts"], list):
        raise ValueError("AI response missing 'parts' array")

    if len(result["parts"]) < 2:
        raise ValueError(f"Only {len(result['parts'])} parts generated, need at least 2")

    return result


# ── Registry Management ─────────────────────────────────────────

def load_registry():
    """Load or create the series registry."""
    if os.path.exists(REGISTRY):
        with open(REGISTRY, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"active_series": [], "completed_series": []}


def save_registry(registry):
    """Save the series registry."""
    os.makedirs(SERIES_DIR, exist_ok=True)
    with open(REGISTRY, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)


def create_series_id(title):
    """Generate a snake_case series ID from the title + timestamp."""
    # Clean title to snake_case
    clean = title.lower().strip()
    clean = "".join(c if c.isalnum() or c == " " else "" for c in clean)
    clean = "_".join(clean.split())
    # Truncate and add timestamp
    clean = clean[:40]
    ts    = datetime.now().strftime("%Y%m%d")
    return f"{clean}_{ts}"


# ── Save Series ─────────────────────────────────────────────────

def save_series(story_data):
    """Save the generated series to disk and update registry."""
    title       = story_data.get("series_title", "Untitled Story")
    category    = story_data.get("category", "unknown")
    total_parts = story_data.get("total_parts", len(story_data["parts"]))
    series_id   = create_series_id(title)

    # Create series directory
    series_dir = os.path.join(SERIES_DIR, series_id)
    os.makedirs(series_dir, exist_ok=True)

    # Build upload schedule (one part per day, starting today)
    today    = date.today()
    schedule = {}
    parts_status = {}
    for i in range(1, total_parts + 1):
        upload_date = today + timedelta(days=i - 1)
        schedule[f"part_{i}"]   = upload_date.isoformat()
        parts_status[str(i)]    = "pending"

    # Save series_meta.json
    meta = {
        "series_id":       series_id,
        "series_title":    title,
        "category":        category,
        "total_parts":     total_parts,
        "created_at":      datetime.now().isoformat(timespec="seconds"),
        "status":          "pending",
        "upload_schedule":  schedule,
        "parts_status":     parts_status,
    }
    meta_path = os.path.join(series_dir, "series_meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    # Save each part's script.json
    for part in story_data["parts"]:
        part_num = part["part_number"]
        part_dir = os.path.join(series_dir, f"part_{part_num}")
        os.makedirs(part_dir, exist_ok=True)

        script_path = os.path.join(part_dir, "script.json")
        with open(script_path, "w", encoding="utf-8") as f:
            json.dump(part, f, indent=2, ensure_ascii=False)

        # Initialize status.json
        status_path = os.path.join(part_dir, "status.json")
        with open(status_path, "w", encoding="utf-8") as f:
            json.dump({
                "part_number":     part_num,
                "status":          "pending",
                "scheduled_date":  schedule[f"part_{part_num}"],
                "uploaded_at":     None,
                "instagram_media_id": None,
                "tmpfiles_url":    None,
            }, f, indent=2, ensure_ascii=False)

    # Update registry
    registry = load_registry()
    registry["active_series"].append({
        "series_id":        series_id,
        "series_title":     title,
        "category":         category,
        "total_parts":      total_parts,
        "next_upload_part": 1,
        "next_upload_date": schedule["part_1"],
        "status":           "active",
    })
    save_registry(registry)

    return series_id, meta


# ── CLI ─────────────────────────────────────────────────────────

def list_categories():
    """Print all available categories."""
    print("\n  Available Categories:")
    print(f"  {'─' * 50}")
    for key, cat in CATEGORIES.items():
        print(f"  {key:<25} {cat['name']}")
        print(f"  {'':25} {cat['description'][:60]}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Generate a multi-part Instagram story series using AI"
    )
    parser.add_argument("--category",        type=str, default=None,
                        help="Category key (e.g. mental_strength)")
    parser.add_argument("--parts",           type=int, default=None,
                        help="Number of parts (2-5, default: AI decides)")
    parser.add_argument("--list-categories", action="store_true",
                        help="List all available categories")
    args = parser.parse_args()

    print("\n" + "=" * 55)
    print("  📖 Story Series Generator — NextLevelMind")
    print(f"  Model: {MODEL}")
    print("=" * 55)

    if args.list_categories:
        list_categories()
        return

    # Pick category
    if args.category:
        if args.category not in CATEGORIES:
            print(f"\n  ❌ Unknown category: {args.category}")
            list_categories()
            sys.exit(1)
        category_key = args.category
    else:
        category_key = random.choice(list(CATEGORIES.keys()))

    # Number of parts
    num_parts = args.parts or random.randint(3, 4)
    num_parts = max(2, min(5, num_parts))

    cat = CATEGORIES[category_key]
    print(f"\n  Category: {cat['name']}")
    print(f"  Parts:    {num_parts}")

    # Generate
    print(f"\n  {'─' * 50}")
    try:
        story_data = generate_story(category_key, num_parts)
    except Exception as e:
        print(f"\n  ❌ Generation failed: {e}")
        sys.exit(1)

    title       = story_data.get("series_title", "Untitled")
    total_parts = story_data.get("total_parts", len(story_data["parts"]))

    print(f"\n  ✅ Generated: \"{title}\"")
    print(f"  Parts: {len(story_data['parts'])}")

    for part in story_data["parts"]:
        pn    = part["part_number"]
        mood  = part.get("mood", "?")
        words = len(part.get("script", "").split())
        hook  = part.get("hook", "")[:60]
        print(f"\n  Part {pn}: {part.get('title', f'Part {pn}')}")
        print(f"    Mood: {mood} | Words: {words}")
        print(f"    Hook: {hook}...")

    # Save
    print(f"\n  {'─' * 50}")
    print(f"  Saving series...")
    series_id, meta = save_series(story_data)

    # Print schedule
    print(f"\n  ✅ Series created: {series_id}")
    print(f"\n  📅 Upload Schedule:")
    for part_key, upload_date in meta["upload_schedule"].items():
        part_num = part_key.replace("part_", "")
        print(f"     Part {part_num} → {upload_date}")

    print(f"\n  📂 Files: story_series/{series_id}/")
    print(f"\n{'=' * 55}")
    print(f"  Next steps:")
    print(f"  1. Render reels:  python render_story_reels.py --series {series_id}")
    print(f"  2. Upload daily:  python schedule_story_upload.py")
    print(f"  3. View status:   python story_dashboard.py")
    print(f"{'=' * 55}\n")


if __name__ == "__main__":
    main()
