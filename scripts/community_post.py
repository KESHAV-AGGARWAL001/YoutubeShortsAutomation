"""
community_post.py — YouTube Community Post Generator

Automatically generates a community post for every video (Shorts + long-form):
  1. Reads the video script sections to find the strongest insight/quote
  2. Generates a bold quote card image via Gemini AI
  3. Generates an engaging post caption via Gemini
  4. Saves output/community_post.jpg + output/community_post_text.txt
  5. Emails the image + caption to your Gmail so you can post it in <60 seconds

NOTE: YouTube Community Posts cannot be auto-uploaded via API.
      This script emails everything ready — posting takes <60 seconds:
      YouTube Studio → Create → Community post → paste text + upload image → Post

.env variables required for email:
  COMMUNITY_POST_EMAIL       = your.gmail@gmail.com
  COMMUNITY_POST_APP_PASSWORD = xxxx xxxx xxxx xxxx   (Gmail App Password)

How to create a Gmail App Password:
  1. Go to myaccount.google.com → Security → 2-Step Verification → App passwords
  2. Select app: Mail, device: Windows Computer → Generate
  3. Copy the 16-character password into .env

Requirements:
  - 500+ subscribers to access Community Posts tab
  - output/seo_data.json must exist (run after script generation step)
  - output/sections/ must exist (run after script generation step)
"""

import os
import json
import random
import time as _time
import smtplib
import ssl
from io import BytesIO
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont

load_dotenv()

# ── Gemini Setup ─────────────────────────────────────────────────────
try:
    from google import genai
    from google.genai.types import GenerateContentConfig, Modality
    _text_key  = os.getenv("GEMINI_API_KEY")
    _image_key = os.getenv("GEMINI_IMAGE_API_KEY") or _text_key
    text_client  = genai.Client(api_key=_text_key)
    image_client = genai.Client(api_key=_image_key)
    GEMINI_AVAILABLE = True
except Exception:
    GEMINI_AVAILABLE = False
    text_client  = None
    image_client = None

TEXT_MODEL  = "gemini-2.5-flash"
IMAGE_MODEL = "gemini-3.1-flash-image-preview"

POST_W, POST_H = 1280, 720   # YouTube recommends 16:9 for community post images

# ── Quote card prompt styles ──────────────────────────────────────────
QUOTE_CARD_PROMPTS = [
    # Style A — Dark minimal quote card
    """Create a YouTube community post quote card image (1280x720).
Style: Dark, clean, minimal. Solid near-black background (#0d0d0d or #111111).
Layout: Large bold quote text centered on the image.
Quote text: "{quote}"
Text color: Bright white with a subtle text shadow.
Add a thin gold or amber horizontal accent line below the quote.
Bottom right corner: small text "@NextLevelMind" in gray.
NO people, NO faces. Typography-only design. Make it look premium.""",

    # Style B — Neon accent quote card
    """Create a YouTube community post image (1280x720).
Style: Dark background with a single neon accent color (choose: electric blue, purple, or red).
Quote: "{quote}"
The quote should be large, bold, centered white text with a neon glow effect.
Add subtle neon light streaks or particles in the corners.
Bottom: "@NextLevelMind" in the accent color, small.
NO people, NO faces. Abstract, modern, high-contrast.""",

    # Style C — Spotlight/cinematic
    """Create a YouTube community post image (1280x720).
Style: Black background with a dramatic spotlight or light beam from above center.
Quote: "{quote}"
Text: Large, bold, centered. White text. Key words in gold/yellow.
Subtle fog or smoke at the bottom of the image.
Bottom right: "@NextLevelMind" watermark in white, small.
NO people, NO faces. Cinematic and dramatic.""",

    # Style D — Bold typographic
    """Create a YouTube community post image (1280x720).
Style: Bold, typographic-forward design. Very dark gray or black background.
Quote: "{quote}"
Make the text very large — it should dominate the image.
Use a mix: most words in white, 2-3 impactful words in bright red or orange.
Add a thick red accent bar on the left side or bottom of the image.
Small "@NextLevelMind" in bottom right, gray.
NO people, NO faces. Pure typography power.""",
]

# ── Caption prompt styles ─────────────────────────────────────────────
CAPTION_PROMPTS = [
    # Style A — Question hook
    """Write a short YouTube Community Post caption for this video topic:
Title: "{title}"
Key insight: "{quote}"

Format:
- Start with a thought-provoking question (1 sentence)
- 2-3 sentences expanding on the insight — conversational, real, not salesy
- One line CTA like "Full video is live on the channel ↑" (vary the wording)
- 3-4 hashtags at the end

Write it as a real person sharing a genuine thought. Max 150 words.""",

    # Style B — Bold statement hook
    """Write a short YouTube Community Post caption for this video topic:
Title: "{title}"
Key insight: "{quote}"

Format:
- Open with a bold, provocative statement (not a question)
- 2-3 sentences of real talk — no fluff, no corporate speak
- Short CTA pointing to the video (one line, casual)
- 3-4 hashtags

Tone: Direct, confident, like you're texting a friend who needs to hear this. Max 150 words.""",

    # Style C — Storytelling
    """Write a short YouTube Community Post caption for this video topic:
Title: "{title}"
Key insight: "{quote}"

Format:
- Open with a micro-story or personal moment (1-2 sentences, fictional but relatable)
- Connect it to the insight (1-2 sentences)
- CTA to watch the full video (casual, varied — not always "subscribe")
- 3-4 hashtags

Keep it human, warm, under 150 words. Avoid motivational clichés.""",
]


# ── Font paths for PIL fallback ───────────────────────────────────────
FONT_PATHS = [
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/calibrib.ttf",
    "C:/Windows/Fonts/verdanab.ttf",
    "C:/Windows/Fonts/arial.ttf",
]


def load_font(size):
    for fp in FONT_PATHS:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                continue
    return ImageFont.load_default()


def read_script_sections():
    """Read all section text files and concatenate into one block."""
    sections_dir = "output/sections"
    if not os.path.exists(sections_dir):
        return ""
    texts = []
    for fname in sorted(os.listdir(sections_dir)):
        if fname.endswith(".txt"):
            fpath = os.path.join(sections_dir, fname)
            with open(fpath, encoding="utf-8") as f:
                texts.append(f.read().strip())
    return "\n\n".join(texts)


def extract_best_quote(title, script_text):
    """Use Gemini to extract the most powerful single insight from the script."""
    if not GEMINI_AVAILABLE:
        return f"The most powerful lessons are the ones you actually apply."

    prompt = f"""From the following YouTube video script, extract the single most powerful,
quotable insight or lesson. It should be 1-2 sentences max, standalone (no context needed),
punchy and memorable — something that would stop someone while scrolling.

Video title: {title}

Script:
{script_text[:3000]}

Return ONLY the quote itself. No quotation marks, no attribution, no explanation."""

    try:
        response = text_client.models.generate_content(
            model=TEXT_MODEL,
            contents=prompt,
        )
        quote = response.text.strip().strip('"').strip("'")
        return quote
    except Exception as e:
        print(f"  Quote extraction failed: {e}")
        return "The habits you build today are the life you live tomorrow."


def generate_caption(title, quote):
    """Use Gemini to generate the community post caption."""
    if not GEMINI_AVAILABLE:
        return f"{quote}\n\nFull video is live on the channel ↑\n\n#motivation #mindset #selfimprovement #discipline"

    prompt_template = random.choice(CAPTION_PROMPTS)
    prompt = prompt_template.format(title=title, quote=quote)

    try:
        response = text_client.models.generate_content(
            model=TEXT_MODEL,
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        print(f"  Caption generation failed: {e}")
        return f"{quote}\n\nFull video is live on the channel ↑\n\n#motivation #mindset #selfimprovement"


def generate_quote_card_gemini(quote):
    """Generate quote card image using Gemini image generation."""
    prompt_template = random.choice(QUOTE_CARD_PROMPTS)
    # Truncate very long quotes for the image
    display_quote = quote if len(quote) <= 120 else quote[:117] + "..."
    prompt = prompt_template.format(quote=display_quote)

    print(f"  Generating quote card with Gemini...")

    for attempt in range(3):
        try:
            if attempt > 0:
                wait = 10 * attempt
                print(f"  Retry {attempt}/2 — waiting {wait}s...")
                _time.sleep(wait)

            response = image_client.models.generate_content(
                model=IMAGE_MODEL,
                contents=prompt,
                config=GenerateContentConfig(
                    response_modalities=[Modality.TEXT, Modality.IMAGE],
                ),
            )

            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    image_bytes = part.inline_data.data
                    img = Image.open(BytesIO(image_bytes))
                    img = img.convert("RGB")
                    img = img.resize((POST_W, POST_H), Image.LANCZOS)
                    print(f"  Quote card generated successfully!")
                    return img

            print(f"  No image in Gemini response — retrying...")

        except Exception as e:
            err = str(e).lower()
            if any(k in err for k in ["429", "overloaded", "resource", "quota", "rate", "unavailable", "503", "500"]):
                if attempt < 2:
                    continue
            print(f"  Gemini image generation failed: {e}")
            return None

    return None


def generate_quote_card_fallback(quote):
    """Fallback: PIL-generated quote card with dark background."""
    print(f"  Using fallback PIL quote card generator...")

    img  = Image.new("RGB", (POST_W, POST_H), color=(13, 13, 13))
    draw = ImageDraw.Draw(img)

    # Subtle gradient
    for y in range(POST_H):
        ratio = y / POST_H
        r = int(13 + 12 * ratio)
        g = int(13 + 7 * ratio)
        b = int(13 + 22 * ratio)
        draw.line([(0, y), (POST_W, y)], fill=(r, g, b))

    font_quote  = load_font(52)
    font_small  = load_font(28)
    font_handle = load_font(26)

    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    GOLD  = (255, 215, 0)
    GRAY  = (180, 180, 180)

    def draw_bordered(pos, text, font, fill, bw=3, anchor="mm"):
        x, y = pos
        for dx in range(-bw, bw + 1):
            for dy in range(-bw, bw + 1):
                if dx or dy:
                    draw.text((x+dx, y+dy), text, font=font, fill=BLACK, anchor=anchor)
        draw.text(pos, text, font=font, fill=fill, anchor=anchor)

    # Word-wrap the quote manually (approx 36 chars/line at 52px)
    import textwrap
    lines = textwrap.wrap(quote, width=36)
    lines = lines[:4]  # max 4 lines on image

    line_h = 65
    total_h = len(lines) * line_h
    y_start = (POST_H - total_h) // 2 - 20

    for i, line in enumerate(lines):
        y = y_start + i * line_h
        draw_bordered((POST_W // 2, y), line, font_quote, WHITE)

    # Gold accent line below quote
    bar_y = y_start + total_h + 20
    bar_w = int(POST_W * 0.4)
    bar_x = (POST_W - bar_w) // 2
    draw.rectangle([(bar_x, bar_y), (bar_x + bar_w, bar_y + 3)], fill=GOLD)

    # Watermark
    draw_bordered((POST_W - 30, POST_H - 30), "@NextLevelMind",
                  font_handle, GRAY, bw=2, anchor="rb")

    return img


def send_email(caption, image_path, title):
    """Send community post image + caption to Gmail."""
    email_addr = os.getenv("COMMUNITY_POST_EMAIL", "").strip()
    app_password = os.getenv("COMMUNITY_POST_APP_PASSWORD", "").strip()

    if not email_addr or not app_password:
        print("  EMAIL SKIPPED: Set COMMUNITY_POST_EMAIL + COMMUNITY_POST_APP_PASSWORD in .env")
        return False

    print(f"  Sending community post to {email_addr}...")

    try:
        msg = MIMEMultipart("related")
        msg["Subject"] = f"📢 Community Post Ready — {title[:60]}"
        msg["From"]    = email_addr
        msg["To"]      = email_addr

        # HTML body with inline image
        html_body = f"""
<html><body style="font-family:Arial,sans-serif;background:#111;color:#eee;padding:24px;">
  <h2 style="color:#FFD700;">📢 YouTube Community Post Ready</h2>
  <p style="color:#aaa;font-size:13px;">Video: <strong style="color:#fff;">{title}</strong></p>

  <hr style="border-color:#333;margin:16px 0;">

  <h3 style="color:#FFD700;">Post Caption — copy this:</h3>
  <div style="background:#1a1a1a;border-left:4px solid #FFD700;padding:16px;
              border-radius:6px;white-space:pre-wrap;font-size:15px;line-height:1.7;">
{caption}
  </div>

  <hr style="border-color:#333;margin:24px 0;">

  <h3 style="color:#FFD700;">Quote Card Image — attach this to your post:</h3>
  <img src="cid:community_post_img" style="width:100%;max-width:640px;
       border-radius:8px;border:1px solid #333;" alt="Community Post Image">

  <hr style="border-color:#333;margin:24px 0;">

  <h3 style="color:#aaa;font-size:13px;">How to post (60 seconds):</h3>
  <ol style="color:#aaa;font-size:13px;line-height:2;">
    <li>Open <a href="https://studio.youtube.com" style="color:#FFD700;">YouTube Studio</a></li>
    <li>Click <strong>CREATE</strong> (top right) → <strong>Community post</strong></li>
    <li>Paste the caption above</li>
    <li>Click the image icon → save the attached image → upload it</li>
    <li>Click <strong>POST</strong></li>
  </ol>
  <p style="color:#555;font-size:11px;margin-top:32px;">
    Sent by NextLevelMind automation pipeline
  </p>
</body></html>
"""
        msg.attach(MIMEText(html_body, "html"))

        # Attach image as inline
        with open(image_path, "rb") as f:
            img_data = f.read()
        img_part = MIMEImage(img_data, name="community_post.jpg")
        img_part.add_header("Content-ID", "<community_post_img>")
        img_part.add_header("Content-Disposition", "attachment", filename="community_post.jpg")
        msg.attach(img_part)

        context = ssl.create_default_context()
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls(context=context)
            server.login(email_addr, app_password)
            server.sendmail(email_addr, email_addr, msg.as_string())

        print(f"  Email sent to {email_addr} ✓")
        return True

    except smtplib.SMTPAuthenticationError:
        print("  EMAIL FAILED: Authentication error.")
        print("  → Make sure you're using a Gmail App Password, not your regular password.")
        print("  → myaccount.google.com → Security → App passwords")
        return False
    except Exception as e:
        print(f"  EMAIL FAILED: {e}")
        return False


def main():
    print("=" * 50)
    print("  Community Post Generator")
    print("  Quote Card + Caption for YouTube")
    print("=" * 50)

    if not os.path.exists("output/seo_data.json"):
        print("\n  ERROR: output/seo_data.json not found!")
        print("  Run 02_write_script.py first.")
        return

    with open("output/seo_data.json", encoding="utf-8") as f:
        seo = json.load(f)

    title = seo["youtube_title"]
    print(f"\n  Video title: {title}")

    # Step 1 — Read script sections
    print("\n[1/5] Reading script sections...")
    script_text = read_script_sections()
    if not script_text:
        print("  WARNING: No section files found. Using title only for quote extraction.")
        script_text = title

    # Step 2 — Extract best quote
    print("\n[2/5] Extracting best insight/quote...")
    quote = extract_best_quote(title, script_text)
    print(f"  Quote: \"{quote}\"")

    # Step 3 — Generate caption
    print("\n[3/5] Generating post caption...")
    caption = generate_caption(title, quote)

    # Step 4 — Generate quote card image
    print("\n[4/5] Generating quote card image...")
    img = None
    if GEMINI_AVAILABLE:
        img = generate_quote_card_gemini(quote)
    if img is None:
        img = generate_quote_card_fallback(quote)

    # Save outputs
    img.save("output/community_post.jpg", quality=95, optimize=True)

    with open("output/community_post_text.txt", "w", encoding="utf-8") as f:
        f.write(caption)

    img_size_kb = os.path.getsize("output/community_post.jpg") // 1024

    print("\n" + "=" * 50)
    print(f"  Saved: output/community_post.jpg ({img_size_kb} KB)")
    print(f"  Saved: output/community_post_text.txt")
    print("=" * 50)

    print("\n  ── POST CAPTION ─────────────────────────────")
    print(caption)
    print("  ─────────────────────────────────────────────")

    # Send email with image + caption
    print("\n[5/5] Sending email...")
    email_sent = send_email(caption, "output/community_post.jpg", title)

    print("\n" + "=" * 50)
    if email_sent:
        print("  Email sent! Check your inbox.")
        print("  → Open the email, copy the caption, attach the image, post on YouTube.")
    else:
        print("  Email not sent — post manually:")
        print("  1. YouTube Studio → CREATE → Community post")
        print("  2. Paste: output/community_post_text.txt")
        print("  3. Upload: output/community_post.jpg")
    print("  Note: Community Posts tab requires 500+ subscribers.")
    print("=" * 50)


if __name__ == "__main__":
    main()
