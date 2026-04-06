"""
generate_carousel.py — Instagram Carousel Generator

Generates carousel content using Gemini AI and renders each slide
as a 1080x1080 PNG using Pillow.

Usage:
  python generate_carousel.py                                        # random type + category
  python generate_carousel.py --type quotes --category mental_strength
  python generate_carousel.py --type tips --category success_mindset
  python generate_carousel.py --type story --category overcoming_failure
  python generate_carousel.py --list-types                           # show all types
"""

import os
import sys
import json
import random
import argparse
import textwrap
from datetime import datetime
from dotenv import load_dotenv
from google import genai

# Load .env from parent directory
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# API key is read automatically from GEMINI_API_KEY environment variable
client = genai.Client()
MODEL  = "gemini-2.5-flash"

CAROUSELS_DIR = os.path.join(os.path.dirname(__file__), "carousels")
REGISTRY_PATH = os.path.join(CAROUSELS_DIR, "carousel_registry.json")

# ── Try to import Pillow ────────────────────────────────────────
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("  ❌ Pillow is not installed. Run: pip install Pillow")
    sys.exit(1)

# ── Categories ──────────────────────────────────────────────────
CATEGORIES = {
    "discipline_habits": {
        "name":        "Discipline & Habits",
        "description": "daily routines, morning habits, consistency, self-discipline, willpower",
        "title_style": "habit or routine angle — practical and direct",
        "avoid":       "avoid generic 5 morning habits titles",
    },
    "mental_strength": {
        "name":        "Mental Strength",
        "description": "overcoming fear, anxiety, self-doubt, building resilience, mental toughness",
        "title_style": "emotional and deep — speaks to inner struggle",
        "avoid":       "avoid surface-level positivity",
    },
    "success_mindset": {
        "name":        "Success Mindset",
        "description": "billionaire habits, wealth psychology, career growth, thinking like winners",
        "title_style": "aspirational with a contrarian twist",
        "avoid":       "avoid get rich quick or basic tips",
    },
    "life_philosophy": {
        "name":        "Life Philosophy",
        "description": "stoicism, finding purpose, meaning, living intentionally, deep life questions",
        "title_style": "philosophical and thought-provoking",
        "avoid":       "avoid religious or political angles",
    },
    "overcoming_failure": {
        "name":        "Overcoming Failure",
        "description": "bounce back from failure, rejection, starting over, resilience stories",
        "title_style": "story-driven, emotional journey",
        "avoid":       "avoid toxic positivity",
    },
    "focus_productivity": {
        "name":        "Focus & Productivity",
        "description": "deep work, eliminating distraction, getting more done, flow state",
        "title_style": "specific and practical with urgency",
        "avoid":       "avoid generic productivity lists",
    },
}

# ── Color Palettes ──────────────────────────────────────────────
PALETTES = {
    "dark_gold": {
        "bg_top":    "#0D0D0D",
        "bg_bottom": "#1A1200",
        "accent":    "#F5C518",
        "text_main": "#FFFFFF",
        "text_sub":  "#AAAAAA",
        "tag":       "#F5C518",
    },
    "dark_blue": {
        "bg_top":    "#050A1A",
        "bg_bottom": "#0A1628",
        "accent":    "#4A90E2",
        "text_main": "#FFFFFF",
        "text_sub":  "#8899AA",
        "tag":       "#4A90E2",
    },
    "dark_red": {
        "bg_top":    "#0D0000",
        "bg_bottom": "#1A0505",
        "accent":    "#E25555",
        "text_main": "#FFFFFF",
        "text_sub":  "#AAAAAA",
        "tag":       "#E25555",
    },
    "dark_green": {
        "bg_top":    "#010D05",
        "bg_bottom": "#021A0A",
        "accent":    "#2ECC71",
        "text_main": "#FFFFFF",
        "text_sub":  "#99AABB",
        "tag":       "#2ECC71",
    },
    "dark_purple": {
        "bg_top":    "#080010",
        "bg_bottom": "#10001F",
        "accent":    "#9B59B6",
        "text_main": "#FFFFFF",
        "text_sub":  "#AAAAAA",
        "tag":       "#9B59B6",
    },
}

CATEGORY_PALETTES = {
    "discipline_habits":  "dark_gold",
    "mental_strength":    "dark_blue",
    "success_mindset":    "dark_gold",
    "life_philosophy":    "dark_purple",
    "overcoming_failure": "dark_red",
    "focus_productivity": "dark_green",
}

CAROUSEL_TYPES = ["quotes", "tips", "story"]

# ── Font Loading ────────────────────────────────────────────────

FONT_SEARCH_BOLD = [
    os.path.join(os.path.dirname(__file__), "assets", "fonts", "bold.ttf"),
    os.path.join(os.path.dirname(__file__), "assets", "fonts", "Montserrat-Bold.ttf"),
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/calibrib.ttf",
    "C:/Windows/Fonts/verdanab.ttf",
]
FONT_SEARCH_REGULAR = [
    os.path.join(os.path.dirname(__file__), "assets", "fonts", "regular.ttf"),
    os.path.join(os.path.dirname(__file__), "assets", "fonts", "Montserrat-Regular.ttf"),
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/calibri.ttf",
    "C:/Windows/Fonts/verdana.ttf",
]
FONT_SEARCH_LIGHT = [
    os.path.join(os.path.dirname(__file__), "assets", "fonts", "light.ttf"),
    os.path.join(os.path.dirname(__file__), "assets", "fonts", "Montserrat-Light.ttf"),
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/calibri.ttf",
]


def find_font(search_list):
    """Find the first available font file from search list."""
    for fp in search_list:
        if os.path.exists(fp):
            return fp
    return None


def load_font(search_list, size):
    """Load a TrueType font or fall back to default."""
    path = find_font(search_list)
    if path:
        return ImageFont.truetype(path, size)
    return ImageFont.load_default()


FONT_BOLD_PATH    = find_font(FONT_SEARCH_BOLD)
FONT_REGULAR_PATH = find_font(FONT_SEARCH_REGULAR)
FONT_LIGHT_PATH   = find_font(FONT_SEARCH_LIGHT)


# ── Utility ─────────────────────────────────────────────────────

def hex_to_rgb(hex_color):
    """Convert #RRGGBB to (R, G, B) tuple."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


# ── AI Generation ──────────────────────────────────────────────

def ask_gemini(prompt, max_tokens=4096):
    """Send prompt to Gemini and return cleaned text."""
    response = client.models.generate_content(model=MODEL, contents=prompt)
    text = response.text.strip()
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


def generate_quotes_carousel(category_key, cat):
    """Generate a quotes carousel using Gemini."""
    palette = CATEGORY_PALETTES.get(category_key, "dark_gold")
    prompt = f"""You are a viral Instagram carousel content creator for @nextlevelmind_km.
Create a quotes carousel for the category: {cat['name']}
Description: {cat['description']}
Style: {cat['title_style']}
Avoid: {cat['avoid']}

RULES:
- Generate between 5 and 9 slides total (you decide based on quality)
- Slide 1 is always the COVER — it has a hook title and a teaser subtitle
- Middle slides are individual quotes — each quote should be punchy, under 20 words
- Each quote needs a short attribution or context line (e.g. "— on building discipline")
- Last slide is always the CTA slide
- Quotes must feel ORIGINAL — not cliched or overused
- Vary the emotional tone: some intense, some reflective, some surprising

OUTPUT (strict JSON only, no markdown, no extra text):
{{
  "type": "quotes",
  "category": "{category_key}",
  "palette": "{palette}",
  "total_slides": 7,
  "caption": "Instagram caption for the post (150-200 chars, punchy)",
  "hashtags": "#nextlevelmind #mentalstrength #motivation #mindset #quotes",
  "slides": [
    {{
      "slide_number": 1,
      "slide_type": "cover",
      "top_tag": "{cat['name'].upper()}",
      "main_text": "7 Quotes That Will Change How You Handle Pain",
      "sub_text": "Swipe to rewire your mindset >>",
      "bg_style": "gradient"
    }},
    {{
      "slide_number": 2,
      "slide_type": "quote",
      "top_tag": "{cat['name'].upper()}",
      "main_text": "You don't fear failure. You fear what people will think of your failure.",
      "sub_text": "-- on overcoming judgment",
      "bg_style": "gradient"
    }},
    {{
      "slide_number": 7,
      "slide_type": "cta",
      "top_tag": "NEXTLEVELMIND",
      "main_text": "Save this for the day you feel like giving up.",
      "sub_text": "Follow @nextlevelmind_km for more",
      "bg_style": "gradient"
    }}
  ]
}}

Generate all slides. Only JSON output, no other text."""
    return prompt


def generate_tips_carousel(category_key, cat):
    """Generate a tips carousel using Gemini."""
    palette = CATEGORY_PALETTES.get(category_key, "dark_gold")
    prompt = f"""You are a viral Instagram carousel content creator for @nextlevelmind_km.
Create a tips/habits carousel for the category: {cat['name']}
Description: {cat['description']}
Style: {cat['title_style']}
Avoid: {cat['avoid']}

RULES:
- Generate between 5 and 10 slides (cover + tips + CTA)
- Slide 1: Cover with hook title (e.g. "7 Habits of Mentally Strong People")
- Middle slides: One tip per slide — tip number as top_tag, bold headline, 1-line explanation
- Last slide: CTA
- Tips must be SPECIFIC and ACTIONABLE — not generic
- Number each tip on the slide (e.g. "01", "02")

OUTPUT (strict JSON only, no markdown, no extra text):
{{
  "type": "tips",
  "category": "{category_key}",
  "palette": "{palette}",
  "total_slides": 8,
  "caption": "Instagram caption (150-200 chars)",
  "hashtags": "#nextlevelmind #{category_key.replace('_', '')} #motivation #mindset #selfimprovement",
  "slides": [
    {{
      "slide_number": 1,
      "slide_type": "cover",
      "top_tag": "{cat['name'].upper()}",
      "main_text": "7 Habits of People With Unbreakable Discipline",
      "sub_text": "Number 4 will make you uncomfortable >>",
      "bg_style": "gradient"
    }},
    {{
      "slide_number": 2,
      "slide_type": "tip",
      "top_tag": "01",
      "main_text": "They schedule rest like a meeting",
      "sub_text": "Recovery isn't laziness. It's maintenance.",
      "bg_style": "gradient"
    }},
    {{
      "slide_number": 8,
      "slide_type": "cta",
      "top_tag": "NEXTLEVELMIND",
      "main_text": "Which habit will you start tomorrow?",
      "sub_text": "Comment below. Follow for daily mindset content",
      "bg_style": "gradient"
    }}
  ]
}}

Generate all slides. Only JSON output, no other text."""
    return prompt


def generate_story_carousel(category_key, cat):
    """Generate a story carousel using Gemini."""
    palette = CATEGORY_PALETTES.get(category_key, "dark_red")
    prompt = f"""You are a viral Instagram carousel content creator for @nextlevelmind_km.
Create a story-based carousel for the category: {cat['name']}
Description: {cat['description']}
Style: {cat['title_style']}
Avoid: {cat['avoid']}

RULES:
- Generate between 6 and 10 slides
- Slide 1: Hook — a shocking opening statement or question
- Middle slides: Tell the story progressively, each slide = one story beat
- Keep each slide's text SHORT — max 3 lines, punchy sentences
- Create emotional tension — make the reader NEED to swipe
- Last slide: Resolution + CTA
- Write in second person ("you") or cinematic third person

OUTPUT (strict JSON only, no markdown, no extra text):
{{
  "type": "story",
  "category": "{category_key}",
  "palette": "{palette}",
  "total_slides": 8,
  "caption": "Instagram caption (150-200 chars)",
  "hashtags": "#nextlevelmind #{category_key.replace('_', '')} #motivation #storytime #mindset",
  "slides": [
    {{
      "slide_number": 1,
      "slide_type": "cover",
      "top_tag": "TRUE STORY",
      "main_text": "He was fired at 34 with no savings and a family to feed.",
      "sub_text": "What he did next changed everything. Swipe >>",
      "bg_style": "gradient"
    }},
    {{
      "slide_number": 2,
      "slide_type": "story",
      "top_tag": "THE MOMENT",
      "main_text": "He sat in his car for 2 hours. Didn't go inside. Didn't tell his wife.",
      "sub_text": null,
      "bg_style": "gradient"
    }},
    {{
      "slide_number": 8,
      "slide_type": "cta",
      "top_tag": "NEXTLEVELMIND",
      "main_text": "Your setback is not your story. It's your setup.",
      "sub_text": "Follow @nextlevelmind_km. Save this post.",
      "bg_style": "gradient"
    }}
  ]
}}

Generate all slides. Only JSON output, no other text."""
    return prompt


def generate_carousel_content(carousel_type, category_key):
    """Generate carousel content using Gemini AI."""
    cat = CATEGORIES[category_key]

    prompt_funcs = {
        "quotes": generate_quotes_carousel,
        "tips":   generate_tips_carousel,
        "story":  generate_story_carousel,
    }

    prompt = prompt_funcs[carousel_type](category_key, cat)

    print(f"  Generating {carousel_type} carousel...")
    print(f"  Category: {cat['name']}")
    print(f"  Model: {MODEL}")

    text   = ask_gemini(prompt, max_tokens=4096)
    result = parse_json_safe(text, retries=2, prompt=prompt)

    # Validate structure
    if "slides" not in result or not isinstance(result["slides"], list):
        raise ValueError("AI response missing 'slides' array")
    if len(result["slides"]) < 3:
        raise ValueError(f"Only {len(result['slides'])} slides generated, need at least 3")

    # Ensure total_slides matches
    result["total_slides"] = len(result["slides"])

    return result


# ── Pillow Slide Renderer ───────────────────────────────────────

def draw_gradient(draw, width, height, top_color, bottom_color):
    """Draw a vertical gradient from top_color to bottom_color."""
    top_rgb    = hex_to_rgb(top_color)
    bottom_rgb = hex_to_rgb(bottom_color)
    for y in range(height):
        ratio = y / height
        r = int(top_rgb[0] + (bottom_rgb[0] - top_rgb[0]) * ratio)
        g = int(top_rgb[1] + (bottom_rgb[1] - top_rgb[1]) * ratio)
        b = int(top_rgb[2] + (bottom_rgb[2] - top_rgb[2]) * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))


def draw_progress_dots(draw, slide_number, total_slides, center_x, y, accent_rgb):
    """Draw progress indicator dots at the bottom."""
    dot_radius  = 8
    dot_gap     = 28
    total_width = total_slides * dot_gap
    start_x     = center_x - total_width // 2

    for i in range(total_slides):
        cx = start_x + i * dot_gap + dot_radius
        cy = y
        if i == slide_number - 1:
            # Active dot — accent color, larger
            draw.ellipse([cx - 10, cy - 10, cx + 10, cy + 10], fill=accent_rgb)
        else:
            # Inactive dot — dim grey
            draw.ellipse(
                [cx - dot_radius, cy - dot_radius, cx + dot_radius, cy + dot_radius],
                fill=(60, 60, 60),
            )


def auto_wrap_text(draw, text, font_path, max_width, font_sizes, max_lines=6):
    """
    Try font sizes from largest to smallest.
    Returns (font, wrapped_lines) that fit within max_width and max_lines.
    """
    for size in font_sizes:
        if font_path:
            font = ImageFont.truetype(font_path, size)
        else:
            font = ImageFont.load_default()

        # Estimate chars per line
        avg_char_w = size * 0.52
        chars_per_line = max(8, int(max_width / avg_char_w))
        wrapped = textwrap.fill(text, width=chars_per_line)
        lines   = wrapped.split("\n")

        # Verify each line actually fits
        all_fit = True
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            line_w = bbox[2] - bbox[0]
            if line_w > max_width:
                all_fit = False
                break

        if len(lines) <= max_lines and all_fit:
            return font, lines

    # Fallback: smallest size, allow overflow
    if font_path:
        font = ImageFont.truetype(font_path, font_sizes[-1])
    else:
        font = ImageFont.load_default()
    chars_per_line = max(8, int(max_width / (font_sizes[-1] * 0.52)))
    wrapped = textwrap.fill(text, width=chars_per_line)
    return font, wrapped.split("\n")


def render_slide(slide_data, slide_number, total_slides, palette_name, output_path):
    """Render a single carousel slide as a 1080x1080 PNG."""
    W, H = 1080, 1080
    palette = PALETTES[palette_name]

    img  = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)

    # 1. Gradient background
    draw_gradient(draw, W, H, palette["bg_top"], palette["bg_bottom"])

    accent_rgb   = hex_to_rgb(palette["accent"])
    text_main_rgb = hex_to_rgb(palette["text_main"])
    text_sub_rgb  = hex_to_rgb(palette["text_sub"])

    slide_type = slide_data.get("slide_type", "quote")
    top_tag    = slide_data.get("top_tag", "")
    main_text  = slide_data.get("main_text", "")
    sub_text   = slide_data.get("sub_text")

    # 2. Thin accent bar at top
    bar_width = min(180, len(top_tag) * 16 + 40) if top_tag else 140
    draw.rectangle([60, 105, 60 + bar_width, 108], fill=accent_rgb)

    # 3. Top tag text
    font_tag = load_font(FONT_SEARCH_BOLD, 28)
    draw.text((60, 58), top_tag, font=font_tag, fill=accent_rgb)

    # 4. Main text — auto-scaled and centered
    if slide_type == "cover":
        font_sizes = [88, 76, 66, 58, 50, 44]
    elif slide_type == "cta":
        font_sizes = [72, 62, 54, 48, 42]
    else:
        font_sizes = [80, 68, 58, 50, 44, 38]

    max_text_width = W - 160  # 80px padding each side
    font_main, lines = auto_wrap_text(draw, main_text, FONT_BOLD_PATH, max_text_width, font_sizes)

    # Get line height
    sample_bbox = draw.textbbox((0, 0), "Ay", font=font_main)
    line_height = (sample_bbox[3] - sample_bbox[1]) + 22

    total_text_h = len(lines) * line_height
    start_y = (H - total_text_h) // 2 - 40  # slightly above center

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font_main)
        tw   = bbox[2] - bbox[0]
        x    = (W - tw) // 2
        y    = start_y + i * line_height
        # Subtle shadow
        draw.text((x + 3, y + 3), line, font=font_main, fill=(0, 0, 0))
        draw.text((x, y), line, font=font_main, fill=text_main_rgb)

    # 5. Sub text
    if sub_text:
        font_sub = load_font(FONT_SEARCH_LIGHT, 34)

        # Word wrap sub text too
        sub_max_w = W - 200
        avg_sub_char_w = 34 * 0.5
        sub_chars_per_line = max(10, int(sub_max_w / avg_sub_char_w))
        sub_wrapped = textwrap.fill(sub_text, width=sub_chars_per_line)
        sub_lines = sub_wrapped.split("\n")

        sub_y = start_y + total_text_h + 30

        # Pick sub text color
        if slide_type in ("cover", "cta"):
            sub_color = accent_rgb
        else:
            sub_color = text_sub_rgb

        for j, sline in enumerate(sub_lines):
            bbox = draw.textbbox((0, 0), sline, font=font_sub)
            tw = bbox[2] - bbox[0]
            draw.text(((W - tw) // 2, sub_y + j * 44), sline, font=font_sub, fill=sub_color)

    # 6. CTA slide — accent border
    if slide_type == "cta":
        border_inset = 40
        draw.rectangle(
            [border_inset, border_inset, W - border_inset, H - border_inset],
            outline=accent_rgb + (100,) if len(accent_rgb) == 3 else accent_rgb,
            width=2,
        )

    # 7. Progress dots
    draw_progress_dots(draw, slide_number, total_slides, W // 2, H - 80, accent_rgb)

    # 8. Watermark
    font_wm = load_font(FONT_SEARCH_REGULAR, 24)
    wm_text = "@nextlevelmind_km"
    wm_bbox = draw.textbbox((0, 0), wm_text, font=font_wm)
    wm_w = wm_bbox[2] - wm_bbox[0]
    draw.text((W - wm_w - 30, H - 48), wm_text, font=font_wm, fill=(90, 90, 90))

    # 9. Save
    img.save(output_path, "PNG", quality=95)


# ── Save Carousel ───────────────────────────────────────────────

def create_carousel_id(carousel_data):
    """Generate a snake_case carousel ID."""
    title = carousel_data.get("slides", [{}])[0].get("main_text", "carousel")
    clean = title.lower().strip()
    clean = "".join(c if c.isalnum() or c == " " else "" for c in clean)
    clean = "_".join(clean.split())
    clean = clean[:50]
    ts    = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{clean}_{ts}"


def load_registry():
    """Load or create carousel registry."""
    if os.path.exists(REGISTRY_PATH):
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"pending": [], "uploaded": []}


def save_registry(registry):
    """Save carousel registry."""
    os.makedirs(CAROUSELS_DIR, exist_ok=True)
    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)


def save_carousel(carousel_data):
    """Save carousel content + rendered slides to disk."""
    carousel_id = create_carousel_id(carousel_data)
    carousel_dir = os.path.join(CAROUSELS_DIR, carousel_id)
    os.makedirs(carousel_dir, exist_ok=True)

    total_slides = carousel_data["total_slides"]
    palette_name = carousel_data.get("palette", "dark_gold")
    carousel_type = carousel_data.get("type", "quotes")
    category     = carousel_data.get("category", "unknown")

    # Extract title from cover slide
    title = "Untitled Carousel"
    for s in carousel_data["slides"]:
        if s.get("slide_type") == "cover":
            title = s.get("main_text", title)
            break

    # Save slides_data.json
    slides_path = os.path.join(carousel_dir, "slides_data.json")
    with open(slides_path, "w", encoding="utf-8") as f:
        json.dump(carousel_data, f, indent=2, ensure_ascii=False)

    # Render each slide
    print(f"\n  Rendering {total_slides} slides...")
    for slide in carousel_data["slides"]:
        sn = slide["slide_number"]
        output_path = os.path.join(carousel_dir, f"slide_{sn}.png")
        render_slide(slide, sn, total_slides, palette_name, output_path)
        print(f"    ✅ slide_{sn}.png")

    # Save carousel_meta.json
    meta = {
        "carousel_id":     carousel_id,
        "title":           title,
        "type":            carousel_type,
        "category":        category,
        "palette":         palette_name,
        "total_slides":    total_slides,
        "created_at":      datetime.now().isoformat(timespec="seconds"),
        "status":          "pending",
        "slides_rendered": True,
    }
    meta_path = os.path.join(carousel_dir, "carousel_meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    # Update registry
    registry = load_registry()
    registry["pending"].append({
        "carousel_id":  carousel_id,
        "title":        title,
        "type":         carousel_type,
        "category":     category,
        "total_slides": total_slides,
        "created_at":   meta["created_at"],
    })
    save_registry(registry)

    return carousel_id, meta


# ── CLI ─────────────────────────────────────────────────────────

def list_types():
    """Print available carousel types."""
    print("\n  Carousel Types:")
    print(f"  {'─' * 50}")
    print(f"  quotes  — Powerful standalone quotes (saves & shares)")
    print(f"  tips    — Actionable tips/habits (saves & follows)")
    print(f"  story   — Visual story across slides (comments & shares)")
    print()
    print("  Categories:")
    print(f"  {'─' * 50}")
    for key, cat in CATEGORIES.items():
        print(f"  {key:<25} {cat['name']}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Generate Instagram carousel slides using AI"
    )
    parser.add_argument("--type",            type=str, default=None,
                        choices=CAROUSEL_TYPES, help="Carousel type")
    parser.add_argument("--category",        type=str, default=None,
                        help="Category key")
    parser.add_argument("--list-types",      action="store_true",
                        help="Show all types and categories")
    args = parser.parse_args()

    print("\n" + "=" * 55)
    print("  🎠 Carousel Generator — NextLevelMind")
    print(f"  Model: {MODEL}")
    print("=" * 55)

    if args.list_types:
        list_types()
        return

    # Check font availability
    if not FONT_BOLD_PATH:
        print("\n  ⚠️  No bold font found! Using default font.")
        print("     For better results, download Montserrat from:")
        print("     https://fonts.google.com/specimen/Montserrat")
        print("     Save .ttf files to: carousel/assets/fonts/")

    # Pick type
    carousel_type = args.type or random.choice(CAROUSEL_TYPES)

    # Pick category
    if args.category:
        if args.category not in CATEGORIES:
            print(f"\n  ❌ Unknown category: {args.category}")
            list_types()
            sys.exit(1)
        category_key = args.category
    else:
        category_key = random.choice(list(CATEGORIES.keys()))

    cat = CATEGORIES[category_key]
    palette = CATEGORY_PALETTES.get(category_key, "dark_gold")

    print(f"\n  Type:     {carousel_type}")
    print(f"  Category: {cat['name']}")
    print(f"  Palette:  {palette}")

    # Generate
    print(f"\n  {'─' * 50}")
    try:
        carousel_data = generate_carousel_content(carousel_type, category_key)
    except Exception as e:
        print(f"\n  ❌ Generation failed: {e}")
        sys.exit(1)

    total = carousel_data["total_slides"]
    print(f"\n  ✅ Generated {total} slides")

    for slide in carousel_data["slides"]:
        sn   = slide["slide_number"]
        stype = slide.get("slide_type", "?")
        main  = slide.get("main_text", "")[:60]
        print(f"    Slide {sn} ({stype}): {main}...")

    # Save + render
    print(f"\n  {'─' * 50}")
    carousel_id, meta = save_carousel(carousel_data)

    print(f"\n{'=' * 55}")
    print(f"  ✅ Carousel created: {carousel_id}")
    print(f"  📂 Files: carousel/carousels/{carousel_id}/")
    print(f"  🖼  {total} slides rendered as PNG")
    print(f"\n  Next steps:")
    print(f"  1. Preview slides in the folder")
    print(f"  2. Upload: python upload_carousel.py --id {carousel_id}")
    print(f"  3. Dashboard: python carousel_dashboard.py")
    print(f"{'=' * 55}\n")


if __name__ == "__main__":
    main()
