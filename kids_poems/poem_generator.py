"""
poem_generator.py — AI Poem + SEO Generator for Kids Channel

Uses Gemini to generate original children's poems.
Falls back to HuggingFace if Gemini is overloaded.

Fallback chain: Gemini Pro → Gemini Flash → HuggingFace
"""

import os
import sys
import json
import random
import time
import urllib.request
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import (
    GEMINI_API_KEY, GEMINI_MODEL, POEM_CATEGORIES, OUTPUT_FOLDER,
    POEMS_FOLDER, DEFAULT_TAGS, CHANNEL_NAME,
    HF_TOKEN, HF_TEXT_MODEL,
)

from google import genai

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
FALLBACK_MODEL = "gemini-2.0-flash"

HF_API_URL = "https://api-inference.huggingface.co/models/"


def ask_huggingface(prompt, model=None):
    """Call HuggingFace Inference API as fallback."""
    model = model or HF_TEXT_MODEL
    url = f"{HF_API_URL}{model}"

    payload = json.dumps({
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 1024,
            "temperature": 0.7,
            "return_full_text": False,
        },
    }).encode()

    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "LittleStarFactory/1.0",
    }

    for attempt in range(3):
        try:
            if attempt > 0:
                wait = 10 * attempt
                print(f"  HF retry {attempt}/2 — waiting {wait}s...")
                time.sleep(wait)

            req = urllib.request.Request(url, data=payload, headers=headers)
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode())

            if isinstance(result, list) and result:
                text = result[0].get("generated_text", "")
            elif isinstance(result, dict):
                text = result.get("generated_text", "") or result.get("error", "")
                if "error" in result and "loading" in result.get("error", "").lower():
                    print(f"  Model loading — waiting 30s...")
                    time.sleep(30)
                    continue
            else:
                text = str(result)

            text = text.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()

            if text.startswith("{"):
                return text

            json_start = text.find("{")
            if json_start >= 0:
                return text[json_start:]

            return text

        except Exception as e:
            if attempt < 2:
                continue
            raise

    raise RuntimeError("HuggingFace API failed after 3 attempts")


def ask_gemini(prompt, model=None):
    """Call Gemini API with retry, then fall back to HuggingFace."""
    model = model or GEMINI_MODEL

    if client:
        for attempt in range(4):
            use_model = model if attempt < 3 else FALLBACK_MODEL
            try:
                if attempt > 0:
                    wait = min(2 ** attempt * 5, 60)
                    print(f"  Retry {attempt}/3 — waiting {wait}s... (model: {use_model})")
                    time.sleep(wait)
                response = client.models.generate_content(
                    model=use_model, contents=prompt
                )
                text = response.text.strip()
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0].strip()
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0].strip()
                return text
            except Exception as e:
                err = str(e).lower()
                if any(k in err for k in ["429", "overloaded", "resource", "quota", "rate"]):
                    if attempt < 3:
                        continue
                    print(f"  Gemini overloaded — switching to HuggingFace...")
                    break
                raise

    if HF_TOKEN:
        print(f"  Using HuggingFace: {HF_TEXT_MODEL}")
        return ask_huggingface(prompt)

    raise RuntimeError(
        "Both Gemini and HuggingFace unavailable. "
        "Set KP_GEMINI_API_KEY or HF_TOKEN in kids_poems/.env"
    )


def sanitize_json(text):
    result = []
    in_str = False
    for i, ch in enumerate(text):
        if ch == '"' and (i == 0 or text[i - 1] != '\\'):
            in_str = not in_str
            result.append(ch)
        elif in_str:
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
    return ''.join(result)


def parse_json_safe(text, retries=2, prompt=None):
    text = sanitize_json(text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        repaired = text.rstrip()
        open_b = repaired.count('{') - repaired.count('}')
        open_s = repaired.count('[') - repaired.count(']')
        if open_s > 0:
            repaired += ']' * open_s
        if open_b > 0:
            repaired += '}' * open_b
        try:
            return json.loads(repaired)
        except json.JSONDecodeError:
            if retries > 0 and prompt:
                print(f"  Retrying JSON parse... ({retries} left)")
                new_text = ask_gemini(prompt)
                return parse_json_safe(new_text, retries - 1, prompt)
            raise ValueError(f"Failed to parse JSON:\n{text[:300]}")


def generate_poem(category=None):
    category = category or random.choice(POEM_CATEGORIES)
    print(f"  Category: {category}")

    prompt = f"""You are a children's poet creating content for a YouTube Shorts channel for kids aged 2-6.

TASK: Write ONE original children's poem in the "{category}" category.

POEM RULES:
- 4-6 lines (SHORT — this is a YouTube Short, 20-40 seconds when spoken)
- Simple vocabulary — a 3-year-old should understand every word
- MUST rhyme (AABB or ABAB pattern)
- Fun, positive, educational
- Use repetition — kids love it ("clap clap clap", "one two three")
- Include sounds/actions when possible ("moo", "quack", "jump!")

VISUAL DESCRIPTIONS:
- For EACH line of the poem, write a visual scene description
- These will be used to generate AI images for the video
- Style: "Cute cartoon [subject], bright [color] background, children's book illustration style, adorable, happy, colorful, 2D digital art"
- Keep it child-safe and colorful

YOUTUBE SEO:
- Title: catchy, under 60 chars, include the topic, end with #Shorts
- Description: 3-4 lines, educational angle, include what kids will learn
- Tags: 15 relevant tags (plain text, no #)

Respond ONLY in this exact JSON:
{{
    "category": "{category}",
    "poem_title": "The name of the poem",
    "poem_lines": [
        "First line of the poem",
        "Second line of the poem",
        "Third line of the poem",
        "Fourth line of the poem"
    ],
    "visual_descriptions": [
        "Visual description for line 1 — cartoon style, bright colors",
        "Visual description for line 2 — cartoon style, bright colors",
        "Visual description for line 3 — cartoon style, bright colors",
        "Visual description for line 4 — cartoon style, bright colors"
    ],
    "youtube_title": "Catchy title under 60 chars #Shorts",
    "description": "Fun description for kids and parents\\n\\nWhat your child will learn:\\n- Point 1\\n- Point 2",
    "tags": ["kids poems", "nursery rhymes", "... 15 total"],
    "color_palette": "warm"
}}

ONLY JSON. No other text."""

    text = ask_gemini(prompt)
    data = parse_json_safe(text, retries=2, prompt=prompt)

    # Inject subscribe CTA + default tags
    desc = data.get("description", "")
    desc += f"\n\n🔔 Subscribe to @{CHANNEL_NAME} for daily poems and rhymes!"
    desc += "\n\n#Shorts #KidsPoems #NurseryRhymes #ChildrenSongs #LearnWithFun"
    data["description"] = desc

    tags = data.get("tags", [])
    existing = {t.lower() for t in tags}
    for dt in DEFAULT_TAGS:
        if dt.lower() not in existing:
            tags.append(dt)
            existing.add(dt.lower())
    data["tags"] = tags[:30]

    # Cache the generated poem
    os.makedirs(os.path.join(POEMS_FOLDER, "generated"), exist_ok=True)
    cache_file = os.path.join(
        POEMS_FOLDER, "generated",
        f"{category}_{int(time.time())}.json"
    )
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return data


def main():
    print("=" * 50)
    print(f"  Kids Poem Generator — {GEMINI_MODEL}")
    print("=" * 50)

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    category = random.choice(POEM_CATEGORIES)
    print(f"\n  Generating {category} poem...")
    poem = generate_poem(category)

    print(f"\n  Title: {poem['youtube_title']}")
    print(f"  Lines: {len(poem['poem_lines'])}")
    print(f"  Tags : {len(poem['tags'])}")

    print("\n  Poem:")
    for line in poem["poem_lines"]:
        print(f"    {line}")

    # Save for pipeline
    with open(os.path.join(OUTPUT_FOLDER, "poem_data.json"), "w", encoding="utf-8") as f:
        json.dump(poem, f, indent=2, ensure_ascii=False)

    print(f"\n  Saved: assets/output/poem_data.json")
    print("=" * 50)


if __name__ == "__main__":
    main()
