import os
import sys
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

load_dotenv()
# API key is read automatically from GEMINI_API_KEY environment variable
client = genai.Client()
MODEL = "gemini-2.5-flash"

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
    response = client.models.generate_content(model=MODEL, contents=prompt)
    text = response.text.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    return text

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


def write_shorts_scripts(book_page_text, book_name):
    performance_context = _build_performance_context()

    prompt = f"""You are a top-tier YouTube Shorts Growth Expert specialized in viral content for the USA market (18-35 audience).

{performance_context}INPUT BOOK PAGE TEXT (use concepts and wisdom from this — but NEVER mention the book name):
{book_page_text}

MISSION: Transform this into 2 viral YouTube Shorts.
- Short 1: EMOTIONAL / STORYTELLING angle
- Short 2: DIRECT ADVICE / "HARD TRUTH" angle

━━━━━━━━━━━━━━━━━━━━━━━━
TITLE RULES (CRITICAL FOR ALGORITHM):
━━━━━━━━━━━━━━━━━━━━━━━━
- NEVER include the book name. Nobody searches for a book they haven't read.
- ALWAYS end the title with #Shorts (YouTube algorithm signal).
- Keep under 60 characters (mobile display limit).
- Create curiosity WITHOUT revealing the answer.
- Use one of these proven viral patterns:

  EMOTIONAL patterns:
  • "Nobody Told Me This Would Change Everything #Shorts"
  • "I Wish Someone Had Told Me This Sooner #Shorts"
  • "The Lesson That Actually Changed My Life #Shorts"
  • "What Winners Do That Nobody Ever Sees #Shorts"
  • "One Story That Will Rewire Your Brain #Shorts"
  • "The Mindset Shift That Changes Everything #Shorts"

  ADVICE patterns:
  • "Stop Doing This If You Want to Actually Win #Shorts"
  • "The Brutal Truth About Why You're Still Losing #Shorts"
  • "99% of People Get This Completely Wrong #Shorts"
  • "This Is Exactly Why You're Still Struggling #Shorts"
  • "You're 1 Decision Away From Changing Everything #Shorts"
  • "What Nobody Tells You About [topic] #Shorts"

━━━━━━━━━━━━━━━━━━━━━━━━
DESCRIPTION RULES (CRITICAL FOR SEO):
━━━━━━━━━━━━━━━━━━━━━━━━
YouTube only shows 1-2 lines before "Show more" — those lines are your SEO goldmine.

EXACT STRUCTURE (follow precisely):
Line 1: [Primary keyword phrase] — [direct benefit or shocking fact, under 95 chars]
Line 2: [Secondary keyword phrase] | [curiosity gap or stat that hooks them]
Line 3: (blank)
Line 4: Hook text from the video
Line 5-8: 3-4 sentences of value/context
Line 9: (blank)
Line 10: Follow for daily [topic] content that actually works.
Line 11: 🔔 Subscribe — new short every single day
Line 12: 👍 Like if this hit different
Line 13: 💾 Save this — you'll need it when life gets hard
Line 14: (blank)
Line 15: HASHTAG BLOCK — exactly 15 hashtags, starting with #Shorts #YouTubeShorts then niche-specific

EMOTIONAL description example:
"How to build a success mindset that separates winners from everyone else
Success mindset secrets | The habit 92% of people skip but winners never do

[hook text]
[content value]

Follow for daily mindset content that hits different every time.
🔔 Subscribe — new short every day
👍 Like if this hit different
💾 Save this for when you need it most

#Shorts #YouTubeShorts #motivation #mindset #selfimprovement #discipline #successmindset #growthmindset #personaldevelopment #dailyhabits #mentalstrength #stoicism #motivationalvideo #consistency #inspiration"

ADVICE description example:
"The no-nonsense discipline guide that top 1% use and nobody else will tell you
Daily discipline tips | 87% of people fail here — here is exactly how to fix it

[hook text]
[content value]

Follow for brutal, honest success content that actually changes lives.
🔔 Subscribe — daily mindset drops
👍 Like if this woke you up
💾 Save this — share it with someone who needs it

#Shorts #YouTubeShorts #discipline #successmindset #motivation #productivity #wealthmindset #billionairehabits #hustle #noexcuses #hardtruth #selfimprovement #realadvice #mentalstrength #workethhic"

━━━━━━━━━━━━━━━━━━━━━━━━
TAG RULES:
━━━━━━━━━━━━━━━━━━━━━━━━
Provide EXACTLY 32 tags per short. Mix:
- Broad (high traffic): "motivation", "self improvement", "mindset", "success", "discipline"
- Mid (medium traffic): "daily habits", "morning routine", "success mindset", "mental strength"
- Long-tail (high intent): "how to be disciplined", "how to build good habits", "self improvement tips"
- Viral names/books: "atomic habits", "stoicism", "david goggins", "alex hormozi", "james clear"
- Niche: "motivationalvideo", "selfhelp", "personalgrowth", "mindsetshift", "successhabits"

━━━━━━━━━━━━━━━━━━━━━━━━
SCRIPT RULES:
━━━━━━━━━━━━━━━━━━━━━━━━
- American English, short punchy sentences, zero robotic phrasing
- First line = hook (must make them STOP scrolling in 1 second)
- High pacing — every sentence must earn its place
- 45-55 seconds of speaking content (about 120-140 words)
- End with a thought-provoking statement, not a question

Respond in this EXACT JSON format — no extra text outside the JSON:
{{
    "shorts": [
        {{
            "angle_type": "emotional storytelling",
            "youtube_title": "Viral title under 60 chars ending with #Shorts",
            "description": "Full description following the exact structure above",
            "hook": "First punchy line that stops the scroll",
            "script": "Full 120-140 word narration script",
            "cta": "Subtle viral call to action",
            "tags": ["shorts", "youtubeshorts", "... exactly 30 more unique tags"],
            "category_id": "22"
        }},
        {{
            "angle_type": "direct advice",
            "youtube_title": "Viral title under 60 chars ending with #Shorts",
            "description": "Full description following the exact structure above",
            "hook": "First punchy line that stops the scroll",
            "script": "Full 120-140 word narration script",
            "cta": "Subtle viral call to action",
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
    os.makedirs("output/sections", exist_ok=True)
    with open("output/sections/01_hook.txt", "w", encoding="utf-8") as f:
        f.write(my_short["hook"])
    with open("output/sections/02_script.txt", "w", encoding="utf-8") as f:
        f.write(my_short["script"])
    with open("output/sections/03_cta.txt", "w", encoding="utf-8") as f:
        f.write(my_short["cta"])

    # Inject trending tags (Phase 5) — mix Google Trends keywords into tags
    tags = my_short["tags"]
    if _TRENDING_AVAILABLE:
        print("\n  Fetching trending tags from Google Trends...")
        trending = get_trending_tags(category="general")
        # Merge: deduplicate, trending tags at end
        existing_lower = {t.lower() for t in tags}
        for t in trending:
            if t.lower() not in existing_lower:
                tags.append(t)
                existing_lower.add(t.lower())

    # Update seo_data.json
    seo_data = {
        "youtube_title": my_short["youtube_title"],
        "description": my_short["description"],
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