# LittleStarFactory — Kids Poems Channel

**Channel Name:** LittleStarFactory
**Niche:** Kids poems, nursery rhymes, funny videos with AI-animated visuals + music
**Target Audience:** Toddlers & preschoolers (ages 2-6) and their parents
**Format:** YouTube Shorts (20-40s)
**Pipeline Status:** Fully built and automated

---

## Why This Channel Works

- **Kids rewatch obsessively** — a single nursery rhyme Short can get 500K+ views from the same 10K kids watching it 50 times
- **Parents leave YouTube running** — watch hours accumulate fast
- **Evergreen content** — "Twinkle Twinkle" never stops trending
- **Veo 3.1 animated visuals** — most kids' channels use static images or cheap animations. AI-animated clips per verse set us apart
- **YPP faster** — kids' content consistently hits 3M Shorts views faster than any other niche

---

## Pipeline Architecture

```
[Gemini 2.5 Flash: Original Poem + SEO]
         ↓
[Edge TTS: Warm Child-Friendly Voiceover]
         ↓
[Veo 3.1: Animated Cartoon Clips Per Verse]  →  fallback: [Gemini Images + Ken Burns]
         ↓
[FFmpeg: Concatenate Clips + Crossfade Transitions]
         ↓
[FFmpeg: Merge Video + Voiceover + Music + Burn Subtitles]
         ↓
[YouTube API: Upload with Made for Kids = True]
```

### Pipeline Files (all in `kids_poems/`)

| File | Purpose |
|------|---------|
| `main.py` | Orchestrator — generates + uploads 3 videos/day |
| `config.py` | All settings (voice, video, Veo, YouTube, categories) |
| `poem_generator.py` | Gemini AI poem + SEO generation |
| `video_clip_generator.py` | **Veo 3.1 animated clips per verse (primary)** |
| `clip_concatenator.py` | Normalize + concatenate Veo clips with crossfade |
| `image_generator.py` | Gemini AI illustrations (fallback if Veo fails) |
| `slideshow_builder.py` | Ken Burns slideshow from images (fallback) |
| `tts_generator.py` | Edge TTS voiceover (free, en-US-AnaNeural) |
| `subtitle_builder.py` | Colorful SRT subtitles (large yellow text) |
| `video_compositor.py` | Final assembly (video + voice + music + subs) |
| `youtube_uploader.py` | YouTube upload with `selfDeclaredMadeForKids: True` |

---

## Tools & Costs

| Tool | Purpose | Cost |
|------|---------|------|
| Gemini 2.5 Flash | Poem generation + SEO | Free |
| Veo 3.1 | Animated cartoon clips per verse | ~$2-4/day (AI Pro) |
| Gemini 2.0 Flash | Fallback image generation | Free |
| Edge TTS | Warm child-friendly voiceover | Free |
| YouTube Audio Library | Background music (mood-organized) | Free |
| FFmpeg | Video/audio processing | Free |
| YouTube Data API v3 | Upload + scheduling | Free |

**Daily cost: ~$2-4/day** (Veo clips only). Set `KP_VEO_ENABLED=false` for $0/day with static images.

---

## Google AI Pro Benefits — How We Use Them

| AI Pro Feature | How We Use It |
|---|---|
| **Gemini 2.5 Flash** | Generate original poems + visual descriptions + SEO metadata |
| **Veo 3.1** | Generate animated cartoon clips per verse (primary visual pipeline) |
| **Veo 3.1 Lite** | Fallback model if Veo 3.1 fails (half cost) |
| **Google AI Studio** | Higher API limits for batch production (3 videos/day) |
| **5 TB Storage** | Archive all generated assets + videos |
| **1,000 AI Credits** | Overflow capacity for heavy generation weeks |

**Not using AI Pro for music** — YouTube Audio Library (free, copyright-safe) organized by mood folders.

---

## Content Categories

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

## Publishing Schedule

- **3 Shorts/day** — automated via `python main.py`
- **Schedule:** 9 AM EST, 4 PM EST, 8 PM EST (peak parent + kid viewing times)
- **Categories:** Randomly rotated each day

---

## Made for Kids — Rules

Videos are uploaded with `selfDeclaredMadeForKids: True`:

- No personalized ads (lower CPM but still pays)
- Comments automatically disabled
- No subscriber notifications
- Algorithm-driven discovery ONLY
- **The algorithm is everything.** High completion rate + rewatches = push

---

## Veo 3.1 Integration

When `KP_VEO_ENABLED=true` (default), the pipeline flow changes:

1. **Voiceover generated first** (need timing data for clip durations)
2. **Veo generates animated clips in parallel** (4 workers by default)
3. Each clip duration matches its verse's spoken duration (4s, 6s, or 8s)
4. Clips upscaled from 720p to 1080x1920 and concatenated with crossfade

**Fallback chain:**
1. Veo 3.1 → 2. Veo Lite (if enabled) → 3. Static image + Ken Burns → 4. Full legacy pipeline

**Prompt style:** "Create a gentle animated children's cartoon scene: {visual_description}. Style: cute 2D animation, bright vivid colors, simple shapes, child-friendly, happy mood, smooth slow gentle motion, no text or words, no scary elements, safe for toddlers."

---

## Music Setup

Download 8-10 tracks per mood from YouTube Audio Library:

```
kids_poems/music/
├── upbeat/    — energetic (counting, animals, action poems)
├── calm/      — gentle (bedtime, lullabies)
├── playful/   — cheerful (alphabet, colors, nursery rhymes)
└── magical/   — dreamy (space, fairy tales, seasonal)
```

Pipeline auto-picks a random track matching the poem's mood category.

---

## Pinterest Search Terms — Kids Animated Illustrations

Use these to find fallback images for `assets/images/`, visual inspiration, and reference styles for AI prompts.

### General Style

- Kids cartoon illustration
- Children's book illustration art
- Cute cartoon characters for kids
- Kawaii kids illustration
- Toddler friendly cartoon art
- Preschool cartoon illustration
- Bright colorful kids illustration
- 2D flat illustration for children
- Digital art for kids videos
- Cute nursery wall art cartoon

### Animals

- Cute cartoon animals for kids
- Baby animal illustration kawaii
- Cartoon duck pond kids
- Cute cartoon bunny illustration
- Friendly cartoon farm animals
- Cartoon jungle animals for toddlers
- Cartoon ocean animals kids
- Cute cartoon dinosaur kids
- Baby elephant cartoon illustration
- Cartoon cats and dogs for children

### Nursery Rhymes & Poems

- Nursery rhyme illustration art
- Twinkle twinkle little star cartoon
- Humpty Dumpty kids illustration
- Jack and Jill cartoon art
- Hey Diddle Diddle illustration
- Mother Goose cartoon art
- Kids poem visual illustration
- Storybook nursery rhyme art

### Counting & Numbers

- Cartoon numbers for kids
- Counting illustration preschool
- Number characters cartoon kids
- Kids counting game illustration
- Colorful numbers cartoon toddler
- 123 kids learning illustration

### Alphabet & Letters

- ABC cartoon illustration kids
- Alphabet characters for children
- Letter learning cartoon art
- Kids alphabet poster illustration
- Cute alphabet animal illustration
- Preschool letter cartoon art

### Colors & Shapes

- Rainbow cartoon kids illustration
- Learn colors kids cartoon
- Colorful shapes for toddlers art
- Cartoon rainbow characters kids
- Primary colors cartoon illustration
- Shapes cartoon preschool art

### Bedtime & Lullaby

- Bedtime cartoon illustration kids
- Sleepy moon stars cartoon
- Goodnight kids illustration art
- Dreamy night sky cartoon toddler
- Baby sleeping cartoon cute
- Lullaby illustration soft pastel

### Seasonal & Holiday

- Christmas cartoon kids illustration
- Halloween cute cartoon for kids
- Spring flowers cartoon children
- Winter snowflake cartoon kids
- Autumn leaves cartoon toddler
- Easter bunny kids cartoon art

### Action & Fun

- Kids dancing cartoon illustration
- Clapping hands cartoon kids
- Jumping cartoon toddler art
- Kids playing cartoon illustration
- Funny cartoon kids laughing
- Silly face cartoon for children

---

## YPP Timeline Estimate

| Metric | Target | Estimate |
|--------|--------|----------|
| Subscribers | 500 | 4-6 weeks |
| Shorts views (90 days) | 3,000,000 | 6-10 weeks |
| Videos needed | ~150-200 Shorts | 7-10 weeks at 3/day |

Kids' content typically hits YPP **2-3x faster** than adult content because of the rewatch multiplier.

---

## How to Run

```bash
cd kids_poems
python main.py              # Generate + upload 3 videos
python main.py --no-upload  # Generate only, skip upload
```

### Prerequisites

1. Set `KP_GEMINI_API_KEY` in `kids_poems/.env` (your AI Pro account's API key)
2. Download music tracks to `kids_poems/music/{mood}/` folders
3. Set up YouTube channel + OAuth credentials (`client_secrets_kp.json`)
4. Google AI Pro subscription (for Veo 3.1 access)

---

## Environment Configuration — Separate API Keys Per Channel

Each channel has its own `.env` file with isolated API keys. This prevents conflicts when different channels use different Google accounts.

```
YoutubeShortsAutomation/
├── .env                    # Root — NextLevelMind (GEMINI_API_KEY)
├── radha_krishna/.env      # Radha Krishna channel config
└── kids_poems/.env         # LittleStarFactory config (KP_GEMINI_API_KEY)
```

### Key Resolution Order

```
kids_poems/.env  →  KP_GEMINI_API_KEY  (priority 1 — AI Pro account)
       ↓ fallback
root .env        →  GEMINI_API_KEY     (priority 2 — shared key)
```

- `KP_GEMINI_API_KEY` — set this to your Google AI Pro account's API key (the account with Veo 3.1 access)
- If not set, falls back to the root `GEMINI_API_KEY` automatically
- YouTube OAuth (`client_secrets_kp.json`) is always from the channel's own Google account — completely independent from the Gemini API key

### Why Separate Keys?

| Account | Purpose | Key |
|---------|---------|-----|
| AI Pro email | Gemini API, Veo 3.1, image generation | `KP_GEMINI_API_KEY` |
| Channel email | YouTube upload, OAuth | `client_secrets_kp.json` |

These are independent auth flows — Gemini API key generates the content, YouTube OAuth uploads it. Two accounts, zero conflict.

### kids_poems/.env Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `KP_GEMINI_API_KEY` | falls back to `GEMINI_API_KEY` | Gemini API key (AI Pro account) |
| `KP_TTS_VOICE` | `en-US-AnaNeural` | Edge TTS voice |
| `KP_TTS_RATE` | `-15%` | Speech rate (slower for kids) |
| `KP_TTS_PITCH` | `+3Hz` | Pitch adjustment |
| `KP_IMAGES_PER_VIDEO` | `6` | Images per slideshow |
| `KP_MUSIC_VOLUME` | `0.20` | Background music volume |
| `KP_GEMINI_MODEL` | `gemini-2.5-flash` | AI model for poems |
| `KP_GEMINI_IMAGE_MODEL` | `gemini-2.0-flash-exp` | AI model for images |
| `KP_VEO_ENABLED` | `true` | Enable Veo animated clips |
| `KP_VEO_MODEL` | `veo-3.1-generate-preview` | Veo model |
| `KP_VEO_USE_LITE` | `false` | Use Veo Lite as fallback |
| `KP_VEO_TIMEOUT` | `300` | Veo generation timeout (seconds) |
| `KP_VEO_ENHANCE_PROMPT` | `true` | Let Veo enhance prompts |
| `KP_VEO_MAX_WORKERS` | `4` | Parallel clip generation workers |

---

## Shared Infrastructure with NextLevelMind

| Component | Shared? | Notes |
|-----------|---------|-------|
| Edge TTS | Yes | Different voice config (slower, higher pitch) |
| FFmpeg | Yes | Different subtitle style (larger, colorful) |
| Gemini API | **No** | Separate `KP_GEMINI_API_KEY` in `kids_poems/.env` |
| Google AI Pro | Yes | Same subscription, shared Veo quota |
| YouTube API code | Pattern shared | Separate OAuth credentials per channel |
