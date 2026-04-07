"""
long_02_write_script.py — Long-Form Script Generator (7-8 min videos)

Reads 8-10 pages from the current book and generates a structured
long-form script with intro, 5-7 chapters, and outro via Gemini.

Outputs:
  - output/sections/01_intro.txt, 02_chapter1.txt, ..., XX_outro.txt
  - output/seo_data.json (title, description with timestamps + affiliate links, tags)

Uses separate progress tracker: books/long_progress.json
"""

import os
import sys
import re
import json
from datetime import datetime
from dotenv import load_dotenv
from google import genai
import PyPDF2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from get_trending_tags import get_trending_tags
    _TRENDING_AVAILABLE = True
except ImportError:
    _TRENDING_AVAILABLE = False

try:
    from analytics_tracker import get_top_patterns
    _ANALYTICS_AVAILABLE = True
except ImportError:
    _ANALYTICS_AVAILABLE = False

load_dotenv()
client = genai.Client()
MODEL = "gemini-2.5-flash"

CORE_TAGS = [
    "motivation", "mindset", "discipline", "selfimprovement", "success",
    "mentalstrength", "habits", "growthmindset", "personaldevelopment",
    "consistency", "focus", "hustle", "stoicism", "dailymotivation",
    "successmindset", "productivity", "selfhelp", "inspiration",
    "personalgrowth", "mindsetshift",
]

# ── Amazon Affiliate Links ──────────────────────────────────────────
# Map book filenames (lowercase, without .pdf) to affiliate URLs.
# Add your own affiliate tag links here.
AFFILIATE_LINKS = {
    "atomic habits":      "https://amzn.to/REPLACE_atomic_habits",
    "cant hurt me":       "https://amzn.to/REPLACE_cant_hurt_me",
    "48 laws of power":   "https://amzn.to/REPLACE_48_laws",
    "think and grow rich": "https://amzn.to/REPLACE_think_grow_rich",
    "the art of war":     "https://amzn.to/REPLACE_art_of_war",
    "rich dad poor dad":  "https://amzn.to/REPLACE_rich_dad",
    "the psychology of money": "https://amzn.to/REPLACE_psych_money",
    "deep work":          "https://amzn.to/REPLACE_deep_work",
    "mindset":            "https://amzn.to/REPLACE_mindset",
    "the subtle art":     "https://amzn.to/REPLACE_subtle_art",
}

RECOMMENDED_BOOKS = [
    ("Atomic Habits — James Clear", "https://amzn.to/REPLACE_atomic_habits"),
    ("Can't Hurt Me — David Goggins", "https://amzn.to/REPLACE_cant_hurt_me"),
    ("48 Laws of Power — Robert Greene", "https://amzn.to/REPLACE_48_laws"),
    ("Think and Grow Rich — Napoleon Hill", "https://amzn.to/REPLACE_think_grow_rich"),
    ("The Psychology of Money — Morgan Housel", "https://amzn.to/REPLACE_psych_money"),
]


def get_book_pages_long():
    """
    Read 8-10 pages from the current book for long-form content.
    Uses separate progress tracker: books/long_progress.json
    """
    books_dir = "books"
    if not os.path.exists(books_dir):
        os.makedirs(books_dir)
        print(f"  [!] {books_dir}/ folder created.")
        print("  Please place a book (.pdf file) inside it and run again.")
        sys.exit(1)

    book_files = sorted([f for f in os.listdir(books_dir) if f.endswith(".pdf")])
    if not book_files:
        print(f"  [!] No .pdf files found in {books_dir}/.")
        sys.exit(1)

    progress_file = os.path.join(books_dir, "long_progress.json")
    if os.path.exists(progress_file):
        with open(progress_file, "r", encoding="utf-8") as f:
            progress = json.load(f)
    else:
        progress = {"current_book": book_files[0], "current_page": 0, "end_page": -1}

    current_book = progress.get("current_book")
    if current_book not in book_files:
        current_book = book_files[0]
        progress["current_book"] = current_book
        progress["current_page"] = 0
        progress["end_page"] = -1

    book_path = os.path.join(books_dir, current_book)
    start_page = progress.get("current_page", 0)
    user_end_page = progress.get("end_page", -1)
    page_text = ""
    pages_to_read = 10  # 8-10 pages per long-form video

    try:
        with open(book_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            total_pages = len(reader.pages)

            end_limit = total_pages
            if user_end_page != -1 and user_end_page < total_pages:
                end_limit = user_end_page

            if start_page >= end_limit:
                print(f"  [!] Reached the defined end page ({end_limit}) of {current_book}.")
                print(f"  Please remove {current_book} from {books_dir}/ to start the next book.")
                sys.exit(1)

            actual_pages_read = 0
            for p in range(start_page, min(start_page + pages_to_read, end_limit)):
                extracted = reader.pages[p].extract_text()
                if extracted:
                    page_text += extracted + "\n\n"
                    actual_pages_read += 1

            next_page = start_page + pages_to_read
            if next_page > end_limit:
                next_page = end_limit

    except Exception as e:
        print(f"  [!] Error reading {current_book}: {e}")
        sys.exit(1)

    progress["current_page"] = next_page
    with open(progress_file, "w", encoding="utf-8") as f:
        json.dump(progress, f, indent=2)

    print(f"  [+] Reading from {current_book} (Pages {start_page} to {min(start_page + pages_to_read - 1, end_limit - 1)})")

    if not page_text.strip():
        return get_book_pages_long()

    return page_text.strip(), current_book


def ask_gemini(prompt, max_tokens=16384):
    response = client.models.generate_content(model=MODEL, contents=prompt)
    text = response.text.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    return text


def sanitize_json_text(text):
    result = []
    in_string = False
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == '"' and (i == 0 or text[i - 1] != '\\'):
            in_string = not in_string
            result.append(ch)
        elif in_string:
            if ch == '\n':
                result.append('\\n')
            elif ch == '\r':
                result.append('\\r')
            elif ch == '\t':
                result.append('\\t')
            elif ord(ch) < 0x20:
                pass
            else:
                result.append(ch)
        else:
            result.append(ch)
        i += 1
    return ''.join(result)


def parse_json_safe(text, retries_left=2, prompt=None):
    text = sanitize_json_text(text)
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"  WARNING: JSON parse failed - {e}")
        repaired = text.rstrip()
        if repaired.count('"') % 2 != 0:
            repaired += '"'
        open_braces = repaired.count('{') - repaired.count('}')
        open_brackets = repaired.count('[') - repaired.count(']')
        if open_brackets > 0:
            repaired += ']' * open_brackets
        if open_braces > 0:
            repaired += '}' * open_braces
        try:
            return json.loads(repaired)
        except json.JSONDecodeError:
            pass
        if retries_left > 0 and prompt:
            print(f"  Retrying... ({retries_left} attempts left)")
            new_text = ask_gemini(prompt)
            return parse_json_safe(new_text, retries_left - 1, prompt)
        raise ValueError(f"Failed to parse JSON. Raw:\n{text[:500]}")


def sanitize_tags(tags):
    cleaned = []
    for tag in tags:
        tag = str(tag).strip().lstrip('#').strip()
        if not tag:
            continue
        tag = re.sub(r"[^a-zA-Z0-9 \-]", '', tag).strip()
        tag = re.sub(r' +', ' ', tag)
        if not tag:
            continue
        tag = tag[:100] if ' ' in tag else tag[:30]
        cleaned.append(tag)

    seen = set()
    deduped = []
    for tag in cleaned:
        key = tag.lower()
        if key not in seen:
            seen.add(key)
            deduped.append(tag)

    result = []
    total = 0
    for tag in deduped:
        cost = len(tag) + (1 if result else 0)
        if total + cost > 500:
            break
        result.append(tag)
        total += cost
    return result


def get_book_affiliate_link(book_name):
    """Find the affiliate link for the current book."""
    book_lower = os.path.splitext(book_name)[0].lower()
    for key, url in AFFILIATE_LINKS.items():
        if key in book_lower or book_lower in key:
            return os.path.splitext(book_name)[0], url
    return os.path.splitext(book_name)[0], None


def build_affiliate_section(book_name):
    """Build the affiliate links section for the description."""
    book_title, book_url = get_book_affiliate_link(book_name)
    lines = []

    if book_url:
        lines.append(f"\n\n📚 Book from this video:")
        lines.append(f"👉 {book_title} — {book_url}")

    lines.append(f"\n📚 Books that changed my life:")
    for title, url in RECOMMENDED_BOOKS:
        lines.append(f"👉 {title} — {url}")

    return "\n".join(lines)


def write_long_script(book_page_text, book_name):
    prompt = f"""You are a top-tier YouTube Content Creator specialized in long-form motivational and self-improvement content for the USA market (18-35 audience).

INPUT BOOK TEXT (use concepts and wisdom from this — but NEVER mention the book name):
{book_page_text}

MISSION: Transform this into a single 7-8 minute YouTube video script.
The video will have pure black background with centered white text (like a cinematic reading experience).

━━━━━━━━━━━━━━━━━━━━━━━━
STRUCTURE RULES:
━━━━━━━━━━━━━━━━━━━━━━━━
The script MUST have this exact structure:
1. INTRO (15-20 seconds, ~50 words) — powerful hook that makes them stay
2. CHAPTERS (5-7 chapters, each 50-70 seconds, ~150 words each) — deep value content
3. OUTRO (15-20 seconds, ~50 words) — strong closing + subscribe CTA

Total word count: 1100-1400 words (for 7-8 minutes at speaking pace).

━━━━━━━━━━━━━━━━━━━━━━━━
TITLE RULES:
━━━━━━━━━━━━━━━━━━━━━━━━
- NEVER include the book name
- Do NOT end with #Shorts (this is a long-form video)
- Keep under 70 characters
- SEO-optimized — include primary keyword naturally
- Create curiosity WITHOUT revealing the answer
- Examples:
  "7 Rules That Separate Winners From Everyone Else"
  "The Mindset That Makes Ordinary People Unstoppable"
  "Why 99% of People Stay Broke (And How to Fix It)"
  "The Psychology Behind Every Successful Person"

━━━━━━━━━━━━━━━━━━━━━━━━
DESCRIPTION RULES:
━━━━━━━━━━━━━━━━━━━━━━━━
Line 1: [Primary keyword phrase] — [direct benefit, under 95 chars]
Line 2: [Secondary keyword phrase] | [curiosity hook or stat]
Line 3: (blank)
Line 4: Hook text from the video intro
Line 5-8: 3-4 sentences of value/context about what they'll learn
Line 9: (blank)
Line 10: TIMESTAMPS (will be filled in later — just put TIMESTAMPS_PLACEHOLDER)
Line 11: (blank)
Line 12: Follow for daily mindset and success content.
Line 13: 🔔 Subscribe — new video every day
Line 14: 👍 Like if this changed your perspective
Line 15: 💾 Save this — you'll want to rewatch it
Line 16: (blank)
Line 17: 15 hashtags starting with #motivation #mindset then niche-specific

━━━━━━━━━━━━━━━━━━━━━━━━
TAG RULES:
━━━━━━━━━━━━━━━━━━━━━━━━
Provide EXACTLY 32 tags. These are YouTube keyword tags, NOT hashtags.
- NEVER start a tag with #
- NEVER use special characters: no &, no /, no quotes, no emojis
- ONLY use: letters, numbers, spaces, hyphens
- Mix broad, mid-tail, long-tail, and name tags

━━━━━━━━━━━━━━━━━━━━━━━━
SCRIPT RULES:
━━━━━━━━━━━━━━━━━━━━━━━━
- American English, conversational but powerful
- Each chapter should have a clear chapter title (short, 2-5 words)
- First line of intro = hook (must make them STOP scrolling)
- High value density — every sentence teaches something
- Natural transitions between chapters
- End with a thought-provoking closing statement

Respond in this EXACT JSON format — no extra text outside the JSON:
{{
    "youtube_title": "SEO-optimized title under 70 chars, no #Shorts",
    "description": "Full description following the structure above",
    "intro": "Full intro script text (15-20 seconds, ~50 words)",
    "chapters": [
        {{
            "chapter_title": "Short Chapter Title",
            "script": "Full chapter script (50-70 seconds, ~150 words)"
        }},
        {{
            "chapter_title": "Short Chapter Title",
            "script": "Full chapter script (50-70 seconds, ~150 words)"
        }}
    ],
    "outro": "Full outro script text (15-20 seconds, ~50 words)",
    "tags": ["motivation", "mindset", "... exactly 30 more unique tags"],
    "category_id": "27"
}}
Only JSON. No extra text."""

    text = ask_gemini(prompt)
    return parse_json_safe(text, retries_left=2, prompt=prompt)


def main():
    print("=" * 50)
    print("  NextLevelMind — Long-Form Script Generator")
    print(f"  Model: {MODEL}")
    print("=" * 50)

    book_page_text, current_book_name = get_book_pages_long()

    print(f"\n  Book: {current_book_name}")
    print(f"\n[1/3] Generating long-form script from book pages...")
    script_data = write_long_script(book_page_text, current_book_name)

    print(f"  Title    : {script_data['youtube_title']}")
    print(f"  Chapters : {len(script_data['chapters'])}")

    # Save section files
    print("\n[2/3] Saving text sections...")
    os.makedirs("output/sections", exist_ok=True)

    # Intro
    with open("output/sections/01_intro.txt", "w", encoding="utf-8") as f:
        f.write(script_data["intro"])

    # Chapters
    for i, chapter in enumerate(script_data["chapters"], 1):
        filename = f"output/sections/{i+1:02d}_chapter{i}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(chapter["script"])

    # Outro
    outro_num = len(script_data["chapters"]) + 2
    with open(f"output/sections/{outro_num:02d}_outro.txt", "w", encoding="utf-8") as f:
        f.write(script_data["outro"])

    total_sections = 1 + len(script_data["chapters"]) + 1
    print(f"  Saved {total_sections} section files")

    # Build tags
    tags = list(CORE_TAGS)
    existing_lower = {t.lower() for t in tags}
    for t in script_data.get("tags", []):
        if t.lower() not in existing_lower:
            tags.append(t)
            existing_lower.add(t.lower())

    if _TRENDING_AVAILABLE:
        print("\n  Fetching trending tags from Google Trends...")
        trending = get_trending_tags(category="general")
        for t in trending:
            if t.lower() not in existing_lower:
                tags.append(t)
                existing_lower.add(t.lower())

    tags = sanitize_tags(tags)
    print(f"  Tags     : {len(tags)} tags ({sum(len(t) for t in tags)} chars)")

    # Build description with affiliate links
    description = script_data.get("description", "")
    if "#motivation" not in description.lower():
        description = description.rstrip() + (
            "\n\n#motivation #mindset #selfimprovement #discipline #successmindset "
            "#growthmindset #personaldevelopment #dailyhabits #mentalstrength "
            "#stoicism #motivationalvideo #consistency #inspiration #selfhelp #productivity"
        )

    # Append affiliate links
    affiliate_section = build_affiliate_section(current_book_name)
    description = description.rstrip() + "\n" + affiliate_section

    # Save chapter titles for timestamp generation later (after voiceover)
    chapter_titles = ["Intro"] + [ch["chapter_title"] for ch in script_data["chapters"]] + ["Outro"]

    seo_data = {
        "youtube_title": script_data["youtube_title"],
        "description": description,
        "tags": tags,
        "keywords": tags,
        "category": "Education",
        "category_id": script_data.get("category_id", "27"),
        "is_long_form": True,
        "chapter_titles": chapter_titles,
    }
    with open("output/seo_data.json", "w", encoding="utf-8") as f:
        json.dump(seo_data, f, indent=2, ensure_ascii=False)

    # Save full script for reference
    full_script = script_data["intro"] + " "
    for ch in script_data["chapters"]:
        full_script += ch["script"] + " "
    full_script += script_data["outro"]
    with open("output/latest_script.txt", "w", encoding="utf-8") as f:
        f.write(full_script)

    word_count = len(full_script.split())
    est_minutes = word_count / 160  # speaking pace

    print(f"\n[3/3] Done!")
    print("=" * 50)
    print(f"  Words    : {word_count} (~{est_minutes:.1f} min at speaking pace)")
    print(f"  Sections : {total_sections}")
    print(f"  Title    : {script_data['youtube_title']}")
    print("=" * 50)
    print("\n  Next step: Run 03_voiceover.py")


if __name__ == "__main__":
    main()
