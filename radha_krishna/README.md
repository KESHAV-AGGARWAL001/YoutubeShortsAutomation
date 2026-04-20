# Radha Krishna YouTube Channel — Automated Video Pipeline

A fully automated pipeline that takes your written script, creates a beautiful slideshow video with devotional voiceover and background music, and uploads it directly to your Radha Krishna YouTube channel.

---

## What This Pipeline Does

You write a script about Bhagavad Gita / Radha Krishna teachings in a simple text file. The pipeline then:

1. **Reads your script** from `content/today_script.txt`
2. **Picks random images** (8-12) from your Radha Krishna image collection
3. **Builds a cinematic slideshow** with Ken Burns zoom effect and smooth crossfade transitions
4. **Generates a voiceover** using a sweet, calm Hindi female voice (Edge TTS — completely free)
5. **Mixes everything together** — slideshow + voiceover + optional background bhajan music
6. **Uploads to YouTube** with your title, description, and tags

One command. One minute of your time. Full video on YouTube.

---

## Project Structure

```
radha_krishna/
├── main.py                  # Run this to execute the full pipeline
├── config.py                # All settings (paths, voice, video params)
├── image_picker.py          # Randomly selects images for each video
├── slideshow_builder.py     # Creates slideshow with Ken Burns + crossfade
├── tts_generator.py         # Generates voiceover using Edge TTS
├── video_compositor.py      # Merges video + audio + background music
├── youtube_uploader.py      # Uploads to YouTube via API
├── .env                     # Your channel-specific settings
├── client_secrets_rk.json   # YouTube OAuth credentials (you provide this)
├── token_rk.json            # Auto-generated after first YouTube login
│
├── assets/
│   ├── images/              # Your Radha Krishna image collection
│   ├── music/               # Background bhajan / instrumental tracks
│   └── output/              # Generated videos (slideshow, voiceover, final)
│
└── content/
    └── today_script.txt     # Your daily script goes here
```

---

## What You Need to Provide

### 1. Radha Krishna Images (Required)

Place at least **10-15 high-quality images** in `assets/images/`.

- Supported formats: `.jpg`, `.jpeg`, `.png`, `.webp`
- Recommended resolution: **1080x1920** (portrait/vertical) or higher
- The pipeline will randomly pick 8-12 images per video
- More images = more variety across videos
- Good sources: beautiful Radha Krishna paintings, temple photos, spiritual artwork

### 2. Background Music (Optional but Recommended)

Place bhajan or instrumental tracks in `assets/music/`.

- Supported formats: `.mp3`, `.wav`, `.m4a`, `.aac`
- The pipeline randomly picks one track per video
- Music plays at 15% volume behind the voiceover (configurable)
- Good choices: flute instrumentals, soft bhajans, Krishna flute music
- If no music files are present, the video will have voiceover only

### 3. YouTube OAuth Credentials (Required for Upload)

You need a `client_secrets_rk.json` file from Google Cloud Console:

**Step-by-step setup:**

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (e.g., "Radha Krishna Channel")
3. Go to **APIs & Services > Library**
4. Search for **YouTube Data API v3** and click **Enable**
5. Go to **APIs & Services > Credentials**
6. Click **Create Credentials > OAuth 2.0 Client ID**
7. Application type: **Desktop App**
8. Name it: "Radha Krishna Uploader"
9. Click **Create** and then **Download JSON**
10. Rename the downloaded file to `client_secrets_rk.json`
11. Place it in the `radha_krishna/` folder

**First-time authentication:**
- When you run `python main.py` for the first time, a browser window will open
- Sign in with the Google account that owns your Radha Krishna YouTube channel
- Grant the requested permissions (upload videos)
- The token will be saved as `token_rk.json` — you won't need to sign in again
- This token is completely separate from your existing channel's credentials

### 4. Your Daily Script (Required)

Write your content in `content/today_script.txt` before each run.

**Script format:**

```
Line 1: Video title
Line 2: Video description  
Line 3 onwards: The actual script (this is what the voice will speak)
Lines starting with # at the end: Tags for YouTube (optional)
```

**Example:**

```
कर्म का सच — श्री कृष्ण का संदेश
भगवद्गीता का सबसे शक्तिशाली उपदेश — कर्म करो, फल की चिंता मत करो।
श्री कृष्ण ने अर्जुन से कहा — हे अर्जुन, तुम्हें केवल कर्म करने
का अधिकार है, फल पर नहीं।

यही गीता का सबसे बड़ा सत्य है।

जय श्री कृष्ण। राधे राधे।
#RadhaKrishna
#BhagavadGita
#KarmYog
```

If you don't add tags at the end, default devotional tags are used automatically:
`Radha Krishna, राधा कृष्ण, Bhagavad Gita, भगवद्गीता, Krishna, Spirituality, Hindi, Devotional, Geeta Saar, गीता सार`

---

## How to Run

### Daily Workflow

```bash
# 1. Write your script
#    Open content/today_script.txt and write today's teaching

# 2. Run the pipeline
cd radha_krishna
python main.py
```

That's it. The pipeline will show progress for each step:

```
=======================================================
  Radha Krishna YouTube Pipeline
=======================================================

[Step 1/6] Reading content...
  Title: कर्म का सच — श्री कृष्ण का संदेश
  Script: 450 chars, 82 words
  Tags: 8 tags
  Done ✓

[Step 2/6] Picking images...
  Selected 10 images for slideshow
  Done ✓

[Step 3/6] Generating voiceover...
  Voice: hi-IN-SwaraNeural | Rate: -5% | Pitch: +2Hz
  Text length: 450 characters
  Voiceover saved: 285KB
  Duration: 42.3s
  Done ✓

[Step 4/6] Building slideshow...
  Building slideshow: 10 images, 5.2s each, 42.3s total
  Running ffmpeg slideshow build...
  Slideshow created: 42.3s, 8.2MB
  Done ✓

[Step 5/6] Compositing final video...
  Voiceover: 42.3s | Slideshow: 42.3s
  Background music: krishna_flute.mp3 (volume: 15%)
  Compositing final video...
  Final video: 42.3s, 12.5MB
  Done ✓

[Step 6/6] Uploading to YouTube...
  File: final_video.mp4 (12.5MB)
  Uploading... 100%
  Upload complete in 18s
  Video ID: abc123xyz
  URL: https://youtube.com/watch?v=abc123xyz
  Done ✓

=======================================================
  Pipeline complete in 95s
  Video: https://youtube.com/watch?v=abc123xyz
=======================================================
```

### Running Individual Steps

Each module can be tested independently:

```bash
# Test image picker
python image_picker.py

# Test TTS voice
python tts_generator.py

# Test YouTube auth (opens browser, saves token)
python youtube_uploader.py
```

---

## Configuration

All settings are in `.env` (this folder) and `config.py`.

### Voice Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `RK_TTS_VOICE` | `hi-IN-SwaraNeural` | Edge TTS voice name |
| `RK_TTS_RATE` | `-5%` | Speech speed (negative = slower) |
| `RK_TTS_PITCH` | `+2Hz` | Voice pitch (positive = higher) |

**Available Hindi female voices:**
- `hi-IN-SwaraNeural` — Sweet, calm (default, recommended for devotional)
- `hi-IN-MadhurNeural` — Mature, warm

**Available English-Indian female voices:**
- `en-IN-NeerjaNeural` — Indian English female
- `en-US-AriaNeural` — American English female

To change the voice, edit `.env`:
```
RK_TTS_VOICE=hi-IN-MadhurNeural
```

### Video Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `RK_IMAGES_PER_VIDEO` | `10` | Number of images per video |
| `RK_IMAGE_DURATION` | `3` | Seconds per image (before adjustment) |
| `RK_MUSIC_VOLUME` | `0.15` | Background music volume (0.0 to 1.0) |

**Note:** The pipeline automatically adjusts image duration to match your voiceover length. If your script is long, each image shows longer. If short, images cycle faster.

### Video Dimensions

The video is created in **portrait mode (1080x1920)** — optimized for YouTube Shorts and mobile viewing. This is set in `config.py`:

```python
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
VIDEO_FPS = 30
```

---

## How It Works — Technical Details

### Ken Burns Effect

Each image gets a random zoom direction (in or out) creating a cinematic "breathing" motion. The zoom is subtle (4% over the image duration) so it looks elegant, not distracting.

### Crossfade Transitions

Images transition using ffmpeg's `xfade` filter with a 1-second fade between each image. This creates smooth, professional-looking transitions instead of hard cuts.

### Voiceover-to-Video Sync

The pipeline generates the voiceover first, measures its exact duration, then builds the slideshow to match:
- If the voiceover is 45 seconds, the slideshow will be exactly 45 seconds
- If you have 10 images, each will show for ~5.4 seconds (45s ÷ 10, adjusted for crossfade overlap)
- The video is never too short or too long for the audio

### Background Music Mixing

If music files exist in `assets/music/`:
- One track is randomly selected
- It loops to fill the entire video duration
- Volume is set to 15% (voiceover stays clear at 100%)
- Mixed using ffmpeg's `amix` filter

### YouTube Upload

- Uses a **separate OAuth token** (`token_rk.json`) that does not interfere with any other channel
- Uploads as **public** with category "People & Blogs"
- Default language set to **Hindi**
- Tags are sanitized for YouTube API compatibility (no #, no special chars, 500 char limit)
- Upload uses **resumable upload** with 5MB chunks (shows progress %)

---

## Troubleshooting

### "No images found"
Put at least 3-4 images in `assets/images/`. Supported: `.jpg`, `.jpeg`, `.png`, `.webp`.

### "Content file not found"
Create `content/today_script.txt` with at least 3 lines (title, description, script).

### "OAuth client secrets not found"
Download `client_secrets_rk.json` from Google Cloud Console (see setup instructions above).

### "FFmpeg error"
Make sure `ffmpeg` and `ffprobe` are installed and accessible from command line:
```bash
ffmpeg -version
ffprobe -version
```

### "Token refresh failed"
Delete `token_rk.json` and run again — it will re-authenticate via browser.

### Voice sounds robotic or wrong language
Check `.env` — make sure `RK_TTS_VOICE` is set to a Hindi voice like `hi-IN-SwaraNeural`. If your script is in English, use `en-IN-NeerjaNeural`.

### Video is too short / too long
The video automatically matches voiceover duration. Write a longer script for a longer video. For YouTube Shorts (under 60s), keep your script under ~150 words in Hindi.

---

## Dependencies

This module uses libraries already installed in the parent project:

| Package | Purpose | API Key Needed? |
|---------|---------|-----------------|
| `edge-tts` | Text-to-speech voiceover | No (free) |
| `google-auth` | YouTube OAuth2 | No |
| `google-auth-oauthlib` | YouTube OAuth2 flow | No |
| `google-api-python-client` | YouTube Data API v3 | OAuth only |
| `python-dotenv` | Environment variables | No |
| `ffmpeg` (system) | Video/audio processing | No |

No additional pip installs required if the parent project's dependencies are already installed.

---

## Content Ideas for Daily Scripts

Here are topic ideas for your Bhagavad Gita / Radha Krishna channel:

1. **Gita Saar (गीता सार)** — Key teachings from each chapter
2. **Krishna's Life Stories** — Childhood leelas, Govardhan, Ras Leela
3. **Karma Yoga** — Action without attachment
4. **Bhakti Yoga** — Path of devotion
5. **Daily Motivation** — Gita verses applied to modern life
6. **Radha Krishna Love** — Divine love teachings
7. **Dharma vs Adharma** — Right vs wrong from Gita's perspective
8. **Mind Control** — Gita's teachings on controlling the mind
9. **Detachment (Vairagya)** — Living without attachment
10. **Purpose of Life** — What Gita says about why we are here

---

## Important Notes

- This pipeline is **completely independent** from the existing YouTube Shorts automation
- No files outside `radha_krishna/` are modified
- The YouTube token (`token_rk.json`) is separate — your existing channel is safe
- Edge TTS is **free with no API key** — no usage limits, no billing
- Videos are saved in `assets/output/` — you can review before the upload starts
- To skip YouTube upload and just generate the video, comment out Step 6 in `main.py`
