import os
import sys
import re
import json
import random
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime
from dotenv import load_dotenv
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

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

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

def ask_groq(prompt, max_tokens=8192):
    """Call Groq chat completions API with retry on overload."""
    if not GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY not set. Get a free key at https://console.groq.com and add to .env"
        )

    payload = json.dumps({
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.7,
    }).encode()

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }

    for attempt in range(3):
        try:
            if attempt > 0:
                wait = 10 * attempt
                print(f"  Groq retry {attempt}/2 — waiting {wait}s...")
                _time.sleep(wait)

            req = urllib.request.Request(GROQ_API_URL, data=payload, headers=headers)
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode())

            text = result["choices"][0]["message"]["content"].strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            return text

        except urllib.error.HTTPError as e:
            if e.code in (429, 503, 500) and attempt < 2:
                print(f"  Groq overloaded ({e.code}) — will retry...")
                continue
            raise
        except Exception as e:
            if attempt < 2:
                print(f"  Groq error — will retry... ({e})")
                continue
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
            new_text = ask_groq(prompt)
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


DESCRIPTION_STYLES = [
    # Style A — Full structured (classic)
    """Write a natural, unique description. Do NOT follow a rigid template. Include:
- A compelling opening line that hooks the reader (different every time)
- 2-3 sentences about what the viewer will learn or feel
- A personal CTA (vary it — not always "subscribe" or "like")
- 5-8 hashtags at the end (start with #Shorts, rest are niche-specific, VARY them each time)
Do NOT use emoji-heavy CTA blocks. Write it like a real person, not a bot.""",

    # Style B — Minimal (short and punchy)
    """Write a SHORT description (3-5 lines max). No fluff. Include:
- One powerful sentence about the video's core message
- One line of value or a bold claim
- 5-6 hashtags at the end (start with #Shorts)
Do NOT add subscribe/like/save CTAs. Keep it clean and minimal.""",

    # Style C — Story-driven
    """Write the description as a mini-story or thought. Include:
- Start with a question or a "what if" scenario
- 2-3 lines that build curiosity about the video
- End with a casual CTA (like "watch till the end" or "think about this tonight")
- 6-8 hashtags at the end (start with #Shorts)
No rigid format. Make it feel like a journal entry or a tweet thread.""",

    # Style D — SEO-focused conversational
    """Write a natural description optimized for YouTube search. Include:
- Open with a searchable keyword phrase woven into a natural sentence
- 2-3 sentences of value using different keyword variations
- One line encouraging engagement (vary the CTA every time — be creative)
- 5-7 hashtags at the end (start with #Shorts)
Make it feel like a human wrote it, not a template.""",
]


def _load_competitor_insights():
    """Load competitor analysis insights if available."""
    insights_file = "output/competitor_insights.json"
    if not os.path.exists(insights_file):
        return ""
    try:
        with open(insights_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        insights = data.get("insights", {})
        if not insights:
            return ""

        parts = []
        parts.append("━━━━━━━━━━━━━━━━━━━━━━━━")
        parts.append("COMPETITOR INSIGHTS (from recent top-performing Shorts in your niche):")
        parts.append("━━━━━━━━━━━━━━━━━━━━━━━━")

        if insights.get("title_patterns"):
            parts.append("Title formulas that are working RIGHT NOW:")
            for p in insights["title_patterns"][:5]:
                parts.append(f"  - {p}")

        if insights.get("hook_words"):
            parts.append(f"Power words in top titles: {', '.join(insights['hook_words'][:8])}")

        if insights.get("trending_topics"):
            parts.append("Trending topics getting views this week:")
            for t in insights["trending_topics"][:5]:
                parts.append(f"  - {t}")

        if insights.get("avoid"):
            parts.append("Patterns that UNDERPERFORM (avoid these):")
            for a in insights["avoid"][:3]:
                parts.append(f"  x {a}")

        parts.append("Use these insights to craft titles and hooks that match current trends.\n")
        return "\n".join(parts)
    except Exception:
        return ""


def write_shorts_scripts(book_page_text, book_name):
    performance_context = _build_performance_context()
    competitor_context = _load_competitor_insights()

    # Randomize prompt elements to avoid template detection
    desc_style = random.choice(DESCRIPTION_STYLES)
    tag_count = random.randint(8, 12)
    style_idx = DESCRIPTION_STYLES.index(desc_style)
    style_names = ["structured", "minimal", "story-driven", "SEO-conversational"]
    print(f"  Prompt style: {style_names[style_idx]} | Tags: {tag_count}")

    prompt = f"""You are an elite YouTube Shorts viral content strategist. You understand the algorithm deeply: completion rate is EVERYTHING. A 15-second Short with 95% retention will outperform a 50-second Short with 40% retention every single time.

{performance_context}{competitor_context}INPUT BOOK PAGE TEXT (use as INSPIRATION ONLY — do NOT copy, quote, or closely paraphrase):
{book_page_text}

━━━━━━━━━━━━━━━━━━━━━━━━
COPYRIGHT SAFETY (MANDATORY — CHANNEL SURVIVAL DEPENDS ON THIS):
━━━━━━━━━━━━━━━━━━━━━━━━
- NEVER copy sentences or phrases from the book. Transform every idea into YOUR OWN words.
- NEVER mention the book name, author name, or any direct quotes.
- Take the CORE CONCEPT from the book and add YOUR OWN:
  → Real-world examples and scenarios (invent them — "Picture your friend who...")
  → Personal opinions and hot takes ("Here's what nobody realizes about this...")
  → Practical action steps the book doesn't mention
  → Connections to modern life, psychology studies, or pop culture
  → Contrarian angles — challenge or expand on the book's ideas
- The final script should feel like ORIGINAL ADVICE that was INSPIRED by a concept, NOT a book summary.
- A viewer should NEVER be able to tell this came from a specific book.

MISSION: Transform this into 3 viral YouTube Shorts with ORIGINAL commentary.
- Short 1: EMOTIONAL / STORYTELLING angle — invent a relatable scenario
- Short 2: DIRECT ADVICE / "HARD TRUTH" angle — add your own unique take
- Short 3: SERIES / COUNTDOWN angle — "Part X" or "3 things" format to drive binge-watching

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
LENGTH: 10-15 seconds of speaking content. That's 30-45 words TOTAL. NOT 70 words. NOT 60 words. MAXIMUM 45 WORDS.
Why? Shorter = higher completion rate = YouTube pushes to millions. A 12-second Short with 95% retention DESTROYS a 25-second Short with 50% retention.

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
{desc_style}

━━━━━━━━━━━━━━━━━━━━━━━━
TAG RULES:
━━━━━━━━━━━━━━━━━━━━━━━━
Provide {tag_count} tags per short. YouTube keyword tags, NOT hashtags.
- NEVER start a tag with # — just plain text
- NEVER use special characters: no &, no /, no quotes, no emojis
- ONLY use: letters, numbers, spaces, hyphens
- Mix: broad ("motivation"), mid ("success mindset"), long-tail ("how to build discipline")

Respond in this EXACT JSON format — no extra text outside the JSON:
{{
    "shorts": [
        {{
            "angle_type": "emotional storytelling",
            "youtube_title": "SPECIFIC personal title under 60 chars ending with #Shorts",
            "description": "Full description following structure above",
            "hook": "First punchy line — pattern interrupt — uses YOU",
            "script": "Full 30-45 word script. ULTRA SHORT. Every word earns its place.",
            "cta": "One short line that triggers rewatch or follow",
            "tags": ["shorts", "youtubeshorts", "... {tag_count} total unique tags"],
            "category_id": "22"
        }},
        {{
            "angle_type": "direct advice",
            "youtube_title": "SPECIFIC personal title under 60 chars ending with #Shorts",
            "description": "Full description following structure above",
            "hook": "First punchy line — pattern interrupt — uses YOU",
            "script": "Full 30-45 word script. ULTRA SHORT. Every word earns its place.",
            "cta": "One short line that triggers rewatch or follow",
            "tags": ["shorts", "youtubeshorts", "... {tag_count} total unique tags"],
            "category_id": "27"
        }},
        {{
            "angle_type": "series countdown",
            "youtube_title": "Use Part X or numbered list format — under 60 chars ending with #Shorts",
            "description": "Full description following structure above",
            "hook": "First punchy line — pattern interrupt — uses YOU",
            "script": "Full 30-45 word script. ULTRA SHORT. Every word earns its place.",
            "cta": "One short line that triggers rewatch or follow — mention next part",
            "tags": ["shorts", "youtubeshorts", "... {tag_count} total unique tags"],
            "category_id": "27"
        }}
    ]
}}
Only JSON. No extra text."""

    text = ask_groq(prompt)
    return parse_json_safe(text, retries_left=2, prompt=prompt)

def main():
    print("=" * 50)
    print("  NextLevelMind Shorts Generator — Groq")
    print(f"  Model: {GROQ_MODEL}")
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
        print("\n[1/3] Generating 3 shorts from book page...")
        script_data = write_shorts_scripts(book_page_text, current_book_name)
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(script_data, f, indent=2, ensure_ascii=False)
        short_idx = 0
    else:
        if not os.path.exists(cache_file):
            print(f"\n[1/3] No cache found, generating new...")
            book_page_text, current_book_name = get_book_page()
            script_data = write_shorts_scripts(book_page_text, current_book_name)
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(script_data, f, indent=2, ensure_ascii=False)
        else:
            print(f"\n[1/3] Loading script from cache for Video {video_num}...")
            with open(cache_file, "r", encoding="utf-8") as f:
                script_data = json.load(f)
        short_idx = int(video_num) - 1
        if short_idx >= len(script_data.get("shorts", [])):
            short_idx = len(script_data["shorts"]) - 1

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

    # Inject subscribe CTA before hashtags (critical for YPP subscriber growth)
    description = my_short.get("description", "")
    sub_cta = "\n\n🔔 Subscribe to @NextLevelMind for daily mindset shifts that actually work."
    if "@NextLevelMind" not in description:
        description = description.rstrip() + sub_cta

    # Ensure description always ends with a hashtag block
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