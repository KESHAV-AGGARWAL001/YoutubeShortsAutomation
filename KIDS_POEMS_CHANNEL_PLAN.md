# Kids Poems Channel — Full Build Plan

**Created:** 2026-04-21
**Channel Name:** TBD (suggestions: TinyVerseLand, PoemPals, LittleRhymeTime)
**Niche:** Kids poems with colorful AI-generated visuals + music
**Formats:** YouTube Shorts (30-60s) + Long-form compilations (10-15 min)

---

## Why This Channel Will Work

- **Kids rewatch obsessively** — a single nursery rhyme Short can get 500K+ views from the same 10K kids watching it 50 times. Completion rate and rewatch rate go through the roof.
- **Parents leave YouTube running** — watch hours accumulate fast. Even Shorts feed into session time.
- **Evergreen content** — "Twinkle Twinkle" never stops trending. No need to chase weekly trends.
- **Low competition for AI-quality visuals** — most kids' poem channels use static images or cheap animations. AI-generated visuals will stand out.
- **YPP faster** — kids' content consistently hits 3M Shorts views faster than any other niche.

---

## Google AI Pro Benefits — Mapped to This Channel

| AI Pro Feature | Use Case | Impact |
|---|---|---|
| **Gemini 2.5 Pro** | Generate original poems + adapt public domain rhymes | Better rhyming, age-appropriate language |
| **Flow (text-to-video)** | Generate animated visual backgrounds per verse | Colorful, unique scenes for each poem |
| **Whisk** | Generate illustrations (characters, animals, scenes) | Kid-friendly art style per frame |
| **Google AI Studio** | Higher limits for all generation tasks | Handle batch production (21+ videos/week) |
| **5 TB Storage** | Store all generated assets + video archive | Never run out of space |
| **NotebookLM** | Research popular poems, analyze what works | Feed insights into content strategy |
| **Deep Research** | Find trending kids' content topics | Stay ahead of seasonal trends |
| **1,000 AI Credits** | Overflow capacity for heavy generation weeks | Safety net for batch production |
| **Google Cloud Credits** | YouTube API quota + Cloud Run automation | Hands-free publishing |

**Not using AI Pro for music** — free alternatives are better suited:
| Free Tool | Use Case | Cost |
|---|---|---|
| **YouTube Audio Library** | Pre-made royalty-free kids' tracks | Free, copyright-safe |
| **Meta MusicGen** | AI-generated custom melodies per poem | Free, open-source, runs locally |
| **Suno AI free tier** | High-quality tracks for compilations | Free (10 songs/day) |

---

## Pipeline Architecture

```
[Poem Source] → [Gemini Pro: Script] → [Flow/Whisk: Visuals] → [ProducerAI: Music]
                                                                        ↓
[Edge TTS: Narration] → [FFmpeg: Assemble] → [YouTube API: Upload]
```

### Step-by-Step Pipeline

#### Step 1: Poem Script Generation (`kids_01_write_poem.py`)
- **Input:** Poem type (nursery rhyme, animal poem, counting poem, bedtime poem, alphabet poem)
- **Model:** Gemini 2.5 Pro (AI Pro limits)
- **Output:** 
  - Poem text (4-8 lines, rhyming, age 2-6)
  - Per-line visual descriptions (for image/video generation)
  - YouTube title, description, tags
  - Color palette suggestion (warm/cool/bright)
- **Public domain poems:** Also adapt classics (Twinkle Twinkle, Humpty Dumpty, etc.) with fresh visual scripts
- **Original poems:** Generate new poems on trending kids' topics (animals, colors, seasons, space, dinosaurs)

#### Step 2: Visual Generation (`kids_02_generate_visuals.py`)
Two modes depending on API availability:

**Mode A — Flow (text-to-video):**
- Generate a 5-10 second video clip per verse
- Prompt style: "Cute cartoon style, bright colors, [scene from poem], child-friendly, no text, 4K"
- Example: "A happy yellow star twinkling in a dark blue night sky with smiling clouds, cartoon style"
- Concat all clips into one background video

**Mode B — Whisk (image generation) + Ken Burns:**
- Generate 1 illustration per verse using Whisk
- Style: colorful children's book illustration
- Apply Ken Burns effect (slow zoom/pan) via FFmpeg to make static images feel animated
- This is the reliable fallback if Flow API isn't available

**Mode C — Hybrid (recommended):**
- Use Flow for key scenes (opening, climax)
- Use Whisk for transitional frames
- Mix for variety

#### Step 3: Music / Melody (`kids_03_music.py`) — FREE, Zero Cost

Three free approaches, layered for reliability:

**Option A — YouTube Audio Library (Simplest, recommended to start)**
- YouTube Studio → Audio Library → free, royalty-free tracks
- Pre-download 30-40 kids' tracks, organized by mood into `kids_poems/music/`
  - `music/upbeat/` — counting poems, animal poems, action poems
  - `music/calm/` — bedtime poems, lullabies
  - `music/playful/` — alphabet, color, nursery rhyme
  - `music/magical/` — space, fairy tale, seasonal
- Script picks a random track from the matching mood folder
- **Pros:** Zero setup, guaranteed copyright-safe on YouTube, high quality
- **Cons:** Not unique per video (but kids don't care — they want familiarity)

**Option B — Meta MusicGen (AI-generated, runs locally, 100% free)**
- Open-source model from Meta: `facebook/musicgen-small` (300M params, runs on CPU)
- Text-to-music: "happy children's xylophone melody, major key, 120 bpm"
- Generates 15-30 second custom clips per poem
- Python package: `audiocraft` (requires PyTorch)
- **Pros:** Unique melody per video, fully automated, no API cost, no rate limits
- **Cons:** Needs ~2GB disk for model, first run downloads weights, CPU generation takes ~30-60s per clip
- **Example prompts by poem type:**
  - Counting: "playful pizzicato strings, children's counting song, C major, 110 bpm"
  - Bedtime: "gentle music box lullaby, soft piano, slow tempo, 70 bpm"
  - Animals: "bouncy ukulele melody, happy, children's song, 120 bpm"
  - Alphabet: "cheerful glockenspiel and claps, educational kids song, 130 bpm"

**Option C — Suno AI Free Tier (best quality, limited)**
- Free tier: 10 songs/day (50/month with credits)
- Web-based, no local setup
- Best audio quality of all free options
- **Cons:** Rate-limited, requires manual download (no API), can't fully automate
- **Use for:** Special videos, compilations, hero content

**Recommended strategy:**
1. Start with **Option A** (YouTube Audio Library) — zero setup, instant publishing
2. Add **Option B** (MusicGen) later for unique per-video melodies
3. Use **Option C** (Suno) for weekly compilation soundtracks only

**Music caching:** Regardless of approach, cache generated/selected tracks in a registry so the same poem type consistently uses the same mood of music. Kids like predictability.

#### Step 4: Narration (`kids_04_voiceover.py`)
- **Tool:** Edge TTS (already in pipeline)
- **Voice options:**
  - `en-US-AnaNeural` — young female, warm, perfect for kids
  - `en-US-GuyNeural` — friendly male narrator
  - `en-GB-MaisieNeural` — British children's voice
- **Speed:** Slower than adult content (rate=-10% to -20%) — kids need time to process
- **Emphasis:** Add pauses between verses (500ms silence gaps)

#### Step 5: Video Assembly (`kids_05_make_video.py`)
- **Resolution:** 1080x1920 (Shorts) or 1920x1080 (long-form compilations)
- **Subtitle style:**
  - Large, rounded font (Comic Sans or similar kid-friendly font)
  - Bright colored text with dark outline
  - Word-by-word highlight (karaoke style) — kids follow along
  - Each word lights up as it's spoken — teaches reading
- **End card:** "Subscribe for more poems!" with animated stars
- **Watermark:** Small channel logo in corner

#### Step 6: Thumbnail (`kids_06_thumbnail.py`)
- **Style:** Bright, colorful, large character face, big text
- **Tool:** Whisk or Gemini image generation
- **Template:** Main character/animal from poem + 2-3 word title in bubbly font
- **Colors:** Yellow, red, blue, green — primary colors that attract kids' eyes

#### Step 7: Upload (`kids_07_upload.py`)
- **Schedule:** 3 Shorts/day + 1 compilation/week
- **Category:** Education (ID: 27) or Entertainment (ID: 24)
- **Made for Kids:** `selfDeclaredMadeForKids: True` (CRITICAL — unlocks kids' algorithm)
- **Tags:** nursery rhymes, kids poems, children songs, learn colors, ABC, etc.
- **Playlists:** Auto-group by theme (Animal Poems, Bedtime Poems, Counting Poems)

---

## Content Categories (Rotate Weekly)

| Category | Example Poems | Visual Style |
|----------|--------------|-------------|
| **Nursery Rhymes** | Twinkle Twinkle, Humpty Dumpty, Jack and Jill | Classic storybook |
| **Animal Poems** | "The Lazy Cat", "Five Little Ducks" | Cute cartoon animals |
| **Counting Poems** | "1-2-3 Count With Me", "Ten Little Fingers" | Numbers with objects |
| **Bedtime Poems** | "Goodnight Moon", "Sleepy Stars" | Soft, dreamy pastels |
| **Alphabet Poems** | "A is for Apple", "ABC Adventure" | Bold letters + objects |
| **Season/Holiday** | "Snowflake Song", "Pumpkin Patch" | Seasonal themes |
| **Color Poems** | "Red Red Red", "Rainbow Day" | Single dominant color per verse |
| **Action Poems** | "Clap Your Hands", "Jump Jump Jump" | Animated characters moving |

---

## Long-Form Compilation Strategy

Weekly compilation = stitch 10-15 Shorts into one 10-15 minute video.

- **Title:** "Nursery Rhymes Collection | 30 Minutes of Kids Poems"
- **Value:** Parents put these on loop → massive watch hours
- **Timestamps:** Each poem gets a chapter marker
- **Transition:** 2-second colorful wipe between poems
- **Music:** Continuous background melody throughout

This is the **watch hours machine**. Even if Shorts drive the 3M views, compilations drive the 3,000 watch hours (alternative YPP path).

---

## Directory Structure

```
kids_poems/
├── config.py              # Channel config, voice settings, color palettes
├── main.py                # Daily pipeline: 3 Shorts/day
├── batch_main.py          # Weekly batch: 21 Shorts + 1 compilation
├── compile_weekly.py      # Stitch week's Shorts into long-form compilation
├── scripts/
│   ├── kids_01_write_poem.py       # Gemini Pro poem generation
│   ├── kids_02_generate_visuals.py # Flow/Whisk visual generation
│   ├── kids_03_generate_music.py   # ProducerAI music generation
│   ├── kids_04_voiceover.py        # Edge TTS narration (slow, warm)
│   ├── kids_05_make_video.py       # FFmpeg assembly + karaoke subtitles
│   ├── kids_06_thumbnail.py        # Bright colorful thumbnail
│   └── kids_07_upload.py           # YouTube upload (Made for Kids = true)
├── poems/
│   ├── public_domain/     # Classic nursery rhymes (text files)
│   └── generated/         # AI-generated poems cache
├── music/                 # ProducerAI generated + royalty-free tracks
├── fonts/                 # Kid-friendly fonts (Comic Sans, Bubblegum, etc.)
├── output/                # Current video build
├── archive/               # Completed videos
└── credentials.json       # YouTube API (separate from NextLevelMind)
```

---

## Made for Kids — Important Rules

YouTube "Made for Kids" content has special rules:

1. **No personalized ads** — revenue comes from non-personalized ads (lower CPM but still pays)
2. **No comments** — comments are automatically disabled
3. **No notifications** — subscribers don't get notified (algorithm-driven discovery only)
4. **No community posts** — can't use community tab
5. **No stories** — can't post stories
6. **Algorithm is EVERYTHING** — since there are no notifications, YouTube's kids algorithm must push your content. High completion rate + rewatches = push.

**This means:** Quality visuals + catchy music + short duration = the ENTIRE strategy. No CTA overlays, no "subscribe" reminders — just pure content quality.

---

## YPP Timeline Estimate

| Metric | Target | Estimate |
|--------|--------|----------|
| Subscribers | 500 | 4-6 weeks (kids' parents subscribe in clusters) |
| Shorts views (90 days) | 3,000,000 | 6-10 weeks (kids rewatch = view multiplier) |
| Watch hours (if doing compilations) | 3,000 | 8-12 weeks |
| Videos needed | ~150-200 Shorts | 7-10 weeks at 3/day |

Kids' content typically hits YPP **2-3x faster** than adult motivation content because of the rewatch multiplier.

---

## Shared Infrastructure with NextLevelMind

| Component | Shared? | Notes |
|-----------|---------|-------|
| Edge TTS | Yes | Different voice config |
| FFmpeg | Yes | Different subtitle style |
| YouTube API code | Yes (shared/youtube_api.py) | Different credentials.json |
| Google AI Pro account | Yes | Same API key, same limits |
| Gemini API | Yes | Same GEMINI_API_KEY |
| Server/Dashboard | Future | Add kids channel tab |

---

## Implementation Order

| Phase | What | Effort |
|-------|------|--------|
| **Phase 1** | `config.py` + `kids_01_write_poem.py` + `kids_04_voiceover.py` | 1 session |
| **Phase 2** | `kids_05_make_video.py` (with Whisk images + Ken Burns) + music from YouTube Audio Library | 1 session |
| **Phase 3** | `kids_06_thumbnail.py` + `kids_07_upload.py` + `main.py` | 1 session |
| **Phase 4** | `kids_02_generate_visuals.py` (Flow integration when API available) | 1 session |
| **Phase 5** | `kids_03_music.py` (Meta MusicGen local AI music generation) | 1 session |
| **Phase 6** | `compile_weekly.py` (long-form compilations) | 1 session |
| **Phase 7** | `batch_main.py` (full weekly automation) | 1 session |

**Phase 1-3 gets you publishing with zero music cost** (YouTube Audio Library tracks).
**Phase 5 adds unique AI-generated melodies** per video via MusicGen (still free, just needs setup).

---

## Next Steps

1. Pick a channel name
2. Create the YouTube channel + get credentials.json
3. Start Phase 1 build
