# NextLevelMind — Pipeline Commands Reference

> **Quick answer:** To run everything daily, open a terminal in `C:\YoutubeShortsAutomation\` and run:
> ```
> python main.py          ← 2 YouTube Shorts per day
> python long_form_main.py  ← 1 long-form video per day
> ```
> That's it. Everything else is automatic.

---

## Table of Contents

1. [First-Time Setup](#1-first-time-setup)
2. [Daily Routine — What to Run](#2-daily-routine)
3. [Shorts Pipeline — Full Auto](#3-shorts-pipeline)
4. [Long-Form Pipeline — Full Auto](#4-long-form-pipeline)
5. [Run Individual Steps Manually](#5-run-individual-steps-manually)
6. [Community Post Email](#6-community-post-email)
7. [Folder Structure](#7-folder-structure)
8. [Output Files Explained](#8-output-files-explained)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. First-Time Setup

Run once, never again.

### Step 1 — Open terminal in project folder

```
cd C:\YoutubeShortsAutomation
```

> Or right-click the folder in Windows Explorer → "Open in Terminal"

### Step 2 — Install Python dependencies

```
pip install -r requirements.txt
```

Installs: `google-genai`, `Pillow`, `python-dotenv`, `edge-tts`, `PyPDF2`, `google-auth`, `google-api-python-client`, `pytrends`

### Step 3 — Create your `.env` file

Create a file named `.env` in `C:\YoutubeShortsAutomation\` with these values:

```
GEMINI_API_KEY=your_gemini_api_key_here

INSTAGRAM_TOKEN=your_instagram_long_lived_token
INSTAGRAM_ID=your_instagram_business_account_id

COMMUNITY_POST_EMAIL=your.gmail@gmail.com
COMMUNITY_POST_APP_PASSWORD=xxxx xxxx xxxx xxxx
```

**Where to get each key:**

| Key | Where to get it |
|-----|----------------|
| `GEMINI_API_KEY` | aistudio.google.com → Get API key |
| `INSTAGRAM_TOKEN` | Follow `instagram_setup_guide.md` |
| `INSTAGRAM_ID` | Follow `instagram_setup_guide.md` |
| `COMMUNITY_POST_EMAIL` | Your Gmail address |
| `COMMUNITY_POST_APP_PASSWORD` | myaccount.google.com → Security → App passwords → Generate |

### Step 4 — Place required files

```
C:\YoutubeShortsAutomation\
├── books\          ← Put your PDF books here (e.g. "Atomic Habits.pdf")
├── stock\          ← Put stock videos here (.mp4, .mov) for Short backgrounds
├── music\          ← Put background music here (.mp3, .wav, .aac)
├── credentials.json  ← YouTube API credentials (from Google Cloud Console)
```

**Get `credentials.json`:** Follow `youtube_setup_guide.md` → Steps 3-6

### Step 5 — First YouTube login (one-time only)

```
python scripts/07_upload.py
```

A browser will open asking you to log in to YouTube. Do it once — the token is saved to `output/token.json` and reused automatically forever.

---

## 2. Daily Routine

Run these every day. Both can run on the same day.

| What | Command | Time to run | Videos produced |
|------|---------|-------------|-----------------|
| Shorts (2 videos) | `python main.py` | ~8-12 minutes | 2 × 45-55 sec Shorts |
| Long-form (1 video) | `python long_form_main.py` | ~20-30 minutes | 1 × 7-8 min video |
| Community post only | `python scripts/community_post.py` | ~2 minutes | Email sent to Gmail |

**Recommended order each day:**
```
python long_form_main.py     ← Run first (uploads at 6 AM EST)
python main.py               ← Run after (uploads at 9 AM + 4 PM EST)
```

> Both can be run back-to-back. The long-form pipeline uses a separate book progress
> tracker (`books/long_progress.json`) so it never conflicts with Shorts.

---

## 3. Shorts Pipeline — Full Auto

**Command:**
```
python main.py
```

**What it does automatically:**

| Step | Script | What happens |
|------|--------|-------------|
| 1 | `02_write_script.py` | Picks next book page → writes 3-section script via Gemini → generates SEO title/tags/description |
| 2 | `03_voiceover.py` | Converts each section to MP3 voice via Edge TTS |
| 3 | `04_get_footage.py` | Selects random stock video from `stock/` folder |
| 4 | `05_make_video.py` | Assembles 1080×1920 vertical video with subtitles + background music |
| 5 | `07_upload.py` | Uploads to YouTube as Scheduled Short (9 AM EST + 4 PM EST) |
| 6 | `community_post.py` | Generates quote card image + caption → emails to your Gmail |

**After it finishes:**
- Video 1 goes live on YouTube at **9:00 AM EST**
- Video 2 goes live on YouTube at **4:00 PM EST**
- Community post email arrives in your Gmail — post it to YouTube Studio manually

**Output saved to archive:**
```
archive\video_YYYYMMDD_HHMMSS.mp4
archive\community_post_YYYYMMDD_HHMMSS.jpg
archive\community_post_YYYYMMDD_HHMMSS.txt
```

---

## 4. Long-Form Pipeline — Full Auto

**Command:**
```
python long_form_main.py
```

**What it does automatically:**

| Step | Script | What happens |
|------|--------|-------------|
| 1 | `long_02_write_script.py` | Reads 8-10 pages → writes 7-8 min structured script with chapters via Gemini |
| 2 | `03_voiceover.py` | Converts all sections (8-10) to MP3 voice |
| 3 | `04_get_footage.py` | Prepares black background for 16:9 video |
| 4 | `long_05_make_video.py` | Assembles 1920×1080 horizontal video with centered subtitles + music |
| 5 | `long_06_thumbnail.py` | Generates AI thumbnail via Gemini |
| 6 | `long_07_upload.py` | Uploads to YouTube as Scheduled video (6:00 AM EST) |
| 7 | `community_post.py` | Generates quote card + caption → emails to your Gmail |

**After it finishes:**
- Long-form video goes live on YouTube at **6:00 AM EST**
- Community post email arrives in your Gmail

---

## 5. Run Individual Steps Manually

Use these when a single step fails and you want to retry without re-running everything.

> **Important:** Always run from `C:\YoutubeShortsAutomation\` directory, not from inside `scripts\`

### Shorts steps

```bash
# Step 1 — Write script (reads book, generates SEO data)
python scripts/02_write_script.py

# Step 2 — Generate voiceover MP3s
python scripts/03_voiceover.py

# Step 3 — Select stock video footage
python scripts/04_get_footage.py

# Step 4 — Assemble final video (subtitles + music)
python scripts/05_make_video.py

# Step 5 — Generate AI thumbnail
python scripts/06_thumbnail.py

# Step 6 — Upload to YouTube
python scripts/07_upload.py

# Step 7 — Generate + email community post
python scripts/community_post.py
```

### Long-form steps

```bash
# Step 1 — Write long-form script (8-10 pages, structured chapters)
python scripts/long_02_write_script.py

# Step 2 — Generate voiceover (same script as Shorts)
python scripts/03_voiceover.py

# Step 3 — Footage setup (same script as Shorts)
python scripts/04_get_footage.py

# Step 4 — Assemble 16:9 horizontal video
python scripts/long_05_make_video.py

# Step 5 — Generate AI thumbnail
python scripts/long_06_thumbnail.py

# Step 6 — Upload to YouTube
python scripts/long_07_upload.py

# Step 7 — Generate + email community post
python scripts/community_post.py
```

### Utilities

```bash
# Send community post email only (image + caption already generated)
python scripts/community_post.py

# Check analytics performance data
# (auto-updated each run — view analytics_performance.json)
```

---

## 6. Community Post Email

After every pipeline run, you'll get an email like this:

**Subject:** `📢 Community Post Ready — [Video Title]`

**Email contains:**
- Caption text (copy-paste ready)
- Quote card image (attached as `community_post.jpg`)
- Step-by-step posting instructions inside the email

**To post it on YouTube (< 60 seconds):**
1. Open the email
2. Go to [studio.youtube.com](https://studio.youtube.com)
3. Click **CREATE** (top right) → **Community post**
4. Paste the caption from the email
5. Click the image icon → upload the attached `community_post.jpg`
6. Click **POST**

> Community Posts tab requires **500+ subscribers** to appear.

**Email not arriving? Check:**
```
# Verify .env has both keys
COMMUNITY_POST_EMAIL=your.gmail@gmail.com
COMMUNITY_POST_APP_PASSWORD=xxxx xxxx xxxx xxxx   ← Must be App Password, not Gmail password
```

**Create App Password:**
myaccount.google.com → Security → 2-Step Verification → App passwords → Generate

---

## 7. Folder Structure

```
C:\YoutubeShortsAutomation\
│
├── main.py                  ← Run this for Shorts (2 videos/day)
├── long_form_main.py        ← Run this for long-form (1 video/day)
│
├── scripts\
│   ├── 02_write_script.py       Shorts: script generation
│   ├── 03_voiceover.py          Voiceover (used by both pipelines)
│   ├── 04_get_footage.py        Footage selection (used by both)
│   ├── 05_make_video.py         Shorts: video assembly
│   ├── 06_thumbnail.py          Shorts: AI thumbnail
│   ├── 07_upload.py             Shorts: YouTube upload
│   ├── long_02_write_script.py  Long-form: script generation
│   ├── long_05_make_video.py    Long-form: video assembly
│   ├── long_06_thumbnail.py     Long-form: AI thumbnail
│   ├── long_07_upload.py        Long-form: YouTube upload
│   └── community_post.py        Community post + email (both pipelines)
│
├── books\                   ← Your PDF books go here
│   ├── progress.json            Tracks Shorts reading position per book
│   └── long_progress.json       Tracks long-form reading position per book
│
├── stock\                   ← Stock background videos (.mp4, .mov, .avi)
├── music\                   ← Background music tracks (.mp3, .wav, .aac, .m4a)
│
├── output\                  ← Working folder (auto-cleared after each run)
│   ├── seo_data.json            Title, description, tags for current video
│   ├── sections\                Script text files (one per section)
│   ├── voiceovers\              MP3 files (one per section)
│   ├── final_video.mp4          Assembled video ready for upload
│   ├── thumbnail.jpg            AI-generated thumbnail
│   ├── community_post.jpg       Quote card image for community post
│   └── community_post_text.txt  Caption text for community post
│
├── archive\                 ← Permanent backup after each run
│   ├── video_TIMESTAMP.mp4
│   ├── long_video_TIMESTAMP.mp4
│   ├── community_post_TIMESTAMP.jpg
│   └── community_post_TIMESTAMP.txt
│
├── credentials.json         ← YouTube API credentials (from Google Cloud)
├── .env                     ← API keys (GEMINI, Instagram, Gmail)
└── requirements.txt         ← Python dependencies
```

---

## 8. Output Files Explained

After each pipeline run, these files are in `output\` (and backed up to `archive\`):

| File | What it is | Used for |
|------|-----------|----------|
| `seo_data.json` | Title, description, tags, publish time | Passed to upload script |
| `sections\01_hook.txt` etc. | Script text per section | Voiceover + subtitles |
| `voiceovers\01_hook.mp3` etc. | Voice audio per section | Video assembly |
| `final_video.mp4` | Final assembled video | YouTube upload |
| `thumbnail.jpg` | AI-generated 1280×720 thumbnail | YouTube upload |
| `subtitles.srt` | Subtitle timing file | Burned into video |
| `community_post.jpg` | Quote card image | Community Post upload |
| `community_post_text.txt` | Post caption | Community Post text |
| `token.json` | YouTube auth token | Preserved across runs — DO NOT delete |

---

## 9. Troubleshooting

### "output/seo_data.json not found"
The script step didn't run or failed. Run step 1 first:
```
python scripts/02_write_script.py
```

### Upload fails / YouTube API error
```
python scripts/07_upload.py
```
If it opens a browser → log in again. Token may have expired.

### Video subtitles show wrong content
This was a known stale-file bug — already fixed. If it happens again:
```
# Manually clear old files and re-run
rmdir /s /q output\voiceovers
rmdir /s /q output\sections
python scripts/02_write_script.py
python scripts/03_voiceover.py
```

### FFmpeg error during video assembly
Verify FFmpeg is installed:
```
ffmpeg -version
```
If not installed: [ffmpeg.org/download.html](https://ffmpeg.org/download.html) → download → add to PATH

### "No books found in books/ folder"
Add at least one PDF book to the `books\` folder.

### Community post email not sending
1. Check `.env` has both `COMMUNITY_POST_EMAIL` and `COMMUNITY_POST_APP_PASSWORD`
2. Make sure it's an **App Password** (16 chars), not your Gmail login password
3. Make sure 2-Step Verification is enabled on your Google account

### Gemini thumbnail generation fails
The pipeline automatically falls back to a PIL-generated dark gradient thumbnail. Check your `GEMINI_API_KEY` in `.env` if you want the AI version.

### "No stock videos in stock/ folder"
Add at least one `.mp4` video to the `stock\` folder. Any free stock footage works (Pexels, Pixabay, etc.)

### "No music tracks in music/ folder"
Add at least one `.mp3` file to the `music\` folder. The pipeline picks one randomly each run.

---

## Quick Reference Card

```
════════════════════════════════════════════════
  DAILY COMMANDS — Run from C:\YoutubeShortsAutomation\
════════════════════════════════════════════════

  Full Shorts pipeline (2 videos):
    python main.py

  Full Long-form pipeline (1 video):
    python long_form_main.py

  Retry failed upload (Shorts):
    python scripts/07_upload.py

  Retry failed upload (Long-form):
    python scripts/long_07_upload.py

  Generate community post only:
    python scripts/community_post.py

  First-time setup:
    pip install -r requirements.txt

════════════════════════════════════════════════
  UPLOAD SCHEDULE (auto-set by pipeline)
════════════════════════════════════════════════

  Long-form   →  6:00 AM EST  (11:00 UTC)
  Short #1    →  9:00 AM EST  (14:00 UTC)
  Short #2    →  4:00 PM EST  (21:00 UTC)

════════════════════════════════════════════════
```
