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

import time as _time

load_dotenv()
client = genai.Client()
MODEL = "gemini-2.5-flash"
FALLBACK_MODEL = "gemini-2.0-flash"

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

    # If pages were blank, advance and retry (loop instead of recursion)
    max_retries = 20
    while not page_text.strip() and max_retries > 0:
        max_retries -= 1
        print(f"  [!] Pages were blank — advancing...")
        page_text = ""
        start_page = progress["current_page"]
        try:
            with open(book_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                end_limit = len(reader.pages)
                if user_end_page != -1 and user_end_page < end_limit:
                    end_limit = user_end_page
                if start_page >= end_limit:
                    print(f"  [!] Reached end of {current_book} while skipping blanks.")
                    sys.exit(1)
                for p in range(start_page, min(start_page + pages_to_read, end_limit)):
                    extracted = reader.pages[p].extract_text()
                    if extracted:
                        page_text += extracted + "\n\n"
                progress["current_page"] = min(start_page + pages_to_read, end_limit)
                with open(progress_file, "w", encoding="utf-8") as f:
                    json.dump(progress, f, indent=2)
        except Exception as e:
            print(f"  [!] Error: {e}")
            sys.exit(1)

    if not page_text.strip():
        print(f"  [!] Could not find non-blank pages in {current_book}.")
        sys.exit(1)

    return page_text.strip(), current_book


def ask_gemini(prompt, max_tokens=16384):
    """
    Call Gemini with automatic retry + fallback model.
    Retries 3 times with exponential backoff on overload/rate-limit errors.
    Falls back to FALLBACK_MODEL if primary MODEL keeps failing.
    """
    for attempt in range(4):
        model = MODEL if attempt < 3 else FALLBACK_MODEL
        try:
            if attempt > 0:
                wait = min(2 ** attempt * 5, 60)
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
    prompt = f"""You are an elite YouTube retention strategist who understands exactly how the algorithm works for long-form content. You know that YouTube measures:
- Click-through rate (thumbnail + title → must be irresistible)
- Average view duration (AVD) — the #1 metric. If people watch 5+ minutes of an 8-minute video, YouTube pushes it to MILLIONS.
- Re-impressions: YouTube tests with 500-1000 impressions first. If AVD is high → 10K, 50K, 100K impressions.

Your job is to write scripts that KEEP PEOPLE WATCHING. Every sentence must earn the next 5 seconds of their attention.

INPUT BOOK TEXT (use as INSPIRATION ONLY — do NOT copy, quote, or closely paraphrase):
{book_page_text}

━━━━━━━━━━━━━━━━━━━━━━━━
COPYRIGHT SAFETY (MANDATORY — CHANNEL SURVIVAL DEPENDS ON THIS):
━━━━━━━━━━━━━━━━━━━━━━━━
- NEVER copy sentences or phrases from the book. Transform every idea into YOUR OWN words.
- NEVER mention the book name, author name, or any direct quotes.
- Take the CORE CONCEPTS from the book and add YOUR OWN:
  → Real-world examples and scenarios you create (e.g., "Imagine you're in a meeting and...")
  → Personal opinions and hot takes ("Here's what nobody realizes about this...")
  → Practical step-by-step action plans the book doesn't explicitly give
  → Connections to modern psychology studies, real research, or current trends
  → Contrarian angles — challenge, expand on, or combine the book's ideas with other concepts
  → Invented analogies and metaphors that make the concept memorable
- Each chapter should feel like an ORIGINAL LESSON inspired by a concept, NOT a book summary.
- The viewer should NEVER be able to tell this came from a specific book.
- At least 40% of each chapter's content should be YOUR original insight, examples, or commentary — not derived from the book text.

MISSION: Create a single 7-8 minute YouTube video script with ORIGINAL INSIGHTS that holds retention above 60%.
The video: stock video background, centered white text, phrase-by-phrase display. Like a cinematic experience.

━━━━━━━━━━━━━━━━━━━━━━━━
TITLE RULES (CLICK-THROUGH RATE):
━━━━━━━━━━━━━━━━━━━━━━━━
- NEVER include the book name
- Do NOT end with #Shorts
- Keep under 70 characters
- Must feel PERSONAL — use "You" or "Your" when possible
- Create a SPECIFIC curiosity gap — not vague motivation
- Include a number, a specific claim, or a pattern interrupt

BANNED TITLES (too generic, YouTube has seen them 1 million times):
❌ "7 Rules That Separate Winners From Everyone Else"
❌ "The Mindset That Makes Ordinary People Unstoppable"
❌ "Why 99% of People Stay Broke"
❌ "The Psychology Behind Every Successful Person"
❌ "How to Change Your Life in 30 Days"
❌ anything with "Secret" or "Nobody Tells You"

USE THESE PATTERNS INSTEAD (specific + curiosity):
✅ "You're Wasting 4 Hours Every Day And Don't Know It"
✅ "The Skill That Took Me From Broke to $10K/Month"
✅ "I Tracked My Habits for 90 Days. Here's What Happened."
✅ "Your Morning Routine Is Destroying Your Productivity"
✅ "5 Money Mistakes That Keep Smart People Poor"
✅ "The 2-Minute Rule That Fixed My Entire Life"
✅ "Why Discipline Fails (And What Actually Works)"
✅ "I Deleted Social Media for 30 Days. Everything Changed."
✅ "The Wealth Formula Rich People Learn at 18"
✅ "Stop Setting Goals. Do This Instead."

━━━━━━━━━━━━━━━━━━━━━━━━
STRUCTURE — THE RETENTION ARCHITECTURE:
━━━━━━━━━━━━━━━━━━━━━━━━
This structure is specifically designed to prevent viewer drop-off at every critical point.

1. INTRO — THE HOOK (20-30 seconds, ~70 words)
   YouTube analytics show most drop-off happens in the first 30 seconds. Your intro must:
   a) PATTERN INTERRUPT (first sentence): Shock, provoke, or call out the viewer directly.
      - "Stop everything you're doing. What I'm about to tell you could save you 10 years."
      - "You woke up this morning and made 3 mistakes before you even left your bed."
      - "There's a reason you feel stuck. And it's not what you think."
   b) OPEN LOOP (second part): Promise what's coming but DON'T deliver yet.
      - "By the end of this video, you'll understand the one pattern that separates people who break through from people who stay stuck forever."
      - "I'm going to show you 5 things. Number 4 will change how you see your entire life."
      - "There's one habit I'll share near the end that sounds stupid — but it's the reason people go from zero to six figures."
   c) CREDIBILITY SIGNAL: Why should they listen?
      - Use a stat, a research reference, or a bold specific claim.

2. CHAPTERS (5-6 chapters, each 55-75 seconds, ~160 words each)

   CRITICAL — EVERY CHAPTER MUST FOLLOW THIS PATTERN:
   a) MINI-HOOK (first 1-2 sentences): Re-grab attention. Viewers drift — pull them back.
      - "Here's where it gets interesting."
      - "This next part might make you uncomfortable."
      - "Now pay attention, because this is where most people give up."
      - "Remember what I said about [callback to intro]? This is why."
   b) CONTENT (core teaching): Deliver the value. Be SPECIFIC — use numbers, scenarios, actions.
      - NOT "You need discipline" → YES "Wake up at the same time for 21 days. Your brain physically rewires."
      - NOT "Read more books" → YES "Read 10 pages before you check your phone. In 30 days you've finished 2 books."
   c) TRANSITION HOOK (last sentence): Tease the NEXT chapter to prevent drop-off.
      - "But there's a catch — and it's in the next point."
      - "This alone won't save you. What comes next will."
      - "You're probably thinking this is enough. It's not. Keep watching."

   CHAPTER PACING:
   - Chapters 1-2: Build the foundation. Teach something they partly know — create familiarity.
   - Chapter 3: PATTERN BREAK — reveal something unexpected. Challenge a common belief. This is your mid-video retention spike.
   - Chapter 4-5: Deliver the highest value. The "golden nuggets" that make people save + share the video.
   - Chapter 5/6 (final): The payoff of the open loop from the intro. Deliver on your promise.

3. OUTRO (15-20 seconds, ~50 words)
   - Callback to the intro hook (loop closure)
   - ONE specific action they should take TODAY (not vague "start your journey")
   - Subtle CTA: "If this hit you, subscribe. I drop content like this every day."
   - End on a thought-provoking line that sticks in their head

━━━━━━━━━━━━━━━━━━━━━━━━
SCRIPT WRITING RULES:
━━━━━━━━━━━━━━━━━━━━━━━━
TOTAL: 1100-1400 words (7-8 minutes at speaking pace).

STYLE:
- American English. Conversational. Like a smart friend talking to you at 2 AM.
- Short sentences. 5-12 words each. Punchy rhythm.
- Use "you" and "your" constantly — the viewer must feel spoken to directly.
- SPECIFIC over generic. Always.
  ❌ "Successful people have good habits"
  ✅ "Jeff Bezos makes 3 decisions before 10 AM. Most people can't make 1."
- Use contrast pairs: "Most people do X. The top 1% do Y."
- Use numbers: "87% of people quit by week 3. Here's how to be in the 13%."
- Use scenarios: "Picture this. It's 5 AM. Your alarm goes off..."

RETENTION TRICKS (use at least 4 of these across the script):
- Foreshadowing: "There's something I'll share in chapter 4 that most people miss."
- Callbacks: "Remember that stat I mentioned earlier? Here's why it matters."
- Unexpected pivot: "Everything I just said? Forget it. Here's what actually matters."
- Direct challenge: "You're going to hear this and think it doesn't apply to you. It does."
- Countdown tension: "We're almost at the most important part. Stay with me."
- Social proof: "A study from [university] found..." or "The top [X] performers all do this."

━━━━━━━━━━━━━━━━━━━━━━━━
DESCRIPTION RULES (SEO — CRITICAL FOR SEARCH DISCOVERY):
━━━━━━━━━━━━━━━━━━━━━━━━
YouTube search is the #1 discovery source for long-form. Your description must be keyword-rich.

Line 1: [Primary keyword phrase] — [direct benefit, under 95 chars]
Line 2: [Secondary keyword phrase] | [curiosity hook or stat]
Line 3: (blank)
Line 4: Hook text from the video intro (exact first sentence)
Line 5-8: 3-4 sentences explaining what they'll learn — use searchable phrases naturally
Line 9: (blank)
Line 10: TIMESTAMPS_PLACEHOLDER
Line 11: (blank)
Line 12: Follow for daily content that changes how you think about success.
Line 13: 🔔 Subscribe — new video every single day
Line 14: 👍 Like if this shifted your perspective
Line 15: 💾 Save this — you'll want to rewatch it
Line 16: (blank)
Line 17: 15 hashtags: #motivation #mindset #selfimprovement #discipline #success #personaldevelopment #growthmindset #habits #productivity #mentalstrength #stoicism #wealthmindset #selfhelp #lifelessons #mindsetshift

━━━━━━━━━━━━━━━━━━━━━━━━
TAG RULES:
━━━━━━━━━━━━━━━━━━━━━━━━
Provide EXACTLY 32 tags. YouTube keyword tags, NOT hashtags.
- NEVER start a tag with #
- NEVER use special characters
- ONLY use: letters, numbers, spaces, hyphens
- Mix:
  - Broad: "motivation", "self improvement", "mindset", "success"
  - Mid: "daily habits", "success mindset", "morning routine", "productivity tips"
  - Long-tail: "how to be more disciplined", "how to build good habits", "self improvement for men"
  - Names: "atomic habits", "david goggins", "alex hormozi", "james clear", "stoicism"
  - Trending: "personal growth 2026", "mindset coach", "life advice", "how to be successful"

Respond in this EXACT JSON format — no extra text outside the JSON:
{{
    "youtube_title": "SPECIFIC curiosity-driven title under 70 chars, uses You/Your, no #Shorts",
    "description": "Full description following SEO structure above",
    "intro": "Full intro script (20-30 sec, ~70 words). MUST have: pattern interrupt + open loop + credibility signal.",
    "chapters": [
        {{
            "chapter_title": "Short Chapter Title (2-5 words)",
            "script": "Full chapter (55-75 sec, ~160 words). MUST have: mini-hook + content + transition hook to next chapter."
        }},
        {{
            "chapter_title": "Short Chapter Title",
            "script": "Full chapter — each one follows the mini-hook → content → transition pattern"
        }}
    ],
    "outro": "Full outro (15-20 sec, ~50 words). Callback to intro + specific action + subtle CTA.",
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

    # Save section files — clear old sections first to prevent stale text
    print("\n[2/3] Saving text sections...")
    if os.path.exists("output/sections"):
        import shutil
        shutil.rmtree("output/sections")
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
