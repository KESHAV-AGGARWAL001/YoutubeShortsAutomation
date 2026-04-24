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
| Gemini 2.5 Pro | Poem generation + SEO (primary) | Free (AI Pro) |
| Groq (Llama 3.1 8B) | Poem generation (fallback when Gemini overloaded) | Free (1,000 req/day) |
| Veo 3.1 | Animated cartoon clips per verse | ~$2-4/day (AI Pro) |
| Gemini 2.0 Flash | Image generation (primary) | Free |
| HuggingFace SDXL | Image generation (fallback when Gemini overloaded) | Free |
| Edge TTS | Warm child-friendly voiceover | Free |
| Freesound.org | Background music — CC0 license (auto-download) | Free |
| YouTube Audio Library | Background music (manual download alternative) | Free |
| FFmpeg | Video/audio processing | Free |
| YouTube Data API v3 | Upload + scheduling | Free |

**Daily cost: ~$2-4/day** (Veo clips only). Set `KP_VEO_ENABLED=false` for $0/day with static images.

---

## AI Fallback Chain — Never Stuck on Traffic

The pipeline automatically switches providers when one is overloaded. No manual intervention needed.

```
Poem Generation:    Gemini 2.5 Pro → Gemini 2.0 Flash → Groq (Llama 3.1 8B)
Image Generation:   Gemini 2.0 Flash → HuggingFace (Stable Diffusion XL) → local assets/images/
Video Clips:        Veo 3.1 → Veo 3.1 Lite → static image + Ken Burns
```

| Provider | Models Used | When It Kicks In |
|----------|------------|-----------------|
| **Gemini (primary)** | `gemini-2.5-pro` for poems, `gemini-2.0-flash-exp` for images | Always tried first |
| **Groq (text fallback)** | `llama-3.1-8b-instant` for poems | When Gemini returns 429/overloaded/quota errors |
| **HuggingFace (image fallback)** | `stable-diffusion-xl` for images | When Gemini image generation fails |
| **Local assets (last resort)** | Pre-downloaded images from `assets/images/` | When both AI providers fail |

### Groq Setup (One-Time)

1. Create a free account at https://console.groq.com (no credit card needed)
2. Create an API key from the dashboard
3. Add to `kids_poems/.env`:
   ```
   GROQ_API_KEY=gsk_your_groq_api_key_here
   ```

**Free tier limits:** 1,000 requests/day, 30 requests/min — more than enough for 3 videos/day (~15-20 text calls).

### HuggingFace Setup (One-Time — Images Only)

1. Create a free account at https://huggingface.co/
2. Get your access token at https://huggingface.co/settings/tokens (read access is enough)
3. Add to `kids_poems/.env`:
   ```
   HF_TOKEN=hf_your_token_here
   ```

### How the Fallback Works

- Gemini overloaded? → Pipeline prints "switching to Groq" and continues automatically
- Groq rate limited? → Retries with exponential backoff (3 attempts)
- Both providers down? → Pipeline fails with clear error message
- For images: Gemini fails → HuggingFace SDXL → local assets/images/
- The `_gemini_failed` flag persists within a single run — once Gemini fails for images, all remaining images use HuggingFace (avoids wasting time on repeated 429 errors)

---

## Google AI Pro Benefits — How We Use Them

| AI Pro Feature | How We Use It |
|---|---|
| **Gemini 2.5 Pro** | Generate original poems + visual descriptions + SEO metadata |
| **Veo 3.1** | Generate animated cartoon clips per verse (primary visual pipeline) |
| **Veo 3.1 Lite** | Fallback model if Veo 3.1 fails (half cost) |
| **Google AI Studio** | Higher API limits for batch production (3 videos/day) |
| **5 TB Storage** | Archive all generated assets + videos |
| **1,000 AI Credits** | Overflow capacity for heavy generation weeks |

**Not using AI Pro for music** — Freesound.org (CC0, auto-download) + YouTube Audio Library (manual).

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

### Automated Download — `download_music.py` (Recommended)

Downloads copyright-free music from Freesound.org. All tracks are CC0 (Creative Commons 0) — free for commercial use, no attribution needed, safe for YouTube monetization.

**Steps to set up and run:**

1. Create a free account at https://freesound.org/home/register/
2. Get your API key at https://freesound.org/apiv2/apply/
   - Choose "APIv2 credential"
   - Any description works (e.g., "Kids poems channel music")
   - Key is shown immediately after applying
3. Add to `kids_poems/.env`:
   ```
   FREESOUND_API_KEY=your_freesound_api_key_here
   ```
4. Run the script:
   ```bash
   cd kids_poems

   # List available moods and search terms
   python download_music.py --list

   # Download all moods (~35 tracks per mood)
   python download_music.py

   # Download one mood only
   python download_music.py --mood calm

   # Download more tracks per search term
   python download_music.py --limit 10
   ```
5. Tracks are saved directly into `kids_poems/music/{mood}/`

**Search terms per mood:**

| Mood | Search Terms |
|------|-------------|
| **upbeat** | happy children music, kids fun melody, upbeat cartoon music, cheerful ukulele kids, energetic xylophone children |
| **calm** | lullaby music box, gentle piano lullaby, soft kids bedtime music, calm music box melody, sleeping baby music |
| **playful** | cheerful glockenspiel kids, playful marimba children, funny cartoon music, happy whistle melody, kids toy piano music |
| **magical** | magical fairy music, dreamy celesta melody, whimsical music box fairy, enchanted harp children, sparkle chime magical |

**Output:** ~100-140 tracks across 4 moods (depends on search results)

### Manual Alternative — YouTube Audio Library

If you prefer hand-picked tracks, download 8-10 per mood from [YouTube Audio Library](https://studio.youtube.com/channel/UC/music).

### Folder Structure

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

## Fallback Image Download Scripts

Three automated scripts to build your `assets/images/` library. These images are used as fallback when Veo or Gemini image generation fails during video production.

### Script Comparison

| Script | Source | Cost | Copyright | Quality | Setup |
|--------|--------|------|-----------|---------|-------|
| `generate_fallback_batch.py` | Gemini AI | Free (API quota) | You own them | Best — exact pipeline style match | Just needs `KP_GEMINI_API_KEY` |
| `download_pixabay.py` | Pixabay API | Free | Pixabay License (commercial OK) | Good — real illustrations | Free account + API key |
| `download_pinterest.py` | Pinterest | Free | Check per image | Mixed — needs manual review | `pip install gallery-dl` |

### Recommended Order

**Start with Script 1** (Gemini) — it produces images in the exact same style your pipeline uses. Add Script 2 (Pixabay) for variety. Use Script 3 (Pinterest) only if you need more volume.

---

### Script 1: Gemini Batch Generator (Recommended)

Generates images using your own AI Pro API key. Perfect style match, 100% copyright-free.

**Steps to set up and run:**

1. Make sure `KP_GEMINI_API_KEY` is set in `kids_poems/.env`
2. Run the script:
   ```bash
   cd kids_poems

   # List all categories and prompt counts
   python generate_fallback_batch.py --list

   # Generate all categories (74 images total)
   python generate_fallback_batch.py

   # Generate one category only
   python generate_fallback_batch.py --category animal

   # Limit to 5 images per category
   python generate_fallback_batch.py --count 5
   ```
3. Images are saved to `kids_poems/assets/images/{category}/`
4. Takes ~2-3 minutes per category (API rate limits)

**Output:** ~74 images across 9 categories (general, animal, nursery_rhyme, counting, alphabet, colors, bedtime, seasonal, action)

---

### Script 2: Pixabay API Downloader

Downloads free, copyright-safe illustrations from Pixabay. Good variety, legal for commercial use.

**Steps to set up and run:**

1. Create a free Pixabay account: https://pixabay.com/accounts/register/
2. Get your API key: https://pixabay.com/api/docs/ (scroll to "Search Images" → your key is shown at the top)
3. Add to `kids_poems/.env`:
   ```
   PIXABAY_API_KEY=your_pixabay_api_key_here
   ```
4. Run the script:
   ```bash
   cd kids_poems

   # List all categories
   python download_pixabay.py --list

   # Download all categories (10 images per search term)
   python download_pixabay.py

   # Download one category only
   python download_pixabay.py --category bedtime

   # Download 15 images per search term
   python download_pixabay.py --limit 15
   ```
5. Images are saved to `kids_poems/assets/images/{category}/`

**Output:** ~450+ images across 9 categories (depends on available results)

---

### Script 3: Pinterest Scraper

Scrapes images from Pinterest search results. Largest volume, but requires manual copyright review.

**Steps to set up and run:**

1. Install gallery-dl:
   ```bash
   pip install gallery-dl
   ```
2. Run the script:
   ```bash
   cd kids_poems

   # List all categories
   python download_pinterest.py --list

   # Download all categories (10 images per search term)
   python download_pinterest.py

   # Download one category only
   python download_pinterest.py --category colors

   # Download 20 images per search term
   python download_pinterest.py --limit 20
   ```
3. Images are saved to `kids_poems/assets/images/{category}/`
4. **Important:** Manually review downloaded images — Pinterest images may have varying copyright. Only use for reference/inspiration unless you verify the license.

**Output:** ~600+ images across 9 categories

---

### After Downloading

All three scripts save images into the same folder structure:

```
kids_poems/assets/images/
├── general/          — generic kids cartoon illustrations
├── animal/           — cartoon animals (ducks, bunnies, elephants)
├── nursery_rhyme/    — classic rhyme scenes (Humpty Dumpty, stars)
├── counting/         — number characters, counting scenes
├── alphabet/         — ABC letters, alphabet animals
├── colors/           — rainbow, primary colors, shapes
├── bedtime/          — moon, stars, sleepy characters
├── seasonal/         — Christmas, Easter, seasons
└── action/           — dancing, jumping, clapping kids
```

The pipeline's `image_generator.py` automatically picks from these folders when AI image generation fails. No extra configuration needed — just populate the folders and the fallback works.

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
| `KP_GEMINI_MODEL` | `gemini-2.5-pro` | AI model for poems |
| `KP_GEMINI_IMAGE_MODEL` | `gemini-2.0-flash-exp` | AI model for images |
| `GROQ_API_KEY` | — | Groq API key (text fallback — free, 1000 req/day) |
| `KP_GROQ_MODEL` | `llama-3.1-8b-instant` | Groq model for poems |
| `HF_TOKEN` | — | HuggingFace API token (image fallback only) |
| `KP_HF_IMAGE_MODEL` | `stabilityai/stable-diffusion-xl-base-1.0` | HF image model (SDXL) |
| `KP_VEO_ENABLED` | `true` | Enable Veo animated clips |
| `KP_VEO_MODEL` | `veo-3.1-generate-preview` | Veo model |
| `KP_VEO_USE_LITE` | `false` | Use Veo Lite as fallback |
| `KP_VEO_TIMEOUT` | `300` | Veo generation timeout (seconds) |
| `KP_VEO_ENHANCE_PROMPT` | `true` | Let Veo enhance prompts |
| `KP_VEO_MAX_WORKERS` | `4` | Parallel clip generation workers |
| `FREESOUND_API_KEY` | — | Freesound.org API key (for music download) |
| `PIXABAY_API_KEY` | — | Pixabay API key (for image download) |

---

## Shared Infrastructure with NextLevelMind

| Component | Shared? | Notes |
|-----------|---------|-------|
| Edge TTS | Yes | Different voice config (slower, higher pitch) |
| FFmpeg | Yes | Different subtitle style (larger, colorful) |
| Gemini API | **No** | Separate `KP_GEMINI_API_KEY` in `kids_poems/.env` |
| Google AI Pro | Yes | Same subscription, shared Veo quota |
| YouTube API code | Pattern shared | Separate OAuth credentials per channel |
