# NextLevelMind — Pipeline Commands Reference

> **Quick answer:** Open a terminal in `C:\YoutubeShortsAutomation\` and run:
> ```
> start.bat                  ← WEB DASHBOARD: visual UI to create, edit, preview & upload
> python batch_main.py       ← WEEKLY: 14 Shorts + 7 long-form in one run (recommended)
> python main.py             ← DAILY:  2 YouTube Shorts per day
> python long_form_main.py   ← DAILY:  1 long-form video per day
> ```
> That's it. Everything else is automatic.

---

## Table of Contents

1. [First-Time Setup](#1-first-time-setup)
2. [Web Dashboard (NEW)](#2-web-dashboard)
3. [Daily Routine — What to Run](#3-daily-routine)
4. [Shorts Pipeline — Full Auto](#4-shorts-pipeline)
5. [Long-Form Pipeline — Full Auto](#5-long-form-pipeline)
6. [Run Individual Steps Manually](#6-run-individual-steps-manually)
7. [Community Post Email](#7-community-post-email)
8. [Folder Structure](#8-folder-structure)
9. [Output Files Explained](#9-output-files-explained)
10. [Troubleshooting](#10-troubleshooting)
11. [Weekly Batch Production](#11-weekly-batch-production)
12. [Multi-Language Shorts](#12-multi-language-shorts)
13. [Competitor Analysis](#13-competitor-analysis)
14. [Avatar Overlay](#14-avatar-overlay)
15. [Known Limitations](#15-known-limitations)
16. [Complete Script Inventory](#16-complete-script-inventory)

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
GEMINI_API_KEY=your_gemini_api_key_for_text
GEMINI_IMAGE_API_KEY=your_gemini_api_key_for_images

SCRIPT_VERSION=v2                              # "v1" (original) or "v2" (retention-optimized + HuggingFace)
AI_PROVIDER=gemini                             # "gemini" (default) or "huggingface"
HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxx           # HuggingFace access token (only if AI_PROVIDER=huggingface)
HF_MODEL=google/gemma-3-27b-it                 # HuggingFace model to use

INSTAGRAM_TOKEN=your_instagram_long_lived_token
INSTAGRAM_ID=your_instagram_business_account_id

COMMUNITY_POST_EMAIL=your.gmail@gmail.com
COMMUNITY_POST_APP_PASSWORD=xxxx xxxx xxxx xxxx
```

**Where to get each key:**

| Key | Where to get it | Used for |
|-----|----------------|----------|
| `GEMINI_API_KEY` | aistudio.google.com → Get API key | Script writing, SEO, captions |
| `GEMINI_IMAGE_API_KEY` | aistudio.google.com → Get API key (separate account/project) | Thumbnail + quote card image generation |
| `SCRIPT_VERSION` | Set to `v2` to use retention-optimized prompts | Script generation (v1 or v2) |
| `AI_PROVIDER` | Set to `huggingface` to use Gemma instead of Gemini | Script generation AI model |
| `HF_TOKEN` | huggingface.co → Settings → Access Tokens → New token | HuggingFace Inference API auth |
| `HF_MODEL` | Any chat model on HuggingFace (e.g. `google/gemma-3-27b-it`) | HuggingFace model selection |
| `INSTAGRAM_TOKEN` | Follow `instagram_setup_guide.md` | Instagram uploads |
| `INSTAGRAM_ID` | Follow `instagram_setup_guide.md` | Instagram uploads |
| `COMMUNITY_POST_EMAIL` | Your Gmail address | Community post emails |
| `COMMUNITY_POST_APP_PASSWORD` | myaccount.google.com → Security → App passwords → Generate | Community post emails |

> If `GEMINI_IMAGE_API_KEY` is not set, image generation automatically falls back to `GEMINI_API_KEY`.
> If `AI_PROVIDER=huggingface` fails, the script automatically falls back to Gemini.

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

## 2. Web Dashboard

A visual web UI for creating, editing, previewing, and uploading YouTube Shorts — without touching the command line.

### First-Time Setup

```bash
# 1. Install backend dependencies (one time)
pip install fastapi uvicorn python-multipart

# 2. Install frontend dependencies (one time)
cd frontend
npm install
cd ..
```

### Starting the Dashboard

```bash
# Option A — Double-click (Windows)
start.bat

# Option B — Manual (two terminals)
# Terminal 1:
python -m server.run

# Terminal 2:
cd frontend && npm run dev
```

Open **http://localhost:5173** in your browser.

### What You Can Do

| Feature | How |
|---------|-----|
| **Paste custom content** | Switch to "Custom Text" tab, paste your content |
| **Custom AI prompt** | Write your own prompt for Gemini in the prompt box |
| **Edit AI script** | Modify hook, body, CTA in the Script tab, click Save |
| **Edit SEO data** | Switch to SEO tab — edit title, description, tags |
| **Preview video** | After assembling, switch to Preview tab to watch |
| **Run individual steps** | Click buttons: Generate Voiceover → Assemble Video → Thumbnail |
| **Run full pipeline** | Click "Run All" — all steps run automatically with live progress |
| **Upload to YouTube** | Set schedule time and click Upload |

### Architecture

- **Backend**: FastAPI on port 8000 — wraps existing pipeline scripts
- **Frontend**: React + Vite on port 5173 — proxies `/api` to backend
- **No database** — uses same `output/` files as CLI pipeline
- **CLI still works** — `python main.py` and `python batch_main.py` are unchanged

---

## 3. Daily Routine

You have two modes: **daily** (run every day) or **weekly batch** (run once per week).

### Option A — Daily mode (run every day)

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

### Option B — Weekly batch (run once per week)

| What | Command | Time to run | Videos produced |
|------|---------|-------------|-----------------|
| Entire week | `python batch_main.py` | ~2-3 hours | 14 Shorts + 7 long-form |
| Multi-language | `python scripts/multi_language.py` | ~30-45 minutes | 4 language versions per Short |
| Competitor analysis | `python scripts/competitor_analysis.py` | ~3 minutes | Trend insights saved |

**Recommended weekly workflow:**
```
python scripts/competitor_analysis.py   ← Step 1: Scrape trends (run first)
python batch_main.py                    ← Step 2: Generate + upload 21 English videos
python scripts/multi_language.py        ← Step 3: Generate Hindi/Spanish/Portuguese/Arabic
```
Then upload multi-language videos to separate YouTube channels manually.

> Both modes use separate book progress trackers so Shorts and long-form never conflict.

---

## 4. Shorts Pipeline — Full Auto

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

## 5. Long-Form Pipeline — Full Auto

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

## 6. Run Individual Steps Manually

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

### Growth tools

```bash
# Competitor analysis (scrape top Shorts, analyze patterns)
python scripts/competitor_analysis.py

# Multi-language Shorts (all 4 languages)
python scripts/multi_language.py

# Multi-language (specific languages only)
python scripts/multi_language.py hi es

# Avatar overlay (after video assembly)
python scripts/avatar_overlay.py
python scripts/avatar_overlay.py --position right --size 200

# Community post email only
python scripts/community_post.py
```

---

## 7. Community Post Email

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

## 8. Folder Structure

```
C:\YoutubeShortsAutomation\
│
├── main.py                  ← Daily: 2 Shorts/day
├── long_form_main.py        ← Daily: 1 long-form/day
├── batch_main.py            ← Weekly: 14 Shorts + 7 long-form in one run
│
├── scripts\
│   ├── 02_write_script.py       Shorts: script generation (v1)
│   ├── 02_write_script_v2.py    Shorts: retention-optimized script (v2)
│   ├── 03_voiceover.py          Voiceover via Edge TTS (shared)
│   ├── 04_get_footage.py        Footage selection (shared)
│   ├── 05_make_video.py         Shorts: video assembly (9:16)
│   ├── 06_thumbnail.py          Shorts: AI thumbnail (Gemini)
│   ├── 07_upload.py             Shorts: YouTube upload (no playlist)
│   ├── 07_upload_v2.py          Shorts: YouTube upload + auto-playlist
│   ├── long_02_write_script.py  Long-form: script generation
│   ├── long_05_make_video.py    Long-form: video assembly (16:9)
│   ├── long_06_thumbnail.py     Long-form: AI thumbnail (Gemini)
│   ├── long_07_upload.py        Long-form: YouTube upload
│   ├── community_post.py        Community post + email (both pipelines)
│   ├── multi_language.py        Translate + generate multi-language Shorts
│   ├── competitor_analysis.py   Scrape top Shorts + analyze patterns
│   ├── avatar_overlay.py        Overlay character avatar on video
│   ├── analytics_tracker.py     Upload analytics logging
│   └── get_trending_tags.py     Trending tag injector
│
├── books\                   ← Your PDF books go here
│   ├── progress.json            Tracks Shorts reading position per book
│   └── long_progress.json       Tracks long-form reading position per book
│
├── stock\                   ← Stock background videos (.mp4, .mov, .avi, .mkv)
├── music\                   ← Background music tracks (.mp3, .wav, .aac, .m4a)
├── avatar\                  ← Character avatar image (avatar.png, transparent PNG)
│
├── output\                  ← Working folder (auto-cleared after each run)
│   ├── seo_data.json            Title, description, tags for current video
│   ├── sections\                Script text files (one per section)
│   ├── voiceovers\              MP3 files (one per section)
│   ├── final_video.mp4          Assembled video ready for upload
│   ├── thumbnail.jpg            AI-generated thumbnail
│   ├── community_post.jpg       Quote card image for community post
│   ├── community_post_text.txt  Caption text for community post
│   ├── competitor_insights.json Competitor analysis results
│   ├── lang_hi\                 Hindi translated video + sections
│   ├── lang_es\                 Spanish translated video + sections
│   ├── lang_pt\                 Portuguese translated video + sections
│   ├── lang_ar\                 Arabic translated video + sections
│   ├── token.json               YouTube auth (preserved across runs)
│   └── playlist_cache.json      Playlist ID cache (preserved across runs)
│
├── archive\                 ← Permanent backup after each run
│
├── credentials.json         ← YouTube API credentials (from Google Cloud)
├── .env                     ← API keys (GEMINI, Instagram, Gmail)
└── requirements.txt         ← Python dependencies
```

---

## 9. Output Files Explained

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

## 10. Troubleshooting

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

## 11. Weekly Batch Production

Generate an entire week's content (14 Shorts + 7 Long-form) in one run:

```
python batch_main.py
```

**What it does:**
- Calculates 7 days of schedules starting tomorrow
- For each day: generates 1 long-form + 2 Shorts
- Uploads all 21 videos with staggered publish times
- Auto-creates playlists per book (via `07_upload_v2.py`)
- Archives everything to `archive/`
- Sends community post emails for each video

**Schedule per day:**
| Slot | Time (EST) | Type |
|------|-----------|------|
| 1 | 6:00 AM | Long-form |
| 2 | 9:00 AM | Short #1 |
| 3 | 4:00 PM | Short #2 |

**Script version:** Set `SCRIPT_VERSION=v2` in `.env` to use retention-optimized scripts.

---

## 12. Multi-Language Shorts

Generate translated Shorts in Hindi, Spanish, Portuguese, Arabic:

```bash
# All 4 languages
python scripts/multi_language.py

# Only specific languages
python scripts/multi_language.py hi es       # Hindi + Spanish only
python scripts/multi_language.py pt ar       # Portuguese + Arabic only
```

**What it does:**
1. Reads English sections from `output/sections/`
2. Translates each section via Gemini
3. Generates voiceover in target language (Edge TTS)
4. Assembles video with stock background
5. Saves to `output/lang_hi/`, `output/lang_es/`, etc.

**Language voices:**
| Code | Language | Voice |
|------|----------|-------|
| hi | Hindi | hi-IN-MadhurNeural |
| es | Spanish | es-MX-JorgeNeural |
| pt | Portuguese | pt-BR-AntonioNeural |
| ar | Arabic | ar-SA-HamedNeural |

**Run AFTER** `02_write_script.py` (needs English sections to exist).

---

## 13. Competitor Analysis

Scrape top-performing Shorts in your niche and feed winning patterns into prompts:

```
python scripts/competitor_analysis.py
```

**What it does:**
1. Searches YouTube for top Shorts (8 niche queries)
2. Pulls stats: views, likes, titles, tags from top 50+ Shorts
3. Gemini analyzes winning title formulas, power words, trending topics
4. Saves insights to `output/competitor_insights.json`

**Run weekly BEFORE `batch_main.py`** to keep your content aligned with trends.

> **Auto-wired:** Both `02_write_script.py` and `long_02_write_script.py` automatically
> read `output/competitor_insights.json` and inject trending title patterns, power words,
> and trending topics into the Gemini prompt. Run competitor analysis weekly to keep fresh.

---

## 14. Avatar Overlay

Overlay a static character avatar on your videos for brand recognition:

```bash
# Default (bottom-left, 160px)
python scripts/avatar_overlay.py

# Custom position and size
python scripts/avatar_overlay.py --position right --size 200
```

**Setup:**
1. Create folder: `avatar/`
2. Place your character image: `avatar/avatar.png` (PNG, transparent background, 400x400px+)
3. Run the script after video assembly

**Avatar sources (free):**
- Generate with Gemini image generation
- Canva AI avatar generator
- Remove background from any photo at remove.bg

---

## Quick Reference Card

```
════════════════════════════════════════════════
  DAILY COMMANDS — Run from C:\YoutubeShortsAutomation\
════════════════════════════════════════════════

  Web Dashboard (visual UI):
    start.bat
    → Opens http://localhost:5173

  Full Shorts pipeline (2 videos):
    python main.py

  Full Long-form pipeline (1 video):
    python long_form_main.py

  Weekly batch (14 Shorts + 7 Long-form):
    python batch_main.py

  Retry failed upload (Shorts):
    python scripts/07_upload.py

  Retry failed upload (Long-form):
    python scripts/long_07_upload.py

  Generate community post only:
    python scripts/community_post.py

════════════════════════════════════════════════
  GROWTH TOOLS
════════════════════════════════════════════════

  Competitor analysis (run weekly):
    python scripts/competitor_analysis.py

  Multi-language Shorts (all 4):
    python scripts/multi_language.py

  Multi-language (specific):
    python scripts/multi_language.py hi es

  Avatar overlay:
    python scripts/avatar_overlay.py

  First-time setup:
    pip install -r requirements.txt

════════════════════════════════════════════════
  UPLOAD SCHEDULE (auto-set by pipeline)
════════════════════════════════════════════════

  Long-form   →  6:00 AM EST  (11:00 UTC)
  Short #1    →  9:00 AM EST  (14:00 UTC)
  Short #2    →  4:00 PM EST  (21:00 UTC)

════════════════════════════════════════════════
  RECOMMENDED WEEKLY WORKFLOW
════════════════════════════════════════════════

  1. python scripts/competitor_analysis.py
  2. python batch_main.py
  3. python scripts/multi_language.py
  4. Upload multi-language videos to separate channels

════════════════════════════════════════════════
```

---

## 15. Known Limitations

| Item | Status | Details |
|------|--------|---------|
| **Competitor insights → prompt** | Wired | `competitor_analysis.py` saves insights → `02_write_script.py` and `long_02_write_script.py` auto-read them and inject trending patterns into the Gemini prompt. Run `competitor_analysis.py` weekly to keep insights fresh. |
| **Multi-language upload** | Manual | Translated videos are generated to `output/lang_*/` but must be uploaded manually to separate YouTube channels per language. |
| **Voice cloning** | Not available | Coqui XTTS v2 requires GPU with 4GB+ VRAM. Current setup uses Edge TTS (free, no GPU). ElevenLabs free tier (10K chars/month) is an alternative if custom voice is needed. |
| **Avatar setup** | Manual | You must provide `avatar/avatar.png` (transparent PNG). Generate one using Gemini image generation, Canva AI, or remove.bg. |
| **Affiliate links** | Placeholder | `02_write_script.py` and `long_02_write_script.py` have placeholder Amazon URLs (`https://amzn.to/REPLACE_*`). Replace with your actual affiliate links. |
| **Community post upload** | Manual | YouTube Community Posts API is not publicly available. The pipeline generates everything + emails it to you. Manual upload in YouTube Studio takes < 60 seconds. |
| **Community post access** | 500+ subs | YouTube Community Posts tab only appears after 500 subscribers. |

---

## 16. Complete Script Inventory

### Pipeline runners (run from project root)

| Script | Purpose | Videos/run |
|--------|---------|------------|
| `main.py` | Daily Shorts pipeline | 2 Shorts |
| `long_form_main.py` | Daily long-form pipeline | 1 long-form |
| `batch_main.py` | Weekly batch production | 14 Shorts + 7 long-form |

### Core pipeline scripts (in `scripts/`)

| Script | Step | Used by |
|--------|------|---------|
| `02_write_script.py` | Script generation (v1) | Shorts |
| `02_write_script_v2.py` | Script generation (v2 retention-optimized) | Shorts (if `SCRIPT_VERSION=v2`) |
| `long_02_write_script.py` | Script generation | Long-form |
| `03_voiceover.py` | Edge TTS voiceover | Both |
| `04_get_footage.py` | Stock video selection | Both |
| `05_make_video.py` | 9:16 video assembly | Shorts |
| `long_05_make_video.py` | 16:9 video assembly | Long-form |
| `06_thumbnail.py` | AI thumbnail (Gemini) | Shorts |
| `long_06_thumbnail.py` | AI thumbnail (Gemini) | Long-form |
| `07_upload.py` | YouTube upload (no playlist) | Shorts (daily) |
| `07_upload_v2.py` | YouTube upload + auto-playlist | Shorts (batch) |
| `long_07_upload.py` | YouTube upload | Long-form |

### Growth tools (in `scripts/`)

| Script | Purpose | When to run |
|--------|---------|-------------|
| `community_post.py` | Quote card + caption + email | Auto (end of every pipeline run) |
| `competitor_analysis.py` | Scrape + analyze top Shorts | Weekly, before `batch_main.py` |
| `multi_language.py` | Translate → voiceover → video (4 languages) | After English Shorts are generated |
| `avatar_overlay.py` | Overlay character avatar on video | After video assembly, before upload |

### Web Dashboard (in `server/` and `frontend/`)

| File/Folder | Purpose |
|-------------|---------|
| `server/app.py` | FastAPI app — CORS, static mounts, router registration |
| `server/run.py` | Entry point: `python -m server.run` starts on port 8000 |
| `server/models/schemas.py` | Pydantic models for all API request/response types |
| `server/routers/` | API endpoints: books, script, voiceover, video, thumbnail, upload, pipeline, settings |
| `server/services/state.py` | Pipeline state management with SSE event streaming |
| `server/services/pipeline_runner.py` | Wraps existing scripts, runs them in background threads |
| `server/services/script_service.py` | Custom content injection — bypasses book reading for pasted text |
| `frontend/` | React + TypeScript + Vite app |
| `frontend/vite.config.ts` | Proxy: `/api` → `http://127.0.0.1:8000` |
| `start.bat` | Launches both backend and frontend servers |

### Utilities (in `scripts/`)

| Script | Purpose |
|--------|---------|
| `analytics_tracker.py` | Logs upload data for performance tracking |
| `get_trending_tags.py` | Injects trending tags into uploads |

### Image generation model

All thumbnail and quote card image generation uses:
```
Model: gemini-3.1-flash-image-preview
API Key: GEMINI_IMAGE_API_KEY (falls back to GEMINI_API_KEY)
```

### Voice generation

All voiceovers use Edge TTS (free, no GPU required):

| Language | Voice ID |
|----------|----------|
| English | en-US-GuyNeural (default) |
| Hindi | hi-IN-MadhurNeural |
| Spanish | es-MX-JorgeNeural |
| Portuguese | pt-BR-AntonioNeural |
| Arabic | ar-SA-HamedNeural |
