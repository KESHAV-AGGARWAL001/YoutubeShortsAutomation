"""
09_send_email.py — Send Reel Package via Gmail

Sends complete Reel package to Gmail:
  - Reel video compressed to under 20MB for Gmail attachment
  - Cover image attached
  - Full upload card in email body (HTML — readable on phone)
  - Caption, hashtags, heading, audio, alt text all copy-paste ready
"""

import os
import json
import glob
import smtplib
import datetime
import subprocess
from email.mime.multipart import MIMEMultipart
from email.mime.text      import MIMEText
from email.mime.base      import MIMEBase
from email.mime.image     import MIMEImage
from email                import encoders
from dotenv               import load_dotenv
load_dotenv()

REELS_FOLDER    = "reels"
SENDER_EMAIL    = os.getenv("EMAIL_ADDRESS")
SENDER_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")
RECEIVER_EMAIL  = os.getenv("EMAIL_ADDRESS")
MAX_MB          = 20   # compress reel to stay under Gmail 25MB limit


# ── Helpers ──────────────────────────────────────────────────

def get_latest_files(reel_num):
    def latest(pat):
        files = sorted(glob.glob(pat))
        return files[-1] if files else None
    return {
        "video": latest(f"{REELS_FOLDER}/reel_{reel_num}_*.mp4"),
        "cover": latest(f"{REELS_FOLDER}/reel_{reel_num}_cover_*.jpg"),
        "card":  latest(f"{REELS_FOLDER}/reel_{reel_num}_UPLOAD_CARD_*.txt"),
        "data":  latest(f"{REELS_FOLDER}/reel_{reel_num}_data_*.json"),
    }


def load_data(path):
    if not path or not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def read_card(path):
    if not path or not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# ── Compress video to fit Gmail 25MB limit ────────────────────

def compress_reel(input_path, max_mb=MAX_MB):
    """
    Compress reel video to fit under Gmail attachment limit.
    Uses FFmpeg to reduce bitrate while keeping good quality.
    Returns path to compressed file.
    """
    if not input_path or not os.path.exists(input_path):
        return None

    size_mb = os.path.getsize(input_path) / (1024 * 1024)

    # Already small enough — no compression needed
    if size_mb <= max_mb:
        print(f"  Video size: {size_mb:.1f} MB — no compression needed")
        return input_path

    print(f"  Video size: {size_mb:.1f} MB — compressing to under {max_mb} MB...")

    # Calculate target bitrate
    # formula: (target_size_bits) / duration_seconds = bitrate
    duration = get_duration(input_path)
    if duration <= 0:
        duration = 58

    target_size_bits = max_mb * 1024 * 1024 * 8
    target_bitrate   = int((target_size_bits / duration) * 0.9)  # 10% buffer
    video_bitrate    = int(target_bitrate * 0.85)  # 85% video, 15% audio
    audio_bitrate    = 96000  # 96kbps audio — good quality, small size

    compressed_path = input_path.replace(".mp4", "_compressed.mp4")

    result = subprocess.run([
        "ffmpeg", "-y",
        "-i", input_path,
        "-c:v", "libx264",
        "-b:v", str(video_bitrate),
        "-preset", "fast",
        "-c:a", "aac",
        "-b:a", str(audio_bitrate),
        "-movflags", "+faststart",   # optimise for streaming/mobile
        compressed_path
    ], capture_output=True, text=True)

    if os.path.exists(compressed_path):
        new_size = os.path.getsize(compressed_path) / (1024 * 1024)
        print(f"  Compressed: {size_mb:.1f} MB → {new_size:.1f} MB")
        return compressed_path

    print(f"  Compression failed — attaching original")
    return input_path


def get_duration(filepath):
    try:
        r = subprocess.run([
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            filepath
        ], capture_output=True, text=True, timeout=10)
        return float(r.stdout.strip())
    except Exception:
        return 58.0


# ── Build HTML email body ─────────────────────────────────────

def build_html(reel_num, data):
    caption   = data.get("caption",        "See attached upload card")
    hashtags  = data.get("hashtags",       "")
    audio     = data.get("audio",          "Search: cinematic motivational")
    location  = data.get("location",       "Worldwide")
    alt_text  = data.get("alt_text",       "")
    hook_text = data.get("hook_text",      "WATCH TILL THE END")
    heading   = data.get("heading",        "NEXTLEVELMIND")
    best_time = data.get("best_time",      "7:00 AM / 7:00 PM IST")
    duration  = data.get("duration",       58)
    title     = data.get("youtube_title",  "NextLevelMind")

    return f"""<!DOCTYPE html><html>
<head><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body{{font-family:Arial,sans-serif;background:#0a0a0a;color:#fff;margin:0;padding:12px}}
.w{{max-width:600px;margin:0 auto}}
.hdr{{background:linear-gradient(135deg,#1a1a2e,#7f77dd);padding:20px;border-radius:12px;text-align:center;margin-bottom:14px}}
.hdr h1{{margin:0;font-size:20px;color:#fff}}
.hdr p{{margin:4px 0 0;color:#ccc;font-size:12px}}
.box{{background:#1a1a1a;border:1px solid #2a2a2a;border-radius:10px;padding:14px;margin-bottom:10px}}
.box h2{{margin:0 0 8px;font-size:12px;color:#7f77dd;text-transform:uppercase;letter-spacing:1px}}
.copy{{background:#0d0d1a;border:1px solid #7f77dd;border-radius:8px;padding:12px;font-size:13px;white-space:pre-wrap;word-break:break-word;line-height:1.7}}
.times{{display:flex;gap:8px}}
.t{{flex:1;background:#0d0d1a;border:1px solid #333;border-radius:8px;padding:10px;text-align:center}}
.tt{{font-size:20px;font-weight:bold;color:#f5a623}}
.tl{{font-size:11px;color:#888;margin-top:3px;line-height:1.4}}
.step{{display:flex;gap:8px;padding:7px 0;border-bottom:1px solid #222;font-size:12px;color:#ccc;align-items:flex-start}}
.step:last-child{{border-bottom:none}}
.sn{{background:#7f77dd;color:#fff;width:20px;height:20px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:bold;flex-shrink:0;margin-top:1px}}
.tip{{background:#0d1a0d;border:1px solid #1D9E75;border-radius:8px;padding:10px 12px;font-size:12px;color:#9FE1CB;margin-top:8px}}
.footer{{text-align:center;padding:16px;color:#444;font-size:11px}}
</style></head>
<body><div class="w">

<div class="hdr">
  <h1>📱 Reel {reel_num} Ready — NextLevelMind</h1>
  <p>{title}</p>
  <p style="color:#f5a623;font-size:11px">Duration: {duration}s · 1080×1920 · Video attached below</p>
</div>

<div class="box">
  <h2>⏰ Post at these times</h2>
  <div class="times">
    <div class="t"><div class="tt">7:00 AM</div><div class="tl">IST — Reel 1<br>India morning</div></div>
    <div class="t"><div class="tt">7:00 PM</div><div class="tl">IST — Reel 2<br>India + US peak</div></div>
  </div>
</div>

<div class="box">
  <h2>🎬 Heading (cover text)</h2>
  <div class="copy">{heading}</div>
</div>

<div class="box">
  <h2>🪝 Hook text (first 3 seconds — add as text sticker)</h2>
  <div class="copy">{hook_text}</div>
</div>

<div class="box">
  <h2>📝 Caption — tap and hold to copy</h2>
  <div class="copy">{caption}</div>
</div>

<div class="box">
  <h2>#️⃣ Hashtags — paste after caption</h2>
  <div class="copy">{hashtags}</div>
</div>

<div class="box">
  <h2>🎵 Audio suggestion</h2>
  <div style="font-size:13px;color:#e0e0e0;line-height:1.6">{audio}</div>
  <div class="tip">Use Instagram's own trending audio for extra reach boost</div>
</div>

<div class="box">
  <h2>📍 Location tag</h2>
  <div class="copy">{location}</div>
</div>

<div class="box">
  <h2>♿ Alt text (Advanced Settings → Accessibility)</h2>
  <div class="copy">{alt_text}</div>
</div>

<div class="box">
  <h2>📱 Upload steps</h2>
  <div class="step"><div class="sn">1</div><div>Download the attached .mp4 video to your phone gallery</div></div>
  <div class="step"><div class="sn">2</div><div>Open Instagram → tap + → tap Reel</div></div>
  <div class="step"><div class="sn">3</div><div>Select the video from gallery</div></div>
  <div class="step"><div class="sn">4</div><div>Add audio — search suggestion above in Instagram music</div></div>
  <div class="step"><div class="sn">5</div><div>Add text sticker: <strong>{hook_text}</strong> — show only first 3 seconds</div></div>
  <div class="step"><div class="sn">6</div><div>Paste caption from above</div></div>
  <div class="step"><div class="sn">7</div><div>Paste hashtags after caption</div></div>
  <div class="step"><div class="sn">8</div><div>Add location: {location}</div></div>
  <div class="step"><div class="sn">9</div><div>Advanced Settings → Accessibility → paste alt text</div></div>
  <div class="step"><div class="sn">10</div><div>Share! Reply to every comment in first 30 minutes 🔥</div></div>
</div>

<div class="box">
  <h2>💡 Pro tips</h2>
  <div style="font-size:12px;color:#ccc;line-height:1.9">
    • Share Reel to your Stories immediately after posting<br>
    • Reply to EVERY comment in first 30 minutes<br>
    • Do NOT edit after posting — resets algorithm reach<br>
    • Add to a Highlight after 24 hours
  </div>
</div>

<div class="footer">
  NextLevelMind Content Bot · {datetime.datetime.now().strftime('%d %b %Y %I:%M %p')}<br>
  @nextlevelmind_km · Upload card also attached as .txt
</div>

</div></body></html>"""


# ── Send email ────────────────────────────────────────────────

def send_email(reel_num):
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("  ERROR: EMAIL_ADDRESS or EMAIL_APP_PASSWORD not in .env!")
        return False

    files = get_latest_files(reel_num)
    data  = load_data(files.get("data"))
    title = data.get("youtube_title", "NextLevelMind")

    print(f"\n  Preparing email for Reel {reel_num}...")
    print(f"  To: {RECEIVER_EMAIL}")

    msg            = MIMEMultipart("mixed")
    msg["From"]    = SENDER_EMAIL
    msg["To"]      = RECEIVER_EMAIL
    msg["Subject"] = f"📱 NextLevelMind Reel {reel_num} Ready — {title}"

    # HTML body
    msg.attach(MIMEText(build_html(reel_num, data), "html"))

    # ── Attach video (compressed if needed) ──
    video_path = files.get("video")
    if video_path and os.path.exists(video_path):
        send_path = compress_reel(video_path, MAX_MB)
        if send_path and os.path.exists(send_path):
            size_mb = os.path.getsize(send_path) / (1024 * 1024)
            print(f"  Attaching video: {size_mb:.1f} MB")
            with open(send_path, "rb") as f:
                part = MIMEBase("video", "mp4")
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename=NextLevelMind_Reel_{reel_num}.mp4"
                )
                msg.attach(part)
            # Clean up compressed file
            if send_path != video_path and os.path.exists(send_path):
                os.remove(send_path)
        else:
            print("  Video attach skipped — file not found")
    else:
        print("  Video not found — email sent without video attachment")

    # ── Attach cover image ──
    cover_path = files.get("cover")
    if cover_path and os.path.exists(cover_path):
        print(f"  Attaching cover image")
        with open(cover_path, "rb") as f:
            img = MIMEImage(f.read(), name=f"NextLevelMind_Cover_{reel_num}.jpg")
            img.add_header(
                "Content-Disposition",
                f"attachment; filename=NextLevelMind_Cover_{reel_num}.jpg"
            )
            msg.attach(img)

    # ── Attach upload card .txt ──
    card_path = files.get("card")
    if card_path and os.path.exists(card_path):
        print(f"  Attaching upload card (.txt)")
        with open(card_path, "rb") as f:
            part = MIMEBase("text", "plain")
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename=NextLevelMind_UploadCard_{reel_num}.txt"
            )
            msg.attach(part)

    # ── Send ──
    try:
        print(f"  Connecting to Gmail SMTP...")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        print(f"  Email sent to {RECEIVER_EMAIL}!")
        return True
    except smtplib.SMTPAuthenticationError:
        print("  ERROR: Gmail authentication failed!")
        print("  Check EMAIL_APP_PASSWORD in .env")
        return False
    except smtplib.SMTPException as e:
        print(f"  SMTP error: {e}")
        return False
    except Exception as e:
        print(f"  Error: {e}")
        return False


def main():
    print("=" * 50)
    print("  Email Sender — NextLevelMind Reels")
    print("=" * 50)

    reel_num = os.environ.get("VIDEO_NUMBER", "1")
    success  = send_email(reel_num)

    if success:
        print(f"\n  Check Gmail inbox — video attached!")
        print(f"  Download .mp4 → upload to Instagram")
    else:
        print(f"\n  Email failed — use files in reels/ folder")


if __name__ == "__main__":
    main()