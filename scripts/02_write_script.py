import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq
import PyPDF2

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"

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
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.85,
        max_tokens=max_tokens
    )
    text = response.choices[0].message.content.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    return text

def parse_json_safe(text, retries_left=2, prompt=None):
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

def write_shorts_scripts(book_page_text, book_name):
    # Clean book name (remove .pdf)
    clean_name = book_name.replace(".pdf", "").replace("_", " ").title()
    
    prompt = f"""You are a top-tier YouTube Growth Expert & Strategist specialized in the USA market.
Your goal is to build a massive, high-retention brand for {clean_name}.

INPUT BOOK PAGE TEXT:
{book_page_text}

MISSION:
Transform this dry text into 2 viral YouTube Shorts (USA Target 18-35).
One must be EMOTIONAL/STORYTELLING.
One must be DIRECT ADVICE / "HARD TRUTH".

RULES FOR ELITE CONTENT:
1. TITLES: Use "fancy", curiosity-driven terms. MUST follow format "{clean_name}: [Viral Subtitle]".
   Example: "{clean_name}: The Habit That Will Bankrupt You" or "{clean_name}: Why You're Losing The War."
2. DESCRIPTION: Write a high-engaging, SEO-rich description using industrial "fancy" terms.
   Include a curiosity gap: "Most people fail because [concept]... but when you master this..."
3. HASHTAGS: Use at least 15 relevant, high-traffic hashtags specific to the shorts niche (e.g. #wealthmindset #stoicism #discipline #successsecrets).
4. SCRIPT: American English, short sentences, high-pacing. 0% robotic.

Respond in this exact JSON format:
{{
    "shorts": [
        {{
            "angle_type": "emotional storytelling",
            "youtube_title": "{clean_name}: Viral Subtitle",
            "description": "Fancy engaging SEO description with curiosity gaps",
            "hook": "hook text",
            "script": "full script",
            "cta": "subtle viral CTA",
            "tags": ["shorts", "mindset", "success", "... 12 more tags"]
        }},
        {{
            "angle_type": "direct advice",
            "youtube_title": "{clean_name}: Viral Subtitle",
            "description": "Fancy engaging SEO description with curiosity gaps",
            "hook": "hook text",
            "script": "full script",
            "cta": "subtle viral CTA",
            "tags": ["shorts", "discipline", "money", "... 12 more tags"]
        }}
    ]
}}
Only JSON. No extra text."""

    text = ask_groq(prompt)
    return parse_json_safe(text, retries_left=2, prompt=prompt)

def main():
    print("=" * 50)
    print("  NextLevelMind Shorts Generator — Groq")
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

    # Update seo_data.json
    seo_data = {
        "youtube_title": my_short["youtube_title"],
        "description": my_short["description"], 
        "tags": my_short["tags"],
        "keywords": my_short["tags"],
        "category": "Education"
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