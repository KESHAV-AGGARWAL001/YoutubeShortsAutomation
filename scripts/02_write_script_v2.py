"""
02_write_script_v2.py — Retention-Optimized Shorts Script Generator

V2 improvements over v1:
  - Hook-first structure with open loops, scroll stoppers, FOMO triggers
  - Stronger loop endings that force rewatches
  - HuggingFace Inference API support (Gemma / any model) — no GPU needed
  - Falls back to Gemini if HuggingFace fails (or vice versa)

.env config:
  AI_PROVIDER=gemini          # "gemini" (default) or "huggingface"
  HF_TOKEN=hf_xxxxxxxx       # HuggingFace access token
  HF_MODEL=google/gemma-3-27b-it  # Any HF model with chat support
"""

import os
import sys
import re
import json
import random
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

# ── AI Provider Setup ────────────────────────────────────────────────
AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini").strip().lower()

# Gemini client
_gemini_client = None
try:
    from google import genai
    _gemini_client = genai.Client()
except Exception:
    pass

GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_FALLBACK = "gemini-2.0-flash"

# HuggingFace client
_hf_client = None
HF_MODEL = os.getenv("HF_MODEL", "google/gemma-3-27b-it")
try:
    from huggingface_hub import InferenceClient
    hf_token = os.getenv("HF_TOKEN", "").strip()
    if hf_token:
        _hf_client = InferenceClient(token=hf_token)
except Exception:
    pass


def ask_ai(prompt, max_tokens=8192):
    """
    Route to the configured AI provider.
    Falls back to the other provider if the primary one fails.
    """
    providers = []
    if AI_PROVIDER == "huggingface" and _hf_client:
        providers = [("huggingface", _ask_huggingface)]
        if _gemini_client:
            providers.append(("gemini", _ask_gemini))
    else:
        if _gemini_client:
            providers = [("gemini", _ask_gemini)]
        if _hf_client:
            providers.append(("huggingface", _ask_huggingface))

    if not providers:
        raise RuntimeError("No AI provider available. Set GEMINI_API_KEY or HF_TOKEN in .env")

    for name, fn in providers:
        try:
            print(f"  Using AI provider: {name}")
            return fn(prompt, max_tokens)
        except Exception as e:
            print(f"  {name} failed: {e}")
            if name != providers[-1][0]:
                print(f"  Falling back to next provider...")
            else:
                raise


def _ask_gemini(prompt, max_tokens=8192):
    """Call Gemini with retry + fallback model."""
    for attempt in range(4):
        model = GEMINI_MODEL if attempt < 3 else GEMINI_FALLBACK
        try:
            if attempt > 0:
                wait = min(2 ** attempt * 5, 60)
                print(f"  Retry {attempt}/3 — waiting {wait}s... (model: {model})")
                _time.sleep(wait)
            response = _gemini_client.models.generate_content(model=model, contents=prompt)
            text = response.text.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            if attempt == 3:
                print(f"  Fallback model ({GEMINI_FALLBACK}) succeeded!")
            return text
        except Exception as e:
            err = str(e).lower()
            if any(k in err for k in ["429", "overloaded", "resource", "quota", "rate", "unavailable", "503", "500"]):
                if attempt < 3:
                    print(f"  Gemini overloaded — will retry...")
                    continue
            raise


def _ask_huggingface(prompt, max_tokens=8192):
    """Call HuggingFace Inference API with the configured model."""
    print(f"  HuggingFace model: {HF_MODEL}")

    for attempt in range(3):
        try:
            if attempt > 0:
                wait = 10 * attempt
                print(f"  Retry {attempt}/2 — waiting {wait}s...")
                _time.sleep(wait)

            response = _hf_client.chat_completion(
                model=HF_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
            )
            text = response.choices[0].message.content.strip()

            # Extract JSON from code blocks if present
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()

            return text

        except Exception as e:
            err = str(e).lower()
            if any(k in err for k in ["429", "overloaded", "rate", "503", "500"]):
                if attempt < 2:
                    continue
            raise


# ── Core channel tags ────────────────────────────────────────────────
CORE_TAGS = [
    "shorts", "youtubeshorts", "motivation", "mindset", "discipline",
    "selfimprovement", "success", "mentalstrength", "habits", "growthmindset",
    "personaldevelopment", "consistency", "focus", "hustle", "stoicism",
    "dailymotivation", "successmindset", "productivity", "selfhelp", "inspiration",
]

FALLBACK_HASHTAGS = (
    "#Shorts #YouTubeShorts #motivation #mindset #selfimprovement "
    "#discipline #success #mentalstrength #habits #growthmindset "
    "#personaldevelopment #consistency #hustle #stoicism #dailymotivation"
)

# ── Amazon Affiliate Links ──────────────────────────────────────────
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
                print(f"  [!] Reached end page ({end_limit}) of {current_book}.")
                sys.exit(1)

            if start_page < end_limit:
                extracted_text = reader.pages[start_page].extract_text()
                if extracted_text:
                    page_text += extracted_text + "\n\n"
            if start_page + 1 < end_limit:
                extracted_text2 = reader.pages[start_page + 1].extract_text()
                if extracted_text2:
                    page_text += extracted_text2 + "\n\n"
            next_page = min(start_page + 2, end_limit)
    except Exception as e:
        print(f"  [!] Error reading {current_book}: {e}")
        sys.exit(1)

    progress["current_page"] = next_page
    with open(progress_file, "w", encoding="utf-8") as f:
        json.dump(progress, f, indent=2)

    print(f"  [+] Reading from {current_book} (Pages: {start_page}-{min(start_page + 1, end_limit - 1)})")
    if not page_text.strip():
        return get_book_page()
    return page_text.strip(), current_book


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
            new_text = ask_ai(prompt)
            return parse_json_safe(new_text, retries_left - 1, prompt)
        raise ValueError(f"Failed to parse JSON. Raw:\n{text[:500]}")


def _build_performance_context():
    if not _ANALYTICS_AVAILABLE:
        return ""
    try:
        patterns = get_top_patterns(top_n=3)
        if not patterns:
            return ""
        lines = ["━━━━━━━━━━━━━━━━━━━━━━━━",
                 "PERFORMANCE INTELLIGENCE (A/B data — use winning patterns MORE):"]
        for p in patterns:
            lines.append(
                f"  Pattern [{p['pattern']}] — avg {p['avg_views']:,} views | "
                f"Best: \"{p['best_title'][:60]}\""
            )
        lines.append("Use winning patterns above. Avoid patterns NOT listed here.")
        return "\n".join(lines) + "\n"
    except Exception:
        return ""


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
    book_lower = os.path.splitext(book_name)[0].lower()
    for key, url in AFFILIATE_LINKS.items():
        if key in book_lower or book_lower in key:
            return os.path.splitext(book_name)[0], url
    return os.path.splitext(book_name)[0], None


def build_affiliate_section(book_name):
    book_title, book_url = get_book_affiliate_link(book_name)
    lines = []
    if book_url:
        lines.append(f"\n\n📚 Book from this video:")
        lines.append(f"👉 {book_title} — {book_url}")
    lines.append(f"\n📚 Books that changed my life:")
    for title, url in RECOMMENDED_BOOKS:
        lines.append(f"👉 {title} — {url}")
    return "\n".join(lines)


# ── Description styles (randomized per run) ──────────────────────────
DESCRIPTION_STYLES = [
    """Write a natural, unique description. Do NOT follow a rigid template. Include:
- A compelling opening line that hooks the reader (different every time)
- 2-3 sentences about what the viewer will learn or feel
- A personal CTA (vary it — not always "subscribe" or "like")
- 5-8 hashtags at the end (start with #Shorts, rest are niche-specific, VARY them each time)
Do NOT use emoji-heavy CTA blocks. Write it like a real person, not a bot.""",

    """Write a SHORT description (3-5 lines max). No fluff. Include:
- One powerful sentence about the video's core message
- One line of value or a bold claim
- 5-6 hashtags at the end (start with #Shorts)
Do NOT add subscribe/like/save CTAs. Keep it clean and minimal.""",

    """Write the description as a mini-story or thought. Include:
- Start with a question or a "what if" scenario
- 2-3 lines that build curiosity about the video
- End with a casual CTA (like "watch till the end" or "think about this tonight")
- 6-8 hashtags at the end (start with #Shorts)
No rigid format. Make it feel like a journal entry or a tweet thread.""",

    """Write a natural description optimized for YouTube search. Include:
- Open with a searchable keyword phrase woven into a natural sentence
- 2-3 sentences of value using different keyword variations
- One line encouraging engagement (vary the CTA every time — be creative)
- 5-7 hashtags at the end (start with #Shorts)
Make it feel like a human wrote it, not a template.""",
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# V2 RETENTION-OPTIMIZED PROMPT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def write_shorts_scripts(book_page_text, book_name):
    performance_context = _build_performance_context()

    desc_style = random.choice(DESCRIPTION_STYLES)
    tag_count = random.randint(8, 12)
    style_idx = DESCRIPTION_STYLES.index(desc_style)
    style_names = ["structured", "minimal", "story-driven", "SEO-conversational"]
    print(f"  Prompt style: {style_names[style_idx]} | Tags: {tag_count}")

    prompt = f"""You are an elite YouTube Shorts viral content strategist specializing in RETENTION.
Your #1 metric is COMPLETION RATE. A 15-second Short with 95% retention beats a 50-second Short with 40% retention. Every word, every second must EARN the viewer's attention.

{performance_context}INPUT BOOK PAGE TEXT (use as INSPIRATION ONLY — do NOT copy, quote, or closely paraphrase):
{book_page_text}

━━━━━━━━━━━━━━━━━━━━━━━━
COPYRIGHT SAFETY (MANDATORY — CHANNEL SURVIVAL):
━━━━━━━━━━━━━━━━━━━━━━━━
- NEVER copy sentences or phrases from the book. Transform every idea into YOUR OWN words.
- NEVER mention the book name, author name, or any direct quotes.
- Take the CORE CONCEPT and add YOUR OWN:
  → Real-world examples and scenarios (invent them — "Picture your friend who...")
  → Personal opinions and hot takes ("Here's what nobody realizes about this...")
  → Practical action steps the book doesn't mention
  → Connections to modern life, psychology studies, or pop culture
  → Contrarian angles — challenge or expand on the book's ideas
- The final script must feel like ORIGINAL ADVICE inspired by a concept, NOT a book summary.
- A viewer should NEVER be able to tell this came from a specific book.

MISSION: Transform this into 3 viral YouTube Shorts with ORIGINAL commentary.
- Short 1: EMOTIONAL / STORYTELLING angle — invent a relatable scenario
- Short 2: DIRECT ADVICE / "HARD TRUTH" angle — add your own unique take
- Short 3: SERIES / COUNTDOWN angle — "Part X" or "3 things" format to drive binge-watching

━━━━━━━━━━━━━━━━━━━━━━━━
TITLE RULES (CRITICAL FOR CTR):
━━━━━━━━━━━━━━━━━━━━━━━━
- NEVER include the book name.
- ALWAYS end with #Shorts.
- Keep under 60 characters.
- Must feel PERSONAL — use "You" or "Your" when possible.
- Create a SPECIFIC curiosity gap — not vague motivation.

BANNED TITLES (overused — YouTube suppresses these):
  ❌ "I Wish Someone Had Told Me This Sooner"
  ❌ "The Brutal Truth About Why You're Still Losing"
  ❌ "The Lesson That Actually Changed My Life"
  ❌ "What Winners Do That Nobody Ever Sees"
  ❌ "The Mindset Shift That Changes Everything"
  ❌ "99% of People Get This Completely Wrong"

USE THESE PATTERNS INSTEAD (SPECIFIC + PERSONAL):
  ✅ "You Do THIS Every Morning And It's Destroying You #Shorts"
  ✅ "Your Brain Is Lying to You Right Now #Shorts"
  ✅ "Delete This One Habit Or Stay Broke Forever #Shorts"
  ✅ "3 Seconds. That's All You Get. #Shorts"
  ✅ "You're Not Lazy. You're Doing This Wrong. #Shorts"
  ✅ "Rich People Never Say This Word #Shorts"
  ✅ "Your Phone Is Eating Your Future #Shorts"
  ✅ "This 10-Second Test Reveals Everything #Shorts"

━━━━━━━━━━━━━━━━━━━━━━━━
SCRIPT RULES — RETENTION ENGINE (V2):
━━━━━━━━━━━━━━━━━━━━━━━━
LENGTH: 10-15 seconds speaking. That's 30-45 words TOTAL. MAXIMUM 45 WORDS. Shorter = higher completion rate = algorithm pushes harder.
Short = higher completion = YouTube pushes to millions.

STRUCTURE — Every script MUST follow this EXACT flow:

1. HOOK (first 1-2 seconds) — THE MOST IMPORTANT PART.
   80% of viewers decide to stay or scroll in the first 2 seconds.
   Your hook must be a SCROLL STOPPER.

   HOOK RULES:
   - OPEN WITH A SHOCK, ACCUSATION, OR BOLD CLAIM — never ease in
   - Start with "You" or a direct command
   - Include an OPEN LOOP — hint something important is coming but DON'T reveal it yet
   - Use specific numbers or timeframes — "3 seconds", "90%", "every single morning"
   - Create FOMO — make them feel they'll LOSE something if they scroll away

   PROVEN HOOK FORMULAS (use as templates, never copy exactly):
   ✅ "You lost 3 hours today and didn't even notice."
   ✅ "Stop. The thing you just did 5 minutes ago is the reason you're stuck."
   ✅ "Your brain made a decision this morning that ruined your entire day."
   ✅ "90% of people will scroll past this. The 10% who stay will understand."
   ✅ "There's one word destroying your life and you say it every single day."

   BANNED HOOK PATTERNS (these KILL retention):
   ❌ Starting with a question ("Did you know...?", "What if I told you...?")
   ❌ Starting with greetings ("Hey", "Alright guys", "So", "Welcome")
   ❌ Starting with "Here's the thing" or "The truth is"
   ❌ Generic statements without specifics ("Most people fail because...")
   ❌ Quoting someone ("As [person] once said...")
   ❌ "In this video" or "Today I want to talk about"

2. BODY (10-18 seconds) — ONE single powerful idea. Not 3 ideas. Not a list. ONE.
   - Short punchy sentences. 5-10 words each.
   - Every sentence must create tension or reveal
   - Use "you" and "your" constantly — personal and direct
   - Phrase-by-phrase rhythm: statement. pause. reveal. pause. impact.
   - CLOSE THE OPEN LOOP from the hook — deliver the payoff here
   - Add one UNEXPECTED TWIST the viewer won't see coming
   - Build towards the ending — each sentence raises the stakes

3. LOOP ENDING (last sentence, 2-3 seconds) — Forces REWATCHES.
   Rewatches = YouTube pushes harder = more views. This is the secret weapon.

   LOOP ENDING RULES:
   - CALLBACK the exact phrase or image from the hook
   - The ending must make the viewer feel INCOMPLETE — like they need to rewatch
   - Create a circular moment: the last words should echo the first words

   EXAMPLES:
   - If hook is "You lost 3 hours today..." → end: "...and tomorrow, you'll lose 3 more. Unless you stop right now."
   - If hook is "Your brain made a decision..." → end: "...and your brain is about to make the same decision again."
   - If hook is "There's one word destroying your life..." → end: "...and you almost said it again just now."

   BANNED ENDINGS (these kill loop rate):
   ❌ "Subscribe for more" / "Follow for more" / "Like and share"
   ❌ "Let me know in the comments"
   ❌ "Stay tuned for part 2"
   ❌ Any generic CTA — the LOOP IS the CTA

WRITING STYLE:
- American English. Conversational. Raw.
- NO filler words. NO "basically", "actually", "honestly", "look"
- NO generic motivation. Be SPECIFIC. Use numbers, scenarios, actions.
- Write like you're texting a friend a hard truth at 2 AM.

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
            "hook": "First punchy line — scroll stopper with OPEN LOOP — uses YOU",
            "script": "Full 30-45 word script. ULTRA SHORT. Hook → Body (ONE idea + twist) → Loop ending.",
            "cta": "Loop ending line that callbacks the hook and forces rewatch",
            "tags": ["shorts", "youtubeshorts", "... {tag_count} total unique tags"],
            "category_id": "22"
        }},
        {{
            "angle_type": "direct advice",
            "youtube_title": "SPECIFIC personal title under 60 chars ending with #Shorts",
            "description": "Full description following structure above",
            "hook": "First punchy line — scroll stopper with OPEN LOOP — uses YOU",
            "script": "Full 30-45 word script. ULTRA SHORT. Hook → Body (ONE idea + twist) → Loop ending.",
            "cta": "Loop ending line that callbacks the hook and forces rewatch",
            "tags": ["shorts", "youtubeshorts", "... {tag_count} total unique tags"],
            "category_id": "27"
        }},
        {{
            "angle_type": "series countdown",
            "youtube_title": "Use Part X or numbered list format — under 60 chars ending with #Shorts",
            "description": "Full description following structure above",
            "hook": "First punchy line — scroll stopper with OPEN LOOP — uses YOU",
            "script": "Full 30-45 word script. ULTRA SHORT. Hook → Body (ONE idea + twist) → Loop ending.",
            "cta": "Loop ending that mentions next part to drive binge-watching",
            "tags": ["shorts", "youtubeshorts", "... {tag_count} total unique tags"],
            "category_id": "27"
        }}
    ]
}}
Only JSON. No extra text."""

    text = ask_ai(prompt)
    return parse_json_safe(text, retries_left=2, prompt=prompt)


def main():
    provider_label = "HuggingFace" if AI_PROVIDER == "huggingface" else "Gemini"
    model_label = HF_MODEL if AI_PROVIDER == "huggingface" else GEMINI_MODEL
    print("=" * 50)
    print("  NextLevelMind Shorts Generator — V2 Retention")
    print(f"  AI Provider: {provider_label} ({model_label})")
    print("=" * 50)

    video_num = os.environ.get("VIDEO_NUMBER", "1")
    cache_file = "book_shorts_cache.json"

    print(f"\n  Video        : #{video_num}")

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

    tags = list(CORE_TAGS)
    existing_lower = {t.lower() for t in tags}
    for t in my_short.get("tags", []):
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

    description = my_short.get("description", "")
    if "@NextLevelMind" not in description:
        description = description.rstrip() + "\n\n🔔 Subscribe to @NextLevelMind for daily mindset shifts that actually work."
    if "#Shorts" not in description and "#shorts" not in description:
        description = description.rstrip() + "\n\n" + FALLBACK_HASHTAGS
        print("  [!] AI omitted hashtags — fallback block appended")

    try:
        affiliate_section = build_affiliate_section(current_book_name)
        description = description.rstrip() + "\n" + affiliate_section
        print("  [+] Affiliate links appended")
    except Exception:
        pass

    tags = sanitize_tags(tags)
    print(f"  Tags     : {len(tags)} tags ({sum(len(t) for t in tags)} chars)")

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
