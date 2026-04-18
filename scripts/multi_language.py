"""
multi_language.py — Multi-Language Shorts Generator

Takes the English script sections already generated in output/sections/
and produces translated videos for each target language:

  1. Translates each section text via Gemini
  2. Generates voiceover in the target language via Edge TTS
  3. Assembles the video (reuses existing stock background)
  4. Saves translated video to output/lang_<code>/final_video.mp4

Supported languages:
  - Hindi    (hi) → hi-IN-MadhurNeural
  - Spanish  (es) → es-MX-JorgeNeural
  - Portuguese (pt) → pt-BR-AntonioNeural
  - Arabic   (ar) → ar-SA-HamedNeural

Usage:
  python scripts/multi_language.py              ← all 4 languages
  python scripts/multi_language.py hi es        ← only Hindi + Spanish

.env required: GEMINI_API_KEY
"""

import os
import sys
import json
import shutil
import asyncio
import subprocess
import textwrap
from dotenv import load_dotenv

load_dotenv()

try:
    from google import genai
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    GEMINI_AVAILABLE = True
except Exception:
    GEMINI_AVAILABLE = False

import edge_tts

TEXT_MODEL = "gemini-2.5-flash"

# Voice mapping — male motivational voices for each language
LANG_CONFIG = {
    "hi": {
        "name": "Hindi",
        "voice": "hi-IN-MadhurNeural",
        "title_prefix": "",
        "locale": "hi-IN",
    },
    "es": {
        "name": "Spanish",
        "voice": "es-MX-JorgeNeural",
        "title_prefix": "",
        "locale": "es-MX",
    },
    "pt": {
        "name": "Portuguese",
        "voice": "pt-BR-AntonioNeural",
        "title_prefix": "",
        "locale": "pt-BR",
    },
    "ar": {
        "name": "Arabic",
        "voice": "ar-SA-HamedNeural",
        "title_prefix": "",
        "locale": "ar-SA",
    },
}


def read_english_sections():
    """Read existing English section files from output/sections/."""
    sections_dir = "output/sections"
    if not os.path.exists(sections_dir):
        return {}
    sections = {}
    for fname in sorted(os.listdir(sections_dir)):
        if fname.endswith(".txt"):
            with open(os.path.join(sections_dir, fname), encoding="utf-8") as f:
                sections[fname] = f.read().strip()
    return sections


def translate_text(text, target_lang_name):
    """Translate text to target language using Gemini."""
    if not GEMINI_AVAILABLE:
        print(f"    Gemini not available — cannot translate")
        return None

    prompt = f"""Translate the following motivational/self-improvement text to {target_lang_name}.
Keep the tone powerful, direct, and conversational — like a coach speaking to someone.
Do NOT add any English text, explanations, or notes. Return ONLY the translated text.

Text to translate:
{text}"""

    try:
        response = client.models.generate_content(
            model=TEXT_MODEL,
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        print(f"    Translation failed: {e}")
        return None


def translate_seo(seo_data, target_lang_name, lang_code):
    """Translate title, description, and tags."""
    if not GEMINI_AVAILABLE:
        return None

    prompt = f"""Translate this YouTube Shorts metadata to {target_lang_name}.
Keep hashtags in the description. Translate the tags to {target_lang_name} equivalents.
Return as valid JSON with keys: youtube_title, description, tags (array of strings).
Do NOT include any markdown formatting or code blocks. Return ONLY the JSON.

Title: {seo_data.get('youtube_title', '')}

Description:
{seo_data.get('description', '')}

Tags: {json.dumps(seo_data.get('tags', []))}"""

    try:
        response = client.models.generate_content(
            model=TEXT_MODEL,
            contents=prompt,
        )
        text = response.text.strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        translated_seo = json.loads(text.strip())
        # Preserve non-translated fields
        translated_seo["category_id"] = seo_data.get("category_id", "27")
        return translated_seo
    except Exception as e:
        print(f"    SEO translation failed: {e}")
        return None


async def generate_voiceover_tts(text, voice, output_path):
    """Generate voiceover using Edge TTS for a specific language voice."""
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)


def generate_voiceovers(sections, lang_code, output_dir):
    """Generate voiceover MP3 for each translated section."""
    voice = LANG_CONFIG[lang_code]["voice"]
    os.makedirs(output_dir, exist_ok=True)

    for fname, text in sections.items():
        mp3_name = fname.replace(".txt", ".mp3")
        mp3_path = os.path.join(output_dir, mp3_name)
        try:
            asyncio.run(generate_voiceover_tts(text, voice, mp3_path))
            print(f"    {mp3_name} generated")
        except Exception as e:
            print(f"    {mp3_name} FAILED: {e}")


def get_duration(file):
    try:
        result = subprocess.run([
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            file
        ], capture_output=True, text=True, timeout=15)
        return float(result.stdout.strip())
    except Exception:
        return 0.0


def merge_voiceovers(vo_dir):
    """Merge all voiceover MP3s into one file."""
    sections = sorted([
        os.path.join(vo_dir, f) for f in os.listdir(vo_dir)
        if f.endswith(".mp3")
    ])
    if not sections:
        return None, 0

    list_file = os.path.join(vo_dir, "audio_list.txt")
    with open(list_file, "w") as f:
        for s in sections:
            safe = os.path.abspath(s).replace("\\", "/")
            f.write(f"file '{safe}'\n")

    merged = os.path.join(vo_dir, "full_voiceover.mp3")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", list_file,
        "-c:a", "libmp3lame", "-q:a", "2",
        merged
    ], capture_output=True)

    duration = get_duration(merged)
    return merged, duration


def assemble_translated_video(voiceover_path, duration, lang_dir):
    """Assemble video with stock background + translated voiceover."""
    import random

    # Pick a stock video
    stock_dir = "stock"
    stock_video = None
    if os.path.exists(stock_dir):
        videos = [
            os.path.join(stock_dir, f)
            for f in os.listdir(stock_dir)
            if f.lower().endswith((".mp4", ".mov", ".avi", ".mkv", ".webm"))
        ]
        if videos:
            stock_video = random.choice(videos)

    output_video = os.path.join(lang_dir, "final_video.mp4")

    if stock_video:
        stock_escaped = os.path.abspath(stock_video).replace("\\", "/")
        vf = ("loop=loop=-1:size=32767:start=0,"
              "scale=1080:1920:force_original_aspect_ratio=increase,"
              "crop=1080:1920,setsar=1")
        subprocess.run([
            "ffmpeg", "-y",
            "-i", stock_escaped,
            "-i", voiceover_path,
            "-vf", vf,
            "-t", str(duration),
            "-c:v", "libx264", "-preset", "medium", "-crf", "23",
            "-map", "0:v", "-map", "1:a",
            "-c:a", "aac", "-b:a", "128k",
            output_video
        ], capture_output=True)
    else:
        subprocess.run([
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", f"color=c=black:s=1080x1920:r=30:d={duration}",
            "-i", voiceover_path,
            "-c:v", "libx264", "-preset", "medium", "-crf", "23",
            "-map", "0:v", "-map", "1:a",
            "-c:a", "aac", "-b:a", "128k",
            output_video
        ], capture_output=True)

    if os.path.exists(output_video):
        size_mb = os.path.getsize(output_video) // (1024 * 1024)
        print(f"    Video assembled: {size_mb} MB")
        return output_video
    else:
        print(f"    Video assembly FAILED")
        return None


def process_language(lang_code, english_sections, seo_data):
    """Full pipeline for one language: translate → voiceover → assemble."""
    config = LANG_CONFIG[lang_code]
    lang_name = config["name"]
    lang_dir = f"output/lang_{lang_code}"
    os.makedirs(lang_dir, exist_ok=True)

    print(f"\n  {'='*45}")
    print(f"  {lang_name.upper()} ({lang_code})")
    print(f"  Voice: {config['voice']}")
    print(f"  {'='*45}")

    # Step 1 — Translate sections
    print(f"\n  [1/4] Translating {len(english_sections)} sections to {lang_name}...")
    translated_sections = {}
    sections_dir = os.path.join(lang_dir, "sections")
    os.makedirs(sections_dir, exist_ok=True)

    for fname, eng_text in english_sections.items():
        translated = translate_text(eng_text, lang_name)
        if translated:
            translated_sections[fname] = translated
            with open(os.path.join(sections_dir, fname), "w", encoding="utf-8") as f:
                f.write(translated)
            print(f"    {fname} translated")
        else:
            print(f"    {fname} FAILED — using English fallback")
            translated_sections[fname] = eng_text

    # Step 2 — Translate SEO metadata
    print(f"\n  [2/4] Translating SEO metadata...")
    translated_seo = translate_seo(seo_data, lang_name, lang_code)
    if translated_seo:
        with open(os.path.join(lang_dir, "seo_data.json"), "w", encoding="utf-8") as f:
            json.dump(translated_seo, f, indent=2, ensure_ascii=False)
        print(f"    Title: {translated_seo.get('youtube_title', 'N/A')}")
    else:
        print(f"    SEO translation failed — using English")

    # Step 3 — Generate voiceovers
    print(f"\n  [3/4] Generating {lang_name} voiceovers...")
    vo_dir = os.path.join(lang_dir, "voiceovers")
    generate_voiceovers(translated_sections, lang_code, vo_dir)

    # Merge voiceovers
    merged_vo, duration = merge_voiceovers(vo_dir)
    if not merged_vo:
        print(f"    No voiceovers generated — skipping {lang_name}")
        return False
    print(f"    Merged voiceover: {duration:.1f}s")

    # Step 4 — Assemble video
    print(f"\n  [4/4] Assembling {lang_name} video...")
    video_path = assemble_translated_video(merged_vo, duration, lang_dir)

    if video_path:
        print(f"\n  {lang_name} DONE! → {video_path}")
        return True
    return False


def main():
    print("=" * 50)
    print("  Multi-Language Shorts Generator")
    print("  Translate → Voiceover → Video")
    print("=" * 50)

    # Parse language arguments (default: all 4)
    args = sys.argv[1:]
    if args:
        target_langs = [a.strip().lower() for a in args if a.strip().lower() in LANG_CONFIG]
    else:
        target_langs = list(LANG_CONFIG.keys())

    if not target_langs:
        print("\n  No valid languages specified.")
        print(f"  Available: {', '.join(LANG_CONFIG.keys())}")
        return

    print(f"\n  Languages: {', '.join(LANG_CONFIG[l]['name'] for l in target_langs)}")

    # Read English sections
    english_sections = read_english_sections()
    if not english_sections:
        print("\n  ERROR: No English sections found in output/sections/")
        print("  Run 02_write_script.py first.")
        return

    print(f"  English sections: {len(english_sections)} files")

    # Read English SEO data
    seo_data = {}
    if os.path.exists("output/seo_data.json"):
        with open("output/seo_data.json", encoding="utf-8") as f:
            seo_data = json.load(f)

    # Process each language
    results = {}
    for lang_code in target_langs:
        success = process_language(lang_code, english_sections, seo_data)
        results[lang_code] = success

    # Summary
    print("\n" + "=" * 50)
    print("  MULTI-LANGUAGE RESULTS")
    print("=" * 50)
    for lc, ok in results.items():
        status = "OK" if ok else "FAILED"
        path = f"output/lang_{lc}/final_video.mp4"
        print(f"  {LANG_CONFIG[lc]['name']:12s} : {status:6s} → {path}")

    ok_count = sum(1 for v in results.values() if v)
    print(f"\n  {ok_count}/{len(results)} languages generated successfully")

    print("""
  NEXT STEPS:
  - Each language video is in output/lang_<code>/final_video.mp4
  - SEO data (translated) is in output/lang_<code>/seo_data.json
  - Upload each to its own YouTube channel manually
  - Or extend the upload script to handle multi-channel uploads
""")


if __name__ == "__main__":
    main()
