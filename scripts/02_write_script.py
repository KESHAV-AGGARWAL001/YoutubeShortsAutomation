import os
import sys
import re
import json
from datetime import datetime
from dotenv import load_dotenv
from google import genai
import PyPDF2

# Trending tag injector (Phase 5) and analytics (Phase 6)
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

import time as _time

load_dotenv()
# API key is read automatically from GEMINI_API_KEY environment variable
client = genai.Client()
MODEL = "gemini-2.5-flash"
FALLBACK_MODEL = "gemini-2.0-flash"

# ── Core channel tags — always included, always valid, total ≤ 200 chars ──
# These are prepended to every upload so at minimum these tags are always sent.
CORE_TAGS = [
    "shorts", "youtubeshorts", "motivation", "mindset", "discipline",
    "selfimprovement", "success", "mentalstrength", "habits", "growthmindset",
    "personaldevelopment", "consistency", "focus", "hustle", "stoicism",
    "dailymotivation", "successmindset", "productivity", "selfhelp", "inspiration",
]

# ── Fallback hashtag block appended to description if AI omits it ──
FALLBACK_HASHTAGS = (
    "#Shorts #YouTubeShorts #motivation #mindset #selfimprovement "
    "#discipline #success #mentalstrength #habits #growthmindset "
    "#personaldevelopment #consistency #hustle #stoicism #dailymotivation"
)

# ── Amazon Affiliate Links ──────────────────────────────────────────
# Map book filenames (lowercase, without .pdf) to affiliate URLs.
# Replace the placeholder URLs with your actual Amazon affiliate links.
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

def get_book_page():
    books_dir = "books"
    if not os.path.exists(books_dir):
        os.makedirs(books_dir)
        print(f"  [!] {books_dir}/ folder created.")
        print("  Please place a book (.pdf file) inside it and run again.")
        sys.exit(1)

    book_files = sorted([f for f in os.listdir(books_dir) if f.endswith(".pdf")])
    if not book_files:
        print(f"  [!] No .pdf files found in {books_dir}/.")
        print(f"  Please place a book (.pdf format) inside {books_dir}/ and run again.")
        sys.exit(1)

    progress_file = os.path.join(books_dir, "progress.json")
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
                
            # Extract 2 pages per day
            if start_page < end_limit:
                extracted_text = reader.pages[start_page].extract_text()
                if extracted_text:
                    page_text += extracted_text + "\n\n"
                
            if start_page + 1 < end_limit:
                extracted_text2 = reader.pages[start_page + 1].extract_text()
                if extracted_text2:
                    page_text += extracted_text2 + "\n\n"
                    
            next_page = start_page + 2
            if next_page > end_limit:
                next_page = end_limit
                
    except Exception as e:
        print(f"  [!] Error reading {current_book}: {e}")
        sys.exit(1)

    progress["current_page"] = next_page

    with open(progress_file, "w", encoding="utf-8") as f:
        json.dump(progress, f, indent=2)

    print(f"  [+] Reading from {current_book} (PDF Pages: {start_page} and {min(start_page + 1, end_limit - 1)})")
    
    if not page_text.strip():
        return get_book_page()

    return page_text.strip(), current_book

def ask_gemini(prompt, max_tokens=8192):
    """
    Call Gemini with automatic retry + fallback model.
    Retries 3 times with exponential backoff on overload/rate-limit errors.
    Falls back to FALLBACK_MODEL if primary MODEL keeps failing.
    """
    for attempt in range(4):  # 3 retries on primary + 1 on fallback
        model = MODEL if attempt < 3 else FALLBACK_MODEL
        try:
            if attempt > 0:
                wait = min(2 ** attempt * 5, 60)  # 10s, 20s, 40s
                print(f"  Retry {attempt}/3 — waiting {wait}s... (model: {model})")
                _time.sleep(wait)
            response = client.models.generate_content(model=model, contents=prompt)
            text = response.text.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            if attempt == 3:
                print(f"  Fallback model ({FALLBACK_MODEL}) succeeded!")
            return text
        except Exception as e:
            err = str(e).lower()
            if any(k in err for k in ["429", "overloaded", "resource", "quota", "rate", "unavailable", "503", "500"]):
                if attempt < 3:
                    print(f"  Gemini overloaded — will retry... ({e})")
                    continue
                else:
                    print(f"  Fallback model also failed — {e}")
                    raise
            else:
                raise

def sanitize_json_text(text):
    """
    Fix literal newlines and control characters inside JSON string values.
    Gemini sometimes outputs real newline characters inside description/script
    fields instead of escaped \\n — this breaks json.loads with
    'Invalid control character' errors.

    Walks the raw text character by character, tracking whether we're
    inside a JSON string, and escapes any bare control characters found there.
    """
    result = []
    in_string = False
    i = 0
    while i < len(text):
        ch = text[i]
        # Toggle in_string on unescaped double-quotes
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
                # Drop other control characters — they're never valid in JSON strings
                pass
            else:
                result.append(ch)
        else:
            result.append(ch)
        i += 1
    return ''.join(result)


def parse_json_safe(text, retries_left=2, prompt=None):
    # Sanitize control characters before first parse attempt
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

def _build_performance_context():
    """
    Pull top-performing title patterns from analytics log and format
    them as context for the Gemini prompt (A/B feedback loop).
    """
    if not _ANALYTICS_AVAILABLE:
        return ""
    try:
        patterns = get_top_patterns(top_n=3)
        if not patterns:
            return ""
        lines = ["━━━━━━━━━━━━━━━━━━━━━━━━",
                 "PERFORMANCE INTELLIGENCE (A/B data from your channel — use these patterns MORE):"]
        for p in patterns:
            lines.append(
                f"  ✅ Pattern [{p['pattern']}] — avg {p['avg_views']:,} views | "
                f"Best title: \"{p['best_title'][:60]}\""
            )
        lines.append("Use the winning patterns above more often. Avoid patterns NOT listed here.")
        return "\n".join(lines) + "\n"
    except Exception:
        return ""


def sanitize_tags(tags):
    """
    Sanitize tags to meet YouTube Data API requirements.
    Called before saving seo_data.json so tags are always clean.

    Rules enforced:
    - Strip leading # (YouTube tags must NOT start with #)
    - Only allow: letters, digits, spaces, hyphens, apostrophes
    - Remove empty tags after cleaning
    - Truncate single-word tags to 30 chars, multi-word to 100 chars
    - Total combined length must stay under 500 chars
    """
    cleaned = []
    for tag in tags:
        tag = str(tag).strip().lstrip('#').strip()
        if not tag:
            continue
        # Keep only safe characters: letters, digits, spaces, hyphens
        tag = re.sub(r"[^a-zA-Z0-9 \-]", '', tag).strip()
        # Collapse multiple spaces into one
        tag = re.sub(r' +', ' ', tag)
        if not tag:
            continue
        tag = tag[:100] if ' ' in tag else tag[:30]
        cleaned.append(tag)

    # Deduplicate (case-insensitive) while preserving order
    seen = set()
    deduped = []
    for tag in cleaned:
        key = tag.lower()
        if key not in seen:
            seen.add(key)
            deduped.append(tag)

    # Enforce 500-char total limit
    result = []
    total = 0
    for tag in deduped:
        cost = len(tag) + (1 if result else 0)  # comma before every tag except first
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


def write_shorts_scripts(book_page_text, book_name):
    performance_context = _build_performance_context()

    prompt = f"""You are an elite YouTube Shorts viral content strategist. You understand the algorithm deeply: completion rate is EVERYTHING. A 15-second Short with 95% retention will outperform a 50-second Short with 40% retention every single time.

{performance_context}INPUT BOOK PAGE TEXT (use concepts and wisdom from this — but NEVER mention the book name):
{book_page_text}

MISSION: Transform this into 2 viral YouTube Shorts.
- Short 1: EMOTIONAL / STORYTELLING angle
- Short 2: DIRECT ADVICE / "HARD TRUTH" angle

━━━━━━━━━━━━━━━━━━━━━━━━
TITLE RULES (CRITICAL FOR ALGORITHM):
━━━━━━━━━━━━━━━━━━━━━━━━
- NEVER include the book name.
- ALWAYS end the title with #Shorts.
- Keep under 60 characters.
- The title must feel PERSONAL — use "You" or "Your" when possible.
- Create a SPECIFIC curiosity gap — not vague motivation.
- NEVER use these overused titles (they are BANNED):
  ❌ "I Wish Someone Had Told Me This Sooner"
  ❌ "The Brutal Truth About Why You're Still Losing"
  ❌ "The Lesson That Actually Changed My Life"
  ❌ "What Winners Do That Nobody Ever Sees"
  ❌ "The Mindset Shift That Changes Everything"
  ❌ "99% of People Get This Completely Wrong"

- INSTEAD use patterns that feel SPECIFIC and PERSONAL:
  ✅ "You Do THIS Every Morning And It's Destroying You #Shorts"
  ✅ "Your Brain Is Lying to You Right Now #Shorts"
  ✅ "Delete This One Habit Or Stay Broke Forever #Shorts"
  ✅ "3 Seconds. That's All You Get. #Shorts"
  ✅ "You're Not Lazy. You're Doing This Wrong. #Shorts"
  ✅ "The 5AM Lie Nobody Talks About #Shorts"
  ✅ "Rich People Never Say This Word #Shorts"
  ✅ "If You Do This Before Bed You'll Win #Shorts"
  ✅ "Your Phone Is Eating Your Future #Shorts"
  ✅ "This 10-Second Test Reveals Everything #Shorts"

━━━━━━━━━━━━━━━━━━━━━━━━
SCRIPT RULES (MOST IMPORTANT — READ 3 TIMES):
━━━━━━━━━━━━━━━━━━━━━━━━
LENGTH: 15-25 seconds of speaking content. That's 40-70 words TOTAL. NOT 120 words. NOT 100 words. MAXIMUM 70 WORDS.
Why? Short = higher completion rate = YouTube pushes to millions.

STRUCTURE — Every script MUST follow this exact flow:
1. HOOK (first sentence, 1-2 seconds): Pattern interrupt. Make them STOP.
   - Start with "You" or a direct command — never "Did you know" or "Here's the thing"
   - Must feel like you're calling them out personally
   - Examples: "Stop. You did this today and didn't even realize it."
              "You're reading this because something isn't working."
              "Your alarm went off this morning. What you did next decided everything."

2. BODY (10-18 seconds): ONE single powerful idea. Not 3 ideas. Not a list. ONE.
   - Short punchy sentences. 5-10 words each.
   - Every sentence must create tension or reveal
   - Use "you" and "your" constantly — make it feel personal
   - Phrase-by-phrase rhythm: statement. pause. reveal. pause. impact.

3. LOOP ENDING (last sentence, 2-3 seconds): The ending MUST connect back to the hook.
   This makes people rewatch. Rewatches = YouTube pushes harder.
   - If hook is "You do THIS every morning..." → end with "...and tomorrow morning, you'll remember this."
   - If hook is "Your brain is lying..." → end with "...and now your brain can't lie to you anymore."
   - The viewer should feel the urge to watch again.

WRITING STYLE:
- American English. Conversational. Raw.
- NO filler words. NO "basically", "actually", "honestly", "look"
- NO generic motivation. Be SPECIFIC. Use numbers, scenarios, actions.
- Write like you're texting a friend a hard truth, not giving a TED talk.

━━━━━━━━━━━━━━━━━━━━━━━━
DESCRIPTION RULES:
━━━━━━━━━━━━━━━━━━━━━━━━
Line 1: [Primary keyword phrase] — [benefit or shocking fact, under 95 chars]
Line 2: [Secondary keyword phrase] | [curiosity gap or stat]
Line 3: (blank)
Line 4: Hook text from the video
Line 5-7: 2-3 sentences of value
Line 8: (blank)
Line 9: Follow for daily content that actually changes your life.
Line 10: 🔔 Subscribe — new short every day
Line 11: 👍 Like if this hit different
Line 12: 💾 Save this for when you need it
Line 13: (blank)
Line 14: 15 hashtags starting with #Shorts #YouTubeShorts then niche-specific

━━━━━━━━━━━━━━━━━━━━━━━━
TAG RULES:
━━━━━━━━━━━━━━━━━━━━━━━━
Provide EXACTLY 32 tags per short. YouTube keyword tags, NOT hashtags.
- NEVER start a tag with # — just plain text
- NEVER use special characters: no &, no /, no quotes, no emojis
- ONLY use: letters, numbers, spaces, hyphens
- Mix: broad ("motivation"), mid ("success mindset"), long-tail ("how to build discipline"), viral names ("david goggins")

Respond in this EXACT JSON format — no extra text outside the JSON:
{{
    "shorts": [
        {{
            "angle_type": "emotional storytelling",
            "youtube_title": "SPECIFIC personal title under 60 chars ending with #Shorts",
            "description": "Full description following structure above",
            "hook": "First punchy line — pattern interrupt — uses YOU",
            "script": "Full 40-70 word script. SHORT. Every word earns its place.",
            "cta": "One short line that triggers rewatch or follow",
            "tags": ["shorts", "youtubeshorts", "... exactly 30 more unique tags"],
            "category_id": "22"
        }},
        {{
            "angle_type": "direct advice",
            "youtube_title": "SPECIFIC personal title under 60 chars ending with #Shorts",
            "description": "Full description following structure above",
            "hook": "First punchy line — pattern interrupt — uses YOU",
            "script": "Full 40-70 word script. SHORT. Every word earns its place.",
            "cta": "One short line that triggers rewatch or follow",
            "tags": ["shorts", "youtubeshorts", "... exactly 30 more unique tags"],
            "category_id": "27"
        }}
    ]
}}
Only JSON. No extra text."""

    text = ask_gemini(prompt)
    return parse_json_safe(text, retries_left=2, prompt=prompt)

def main():
    print("=" * 50)
    print("  NextLevelMind Shorts Generator — Gemini")
    print(f"  Model: {MODEL}")
    print("=" * 50)

    video_num = os.environ.get("VIDEO_NUMBER", "1")
    cache_file = "book_shorts_cache.json"

    print(f"\n  Video        : #{video_num}")

    # Read current book name from progress for affiliate links
    progress_file = os.path.join("books", "progress.json")
    if os.path.exists(progress_file):
        with open(progress_file, "r", encoding="utf-8") as f:
            current_book_name = json.load(f).get("current_book", "book")
    else:
        current_book_name = "book"

    if video_num == "1":
        book_page_text, current_book_name = get_book_page()
        print("\n[1/3] Generating 2 shorts from book page...")
        script_data = write_shorts_scripts(book_page_text, current_book_name)
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(script_data, f, indent=2, ensure_ascii=False)
        short_idx = 0
    else:
        if not os.path.exists(cache_file):
            print("\n[1/3] No cache found, generating new...")
            book_page_text, current_book_name = get_book_page()
            script_data = write_shorts_scripts(book_page_text, current_book_name)
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(script_data, f, indent=2, ensure_ascii=False)
        else:
            print("\n[1/3] Loading script from cache for Video 2...")
            with open(cache_file, "r", encoding="utf-8") as f:
                script_data = json.load(f)
        short_idx = 1

    my_short = script_data["shorts"][short_idx]
    
    print(f"  Angle    : {my_short['angle_type']}")
    print(f"  YT Title : {my_short['youtube_title']}")

    print("\n[2/3] Saving text sections...")
    # Clear old sections to prevent stale text leaking into subtitles
    if os.path.exists("output/sections"):
        import shutil
        shutil.rmtree("output/sections")
    os.makedirs("output/sections", exist_ok=True)
    with open("output/sections/01_hook.txt", "w", encoding="utf-8") as f:
        f.write(my_short["hook"])
    with open("output/sections/02_script.txt", "w", encoding="utf-8") as f:
        f.write(my_short["script"])
    with open("output/sections/03_cta.txt", "w", encoding="utf-8") as f:
        f.write(my_short["cta"])

    # Build tag list: CORE_TAGS first (guaranteed valid), then AI tags, then trending
    tags = list(CORE_TAGS)  # start with always-valid core tags
    existing_lower = {t.lower() for t in tags}

    for t in my_short.get("tags", []):
        if t.lower() not in existing_lower:
            tags.append(t)
            existing_lower.add(t.lower())

    # Inject trending tags (Phase 5) — mix Google Trends keywords into tags
    if _TRENDING_AVAILABLE:
        print("\n  Fetching trending tags from Google Trends...")
        trending = get_trending_tags(category="general")
        for t in trending:
            if t.lower() not in existing_lower:
                tags.append(t)
                existing_lower.add(t.lower())

    # Ensure description always ends with a hashtag block
    description = my_short.get("description", "")
    if "#Shorts" not in description and "#shorts" not in description:
        description = description.rstrip() + "\n\n" + FALLBACK_HASHTAGS
        print("  [!] AI omitted hashtags — fallback block appended to description")

    # Append Amazon Affiliate links to description
    try:
        affiliate_section = build_affiliate_section(current_book_name)
        description = description.rstrip() + "\n" + affiliate_section
        print("  [+] Affiliate links appended to description")
    except Exception:
        pass

    # Sanitize tags before saving — strip #, special chars, enforce 500-char limit
    tags = sanitize_tags(tags)
    print(f"  Tags     : {len(tags)} tags ({sum(len(t) for t in tags)} chars)")

    # Update seo_data.json
    seo_data = {
        "youtube_title": my_short["youtube_title"],
        "description": description,
        "tags": tags,
        "keywords": tags,
        "category": "Education",
        "category_id": my_short.get("category_id", "27"),
        "angle_type": my_short.get("angle_type", ""),
    }
    with open("output/seo_data.json", "w", encoding="utf-8") as f:
        json.dump(seo_data, f, indent=2, ensure_ascii=False)

    full_script = f"{my_short['hook']} {my_short['script']} {my_short['cta']}"
    with open("output/latest_script.txt", "w", encoding="utf-8") as f:
        f.write(full_script)

    print("\n[3/3] Done!")
    print("=" * 50)
    print("\n  Next step: Run 03_voiceover.py")

if __name__ == "__main__":
    main()