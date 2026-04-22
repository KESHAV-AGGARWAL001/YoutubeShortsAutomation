# Kids Poems YouTube Channel — Automated Video Pipeline

A fully automated pipeline that generates original children's poems with AI illustrations, warm voiceover, background music, and colorful subtitles — then uploads directly to YouTube as Shorts.

---

## What This Pipeline Does

One command. Three videos. Full automation.

1. **Gemini generates an original poem** — rhyming, age-appropriate (2-6 years), with per-verse visual descriptions
2. **Veo 3.1 generates animated clips** — one cartoon animation per verse (falls back to static images if needed)
3. **Edge TTS creates voiceover** — warm, slow, child-friendly voice with pauses between lines
4. **FFmpeg concatenates clips** — smooth crossfade transitions between animated scenes
5. **FFmpeg burns colorful subtitles** — large yellow text at bottom, one line at a time
6. **FFmpeg mixes background music** — picks from YouTube Audio Library tracks by mood
7. **YouTube API uploads** — with `Made for Kids = True` (critical for kids algorithm)

---

## Project Structure

```
kids_poems/
├── main.py                  # Run this — generates + uploads 3 videos/day
├── config.py                # All settings (voice, video, YouTube, categories)
├── poem_generator.py        # Gemini AI poem + SEO generation
├── image_generator.py       # Gemini AI illustration per verse (fallback)
├── video_clip_generator.py  # Veo 3.1 animated clips per verse (primary)
├── clip_concatenator.py     # Normalize + concatenate Veo clips
├── tts_generator.py         # Edge TTS voiceover (free, no API key)
├── slideshow_builder.py     # Ken Burns slideshow from images (fallback)
├── subtitle_builder.py      # Colorful SRT subtitles
├── video_compositor.py      # Final assembly (video + voice + music + subs)
├── youtube_uploader.py      # YouTube upload (Made for Kids = true)
├── client_secrets_kp.json   # YouTube OAuth credentials (you provide this)
├── token_kp.json            # Auto-generated after first login
│
├── music/                   # Background music (YouTube Audio Library tracks)
│   ├── upbeat/              # Counting, animal, action poems
│   ├── calm/                # Bedtime, lullaby poems
│   ├── playful/             # Alphabet, colors, nursery rhymes
│   └── magical/             # Space, fairy tale, seasonal poems
│
├── assets/
│   ├── images/              # Fallback images (if AI generation fails)
│   └── output/              # Generated videos + intermediates
│
├── poems/
│   ├── public_domain/       # Classic nursery rhymes (text files)
│   └── generated/           # AI-generated poem cache
│
├── fonts/                   # Kid-friendly fonts (optional)
└── archive/                 # Completed videos backup
```

---

## Setup

### 1. Background Music (Required)

Download 8-10 tracks per mood from [YouTube Audio Library](https://studio.youtube.com/channel/UC/music):

- `music/upbeat/` — energetic, fun (for counting, animals, action poems)
- `music/calm/` — gentle, soft (for bedtime, lullabies)
- `music/playful/` — cheerful, bouncy (for alphabet, colors, nursery rhymes)
- `music/magical/` — dreamy, whimsical (for space, fairy tales, seasonal)

Supported formats: `.mp3`, `.wav`, `.m4a`, `.aac`, `.ogg`

### 2. YouTube OAuth Credentials (Required for Upload)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (e.g., "Kids Poems Channel")
3. Enable **YouTube Data API v3**
4. Create **OAuth 2.0 Client ID** (Desktop App)
5. Download JSON → rename to `client_secrets_kp.json`
6. Place in `kids_poems/` folder

First run opens a browser for authentication. Token saved as `token_kp.json`.

### 3. Gemini API Key

Ensure `GEMINI_API_KEY` is set in the root `.env` file. This is shared with the main NextLevelMind pipeline.

### 4. Fallback Images (Optional)

Place colorful kids' illustrations in `assets/images/` as fallback if AI image generation fails. Not required but recommended.

---

## How to Run

### Daily — 3 Videos

```bash
cd kids_poems
python main.py
```

### Generate Only (No Upload)

```bash
python main.py --no-upload
```

### Test Individual Steps

```bash
python poem_generator.py      # Test poem generation
python image_generator.py     # Test image generation (needs poem_data.json)
python tts_generator.py       # Test voiceover
python youtube_uploader.py    # Test YouTube authentication
```

---

## Configuration

All settings are in `config.py` and overridable via `.env`.

### Voice Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `KP_TTS_VOICE` | `en-US-AnaNeural` | Warm young female voice |
| `KP_TTS_RATE` | `-15%` | Slower for kids |
| `KP_TTS_PITCH` | `+3Hz` | Slightly higher pitch |

**Alternative voices:**
- `en-US-AnaNeural` — warm young female (default, recommended)
- `en-GB-MaisieNeural` — British children's voice
- `en-US-GuyNeural` — friendly male narrator

### Video Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `KP_IMAGES_PER_VIDEO` | `6` | Images per slideshow |
| `KP_MUSIC_VOLUME` | `0.20` | Background music volume |
| `KP_GEMINI_MODEL` | `gemini-2.5-flash` | AI model for poems |

### Veo 3.1 Animated Video (Google AI Pro)

When enabled (default), the pipeline generates animated cartoon clips per verse using Google's Veo 3.1 video generation API instead of static images with Ken Burns zoom.

| Setting | Default | Description |
|---------|---------|-------------|
| `KP_VEO_ENABLED` | `true` | Enable Veo animated clips (set `false` for static images) |
| `KP_VEO_MODEL` | `veo-3.1-generate-preview` | Veo model for clip generation |
| `KP_VEO_USE_LITE` | `false` | Fall back to Veo Lite if primary fails (half cost) |
| `KP_VEO_TIMEOUT` | `300` | Max seconds to wait for clip generation |
| `KP_VEO_ENHANCE_PROMPT` | `true` | Let Veo auto-enhance prompts |
| `KP_VEO_MAX_WORKERS` | `4` | Parallel clip generation threads |

**How it works:**
1. Voiceover is generated first (to get per-line timing data)
2. Each verse gets an animated clip matching its spoken duration (4s, 6s, or 8s)
3. Clips are generated in parallel for speed
4. Clips are upscaled from 720p to 1080x1920 and concatenated with crossfade transitions
5. If a clip fails, that verse falls back to a static image with Ken Burns effect

**Cost:** ~$0.05/sec with Veo 3.1 Lite. Roughly $2-4/day for 3 videos.

**To disable Veo** (use static images only): set `KP_VEO_ENABLED=false` in `.env`.

### Poem Categories

The pipeline rotates through these categories automatically:

| Category | Music Mood | Examples |
|----------|-----------|---------|
| `nursery_rhyme` | playful | Twinkle Twinkle, Humpty Dumpty |
| `animal` | upbeat | Five Little Ducks, Old MacDonald |
| `counting` | upbeat | 1-2-3 Count With Me |
| `bedtime` | calm | Goodnight Moon, Sleepy Stars |
| `alphabet` | playful | A is for Apple |
| `colors` | playful | Red Red Red, Rainbow Day |
| `action` | upbeat | Clap Your Hands, Jump Jump |
| `seasonal` | magical | Snowflake Song, Pumpkin Patch |

---

## Made for Kids — Important Rules

Videos are uploaded with `selfDeclaredMadeForKids: True`. This means:

- No personalized ads (lower CPM but still pays)
- Comments automatically disabled
- No subscriber notifications
- Algorithm-driven discovery ONLY

**The algorithm is everything.** High completion rate + rewatches = push. That's why poems are short (20-40s), visuals are colorful, and voice is slow.

---

## How It's Different from NextLevelMind

| Feature | NextLevelMind | Kids Poems |
|---------|-------------|------------|
| Content source | Books (PDF) | AI-generated poems |
| Visuals | Stock footage loop | Veo 3.1 animated clips per verse |
| Voice | Fast, direct | Slow, warm, child-friendly |
| Subtitles | Phrase-by-phrase | Line-by-line, large colorful text |
| Made for Kids | No | Yes |
| Music source | `music/` folder | `music/` folder (organized by mood) |
| Subscribe CTA | Overlay + description | Description only (no overlays for kids) |
| Target duration | 10-15 seconds | 20-40 seconds |

---

## Dependencies

Uses libraries already installed in the parent project:

| Package | Purpose | Cost |
|---------|---------|------|
| `google-genai` | Poem + image + Veo video generation | Free (Gemini API) / ~$2-4/day (Veo) |
| `edge-tts` | Voiceover | Free |
| `google-api-python-client` | YouTube upload | Free |
| `python-dotenv` | Environment variables | Free |
| `ffmpeg` (system) | Video/audio processing | Free |

No additional pip installs required. Veo 3.1 uses the same `google-genai` SDK.
