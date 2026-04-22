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

1. Download music tracks to `kids_poems/music/{mood}/` folders
2. Set up YouTube channel + OAuth credentials (`client_secrets_kp.json`)
3. Ensure `GEMINI_API_KEY` is set in root `.env`
4. Google AI Pro subscription (for Veo 3.1 access)

---

## Shared Infrastructure with NextLevelMind

| Component | Shared? | Notes |
|-----------|---------|-------|
| Edge TTS | Yes | Different voice config (slower, higher pitch) |
| FFmpeg | Yes | Different subtitle style (larger, colorful) |
| Gemini API | Yes | Same `GEMINI_API_KEY` |
| Google AI Pro | Yes | Same subscription, shared Veo quota |
| YouTube API code | Pattern shared | Separate OAuth credentials per channel |
