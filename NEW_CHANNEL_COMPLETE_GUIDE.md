# End-to-End Guide: Creating a New YouTube Channel (From Zero to First Upload)

> **Purpose:** Step-by-step playbook to launch any new YouTube channel using your automation pipeline  
> **Time Required:** 2-4 hours for full setup  
> **Prerequisites:** Python installed, FFmpeg installed, Gemini API key, Internet connection  
> **Last Updated:** April 21, 2026  

---

## TABLE OF CONTENTS

1. [Pre-Launch Planning](#1-pre-launch-planning)
2. [Google Account & YouTube Channel Creation](#2-google-account--youtube-channel-creation)
3. [Channel Branding & Customization](#3-channel-branding--customization)
4. [Google Cloud & YouTube API Setup](#4-google-cloud--youtube-api-setup)
5. [Pipeline Setup & Configuration](#5-pipeline-setup--configuration)
6. [Content Preparation](#6-content-preparation)
7. [First Video: Generate, Review, Upload](#7-first-video-generate-review-upload)
8. [Upload Schedule & Automation](#8-upload-schedule--automation)
9. [SEO & Discoverability Optimization](#9-seo--discoverability-optimization)
10. [Monetization Setup](#10-monetization-setup)
11. [Growth Playbook (First 30 Days)](#11-growth-playbook-first-30-days)
12. [Safety & Compliance Checklist](#12-safety--compliance-checklist)
13. [Troubleshooting](#13-troubleshooting)
14. [Channel Launch Checklist](#14-channel-launch-checklist)

---

## 1. PRE-LAUNCH PLANNING

Before creating anything, answer these questions:

### 1.1 Define Your Channel Identity

| Question | Your Answer |
|---|---|
| **Channel Name** | ________________________________ |
| **Niche / Topic** | ________________________________ |
| **Target Audience** | ________________________________ |
| **Primary Language** | ________________________________ |
| **Content Format** | Shorts / Long-form / Both |
| **Upload Frequency** | _____ Shorts/day + _____ Long-form/week |
| **Monetization Plan** | AdSense / Affiliate / Courses / Sponsorships |

### 1.2 Niche Validation Checklist

Before committing to a niche, verify these:

- [ ] **Search demand exists** — Search your topic on YouTube. Are there videos with 100K+ views?
- [ ] **Competition is beatable** — Are the top channels in this niche <500K subscribers? If yes, you can compete.
- [ ] **Content is producible with your pipeline** — Can you automate script + voiceover + visuals?
- [ ] **Monetization path is clear** — What will you sell/promote? AdSense alone is not enough.
- [ ] **You can produce 30+ days of content** — List at least 30 video topics right now. If you can't, niche is too narrow.
- [ ] **CPM is worth it** — Check CPM for your niche (see MILLIONAIRE_BLUEPRINT_2026.md Section 4)

### 1.3 Competitive Research (15 Minutes)

Do this before creating the channel:

1. **Search YouTube** for your main topic (e.g., "dark psychology", "maths tricks")
2. **Find 5 top channels** in your niche
3. For each, note:
   - Subscriber count
   - Average views per video (last 10 videos)
   - Upload frequency
   - Video length (Shorts vs long-form ratio)
   - Thumbnail style (colors, text, faces?)
   - Title patterns (questions? numbers? emotional words?)
   - Description format (affiliate links? timestamps?)
4. **Identify gaps** — What are they NOT doing that you could do?

Write your findings here:

| Competitor Channel | Subs | Avg Views | Upload Freq | Gap / Opportunity |
|---|---|---|---|---|
| 1. ________________ | _____ | _____ | _________ | _________________ |
| 2. ________________ | _____ | _____ | _________ | _________________ |
| 3. ________________ | _____ | _____ | _________ | _________________ |
| 4. ________________ | _____ | _____ | _________ | _________________ |
| 5. ________________ | _____ | _____ | _________ | _________________ |

### 1.4 Content Pipeline Decision

Your automation platform supports multiple video formats. Choose the right one:

| Format | Best For | Pipeline To Use | Setup Time |
|---|---|---|---|
| **Book-to-Shorts** | Dark Psychology, Motivation, Storytelling | Existing `main.py` pipeline | 30 min (clone config) |
| **Book-to-Long-form** | Deep dives, tutorials, explanations | Existing `long_form_main.py` pipeline | 30 min (clone config) |
| **Slideshow + Voiceover** | Devotional, relaxation, ambient | `radha_krishna/` pipeline | 1 hour (clone + customize) |
| **Whiteboard / Screen Recording** | Maths teaching, coding tutorials | New pipeline needed | 2-3 hours (build new) |
| **AI Image + Narration** | Science facts, history, "What If" | Modify existing pipeline | 1-2 hours |

---

## 2. GOOGLE ACCOUNT & YOUTUBE CHANNEL CREATION

### 2.1 Decide: Same Account or New Account?

| Scenario | Recommendation |
|---|---|
| New niche, same audience (e.g., Finance + Motivation) | Use SAME Google account, create new channel via Brand Account |
| Completely different niche (e.g., Devotion + Dark Psychology) | Use DIFFERENT Google account |
| Want USA CPM rates | Create new account on US VPN (see `new_account_setup_guide.md`) |
| Indian audience channel (Hindi content) | Can use regular Indian account — no VPN needed |

### 2.2 Create YouTube Channel

**Option A: New Channel on Existing Google Account (Brand Account)**

1. Go to **https://www.youtube.com**
2. Click your profile icon (top-right) → **Settings**
3. Click **Add or manage your channels**
4. Click **Create a channel**
5. Enter your channel name → Click **Create**
6. This creates a "Brand Account" — separate from your personal account
7. Your existing channels are NOT affected

**Option B: New Channel on New Google Account**

1. Follow **`new_account_setup_guide.md`** Steps 1-3
2. Summary:
   - Create new Google account (use VPN if targeting US audience)
   - Go to YouTube → Create channel
   - Set channel name and handle

### 2.3 Channel Handle Selection Tips

Your handle (`@YourHandle`) is permanent and important:

- **Keep it short** — under 15 characters
- **Make it memorable** — easy to spell and say out loud
- **Match your brand** — `@DarkMindLab`, `@MathsWithKeshav`, `@MoneyMindHindi`
- **Check availability** — search on YouTube before deciding
- **No numbers if possible** — `@DarkPsych` looks better than `@DarkPsych2026`

### 2.4 Record Your Channel Details

| Field | Value |
|---|---|
| Google Account Email | ________________________________ |
| Google Account Password | (stored securely — not here) |
| YouTube Channel Name | ________________________________ |
| YouTube Handle | @______________________________ |
| Channel URL | youtube.com/@__________________ |
| Channel ID | ________________________________ |
| Country Setting | ________________________________ |
| Language Setting | ________________________________ |

---

## 3. CHANNEL BRANDING & CUSTOMIZATION

### 3.1 Visual Identity

Create these assets before your first upload:

| Asset | Size | Tool | Notes |
|---|---|---|---|
| **Profile Picture** | 800 x 800 px | Canva / Photoshop | Your logo or brand icon. Simple, readable at small sizes. |
| **Banner Image** | 2560 x 1440 px | Canva | Shows channel name + tagline. Safe area: center 1546x423 px |
| **Video Watermark** | 150 x 150 px (PNG, transparent) | Canva | Small subscribe button overlay on all videos |
| **Thumbnail Template** | 1280 x 720 px | Canva / PIL | Consistent style across all videos (colors, fonts, layout) |

### 3.2 Branding Style Guide Per Niche

| Channel Niche | Color Palette | Font Style | Thumbnail Style | Mood |
|---|---|---|---|---|
| **Devotional** | Gold, saffron, deep blue | Elegant serif / Devanagari | Warm, glowing, divine imagery | Peaceful, spiritual |
| **Dark Psychology** | Black, red, dark purple | Bold sans-serif, ALL CAPS | Dark backgrounds, intense eyes, bold text | Mysterious, intense |
| **Personal Finance** | Green, blue, white | Clean sans-serif | Charts, money imagery, numbers | Professional, trustworthy |
| **Maths Teaching** | Blue, white, orange | Clear sans-serif, readable | Whiteboard style, equations, colorful | Educational, friendly |

### 3.3 YouTube Studio Customization

Go to **YouTube Studio → Customization**:

#### Basic Info Tab
1. **Channel Name:** Your brand name
2. **Handle:** @YourHandle
3. **Description:** Write a compelling description (see templates below)
4. **Channel Keywords:** Add 15-25 relevant keywords separated by commas
5. **Links:** Add your social media, website, affiliate links

#### Channel Description Templates

**Devotional Channel:**
```
जय श्री कृष्ण | राधे राधे

भगवद्गीता के शक्तिशाली उपदेश, श्री कृष्ण की अद्भुत लीलाएं, 
और आध्यात्मिक ज्ञान — हर दिन नए वीडियो।

कर्म करो, फल की चिंता मत करो — गीता सार

Topics: Bhagavad Gita, Radha Krishna, Spirituality, Karma Yoga, 
Bhakti, Dharma, Hindu Philosophy, गीता सार, कृष्ण उपदेश

Subscribe करें और bell icon दबाएं — रोज़ नया ज्ञान पाएं।
```

**Dark Psychology Channel:**
```
The human mind is the most powerful — and dangerous — weapon.

We break down dark psychology, manipulation tactics, body language 
secrets, and cognitive biases so you can PROTECT yourself.

Every video is backed by real psychological research.

New videos daily — Subscribe if you want to understand the 
hidden forces that control human behavior.

Topics: Dark Psychology, Manipulation, Body Language, Cognitive Biases, 
Persuasion, Social Engineering, Human Behavior, Mind Games
```

**Personal Finance Channel (Hindi):**
```
पैसा कमाना आसान है — पैसा बचाना और बढ़ाना सीखो।

SIP, Mutual Funds, Stock Market, Budgeting, Tax Saving — 
सब कुछ आसान भाषा में।

हर हफ्ते नए videos — Subscribe करें और अमीर बनने का सफर शुरू करें।

Disclaimer: यह channel educational purposes के लिए है। 
निवेश से पहले SEBI-registered advisor से सलाह लें।

Topics: Personal Finance India, SIP, Mutual Funds, Stock Market Hindi, 
Budgeting, Tax Saving, Financial Freedom, पैसे कैसे बचाएं
```

**Maths Teaching Channel:**
```
Maths is not hard — it just needs the right teacher.

Shortcut tricks, concept explanations, exam preparation — 
Class 9 to 12, JEE, Board Exams, Competitive Exams.

हर concept को आसान भाषा में समझो — Hindi + English.

Topics: Maths Tricks, JEE Preparation, Board Exam Maths, 
NCERT Solutions, Mental Math, Competitive Exam Quant, 
Algebra, Trigonometry, Calculus, Geometry
```

#### Branding Tab
1. Upload **Profile Picture** (800x800)
2. Upload **Banner Image** (2560x1440)
3. Upload **Video Watermark** (150x150 PNG)

#### Layout Tab
1. **Channel Trailer:** Leave empty until you have 5+ videos, then add your best-performing video
2. **Featured Sections:** Add "Short videos" and "Popular uploads"
3. After 10+ videos: Add **Playlists** as featured sections (topic-based organization)

### 3.4 Upload Defaults (Set Once, Applies to All Videos)

Go to **YouTube Studio → Settings → Upload defaults**:

**Basic Info:**
| Setting | Value |
|---|---|
| Title | Leave empty (pipeline fills this) |
| Description | Leave empty (pipeline fills this) |
| Visibility | Private (pipeline handles scheduling) |
| Tags | Leave empty (pipeline fills this) |

**Advanced Settings:**
| Setting | Value | Notes |
|---|---|---|
| Language | Match your content (Hindi / English US) | Affects algorithm targeting |
| Category | Education / People & Blogs / Entertainment | Match your niche |
| License | Standard YouTube License | Default |
| Comments | Hold potentially inappropriate for review | Filters spam |
| Allow embedding | Yes | More distribution |
| Publish to subscriptions feed | Yes | Notify subscribers |

---

## 4. GOOGLE CLOUD & YOUTUBE API SETUP

> Full detailed guide: **`youtube_setup_guide.md`**  
> Summary of key steps below:

### 4.1 Quick Setup (5 Steps)

1. **Google Cloud Project** — Go to console.cloud.google.com → New Project → Name it (e.g., "DarkPsychBot")

2. **Enable API** — APIs & Services → Library → Search "YouTube Data API v3" → Enable

3. **OAuth Consent Screen** — APIs & Services → OAuth consent screen:
   - App name: your bot name
   - Add scopes: `youtube`, `youtube.upload`, `youtube.force-ssl`
   - Add your Gmail as test user

4. **Create Credentials** — APIs & Services → Credentials → Create → OAuth client ID:
   - Type: Desktop app
   - Download JSON → rename to `client_secrets_CHANNELNAME.json`
   - Place in your channel's pipeline folder

5. **First Auth** — Run your upload script once. Browser opens → login → authorize → `token.json` created.

### 4.2 Credential File Naming Convention

Keep credentials organized per channel:

```
YoutubeShortsAutomation/
├── credentials.json                    ← Main/existing channel
├── radha_krishna/
│   ├── client_secrets_rk.json          ← Radha Krishna channel
│   └── token_rk.json
├── dark_psychology/                    ← (to be created)
│   ├── client_secrets_dp.json
│   └── token_dp.json
├── personal_finance/                   ← (to be created)
│   ├── client_secrets_pf.json
│   └── token_pf.json
└── maths_teaching/                     ← (to be created)
    ├── client_secrets_mt.json
    └── token_mt.json
```

### 4.3 API Quota Planning

Each Google Cloud project gets **10,000 quota units/day**:

| Operation | Units | Per Day Limit |
|---|---|---|
| Video Upload | 1,600 | ~6 uploads |
| Thumbnail Set | 50 | ~200 |
| Caption Upload | 400 | ~25 |
| Playlist Insert | 50 | ~200 |

**Per-Channel Daily Budget (3 Shorts + 1 Long-form):**
- Uploads: 4 × 1,600 = 6,400 units
- Thumbnails: 4 × 50 = 200 units
- Captions: 4 × 400 = 1,600 units
- **Total: ~8,200 units/day** (within 10,000 limit)

> **If you exceed quota:** Each channel has its OWN Google Cloud project with its OWN 10,000 units. You never share quota between channels.

### 4.4 Phone Verification (Required for Custom Thumbnails)

1. Go to **https://www.youtube.com/verify** (logged into new channel account)
2. Verify via SMS or phone call
3. Options for verification numbers:
   - Your personal phone (works with Indian numbers)
   - Google Voice (free US number)
   - TextNow (free US number)
4. One phone number can verify up to **2 channels per year**

---

## 5. PIPELINE SETUP & CONFIGURATION

### 5.1 Choose Your Pipeline Architecture

Based on your niche, select and set up the right pipeline:

#### Option A: Clone Existing Book-to-Shorts Pipeline
**Best for:** Dark Psychology, Personal Finance, Motivation, Storytelling

```bash
# Create new channel directory
mkdir dark_psychology
cd dark_psychology

# Create required subdirectories
mkdir books output archive content music
```

**Files to create/configure:**

1. **`.env`** — Channel-specific environment variables:
```env
# Channel: Dark Psychology
GEMINI_API_KEY=your_gemini_key_here
YOUTUBE_CLIENT_SECRET=client_secrets_dp.json

# TTS Voice (pick one)
# English dramatic male:
TTS_VOICE=en-US-GuyNeural
TTS_RATE=-10%
TTS_PITCH=-2Hz

# English dramatic female:
# TTS_VOICE=en-US-AriaNeural
# TTS_RATE=-5%
# TTS_PITCH=+0Hz

# Hindi male (for Hindi channels):
# TTS_VOICE=hi-IN-MadhurNeural
# TTS_RATE=-5%
# TTS_PITCH=+0Hz

# Upload Schedule (EST timezone)
UPLOAD_TIME_1=09:00
UPLOAD_TIME_2=16:00
```

2. **`config.py`** — Channel-specific settings:
```python
import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
load_dotenv(os.path.join(BASE_DIR, ".env"), override=True)

# ── Channel Identity ──
CHANNEL_NAME = "Dark Psychology"
CHANNEL_NICHE = "psychology"
YOUTUBE_CATEGORY_ID = "27"  # Education

# ── Paths ──
BOOK_DIR = os.path.join(BASE_DIR, "books")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
MUSIC_DIR = os.path.join(BASE_DIR, "music")

# ── Video Settings ──
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920  # 9:16 for Shorts
VIDEO_FPS = 30

# ── YouTube Credentials ──
YOUTUBE_CLIENT_SECRETS = os.getenv(
    "YOUTUBE_CLIENT_SECRET",
    os.path.join(BASE_DIR, "client_secrets_dp.json"),
)
YOUTUBE_TOKEN = os.path.join(BASE_DIR, "token_dp.json")
```

3. **Source Books** — Place PDF books in the `books/` folder:
   - Dark Psychology: "48 Laws of Power", "Influence", etc.
   - Personal Finance: "Rich Dad Poor Dad", "The Psychology of Money", etc.

4. **Background Music** — Place royalty-free tracks in `music/`:
   - Dark Psychology: Suspenseful, cinematic ambient
   - Personal Finance: Professional, upbeat background
   - Sources: YouTube Audio Library (free), Pixabay Music (free)

#### Option B: Clone Radha Krishna Slideshow Pipeline
**Best for:** Devotional, Ambient, Relaxation, Quote channels

```bash
# Copy the radha_krishna structure
cp -r radha_krishna/ new_channel_name/

# Update config.py with new channel settings
# Update .env with new credentials
# Replace assets/images/ with niche-appropriate images
# Replace assets/music/ with niche-appropriate music
```

#### Option C: Build Whiteboard/Screen Recording Pipeline
**Best for:** Maths Teaching, Coding tutorials, How-to guides

This requires a different approach — not slideshow-based:

```bash
mkdir maths_teaching
cd maths_teaching
mkdir lessons output recordings scripts
```

**Workflow for Whiteboard Content:**
1. **Write lesson script** → `scripts/lesson_XX.txt`
2. **Record screen** (OBS Studio or tablet recording)
   - Use Samsung Notes / OneNote / Excalidraw as digital whiteboard
   - Record yourself solving problems step by step
3. **Generate voiceover** (Edge TTS) → FFmpeg merges audio + recording
4. **Add intro/outro** (FFmpeg concat)
5. **Upload to YouTube** (same upload script)

**Alternative: Manim Animations (3Blue1Brown style)**
```bash
# Manim generates beautiful math animations programmatically
# Each lesson is a Python script that produces a video
# Example: animate solving a quadratic equation step by step
```

### 5.2 TTS Voice Selection Guide

Choose the right voice for your channel's personality:

| Channel Niche | Recommended Voice | Voice Code | Language | Personality |
|---|---|---|---|---|
| Devotional (Hindi) | Swara | `hi-IN-SwaraNeural` | Hindi | Sweet, calm, devotional |
| Devotional (Hindi Alt) | Madhur | `hi-IN-MadhurNeural` | Hindi | Mature, warm |
| Dark Psychology | Guy | `en-US-GuyNeural` | English | Deep, serious, dramatic |
| Dark Psychology (Alt) | Davis | `en-US-DavisNeural` | English | Authoritative, confident |
| Personal Finance (Hindi) | Madhur | `hi-IN-MadhurNeural` | Hindi | Trustworthy, professional |
| Personal Finance (English) | Andrew | `en-US-AndrewNeural` | English | Clear, professional |
| Maths Teaching (Hindi) | Madhur | `hi-IN-MadhurNeural` | Hindi | Patient, clear |
| Maths Teaching (English) | Ryan | `en-US-RyanMultilingualNeural` | English | Friendly, educational |

**Test a voice before committing:**
```bash
python -c "
import asyncio, edge_tts
async def test():
    voice = 'en-US-GuyNeural'
    text = 'The human mind is the most powerful weapon ever created.'
    comm = edge_tts.Communicate(text, voice, rate='-10%', pitch='-2Hz')
    await comm.save('test_voice.mp3')
    print(f'Saved test_voice.mp3 — listen and decide')
asyncio.run(test())
"
```

### 5.3 Script Prompt Customization

Your Gemini prompt determines the personality and style of your content. Customize per channel:

**Dark Psychology Prompt (Example):**
```
You are a dark psychology expert creating YouTube Shorts scripts.
Topic: {topic}

Rules:
- Start with a SHOCKING hook (first line must grab attention in 0.5 seconds)
- Use "you" language — speak directly to the viewer
- Reveal ONE dark psychology concept in 15-25 seconds
- End with a thought-provoking twist that makes viewers want to watch again
- Tone: mysterious, intense, authoritative — like a professor revealing forbidden knowledge
- NO fluff, NO filler, NO "in this video"
- Keep it under 80 words
```

**Personal Finance Prompt (Example):**
```
You are a personal finance expert creating YouTube Shorts scripts for Indian audience.
Topic: {topic}

Rules:
- Start with a relatable hook about money problems Indians face
- Give ONE actionable financial tip in 15-25 seconds
- Use simple Hindi/Hinglish language (mix Hindi + English naturally)
- Include specific numbers (amounts in Rupees, percentages, timelines)
- End with a call to action: "Follow for more money tips"
- NO jargon without explanation
- Keep it under 80 words
```

**Maths Teaching Prompt (Example):**
```
You are a friendly maths teacher creating YouTube Shorts scripts.
Topic: {topic}

Rules:
- Start with a challenge: "Can you solve this in 10 seconds?"
- Show the problem clearly, then reveal the shortcut trick
- Speak step-by-step — each step on its own line
- Use simple language (Hindi + English mix)
- End with: "Follow for more maths tricks!"
- Keep it under 60 words (maths Shorts should be quick)
- Focus on the TRICK, not the theory
```

---

## 6. CONTENT PREPARATION

### 6.1 Build a 30-Day Content Bank

Before launching, prepare at least 30 video topics per channel:

**Template:**
| Day | Shorts Topic 1 | Shorts Topic 2 | Long-form Topic (if applicable) |
|---|---|---|---|
| 1 | _____________ | _____________ | _____________ |
| 2 | _____________ | _____________ | _____________ |
| ... | ... | ... | ... |
| 30 | _____________ | _____________ | _____________ |

### 6.2 Content Ideas by Niche

**Dark Psychology (30 Starter Topics):**
1. "3 signs someone is secretly manipulating you"
2. "The mirroring technique narcissists use"
3. "Why you always feel guilty — it's not your fault"
4. "Dark psychology trick: the Ben Franklin effect"
5. "How your brain is hacked by social media"
6. "5 body language signs someone is lying"
7. "The door-in-the-face technique explained"
8. "Why toxic people always play the victim"
9. "The anchoring bias: how stores trick you into spending more"
10. "Dark triad personality: are you dating one?"
11. "How cult leaders control millions of minds"
12. "The psychology behind revenge"
13. "Why smart people fall for scams"
14. "Gaslighting: the most dangerous manipulation tactic"
15. "The scarcity principle: why 'limited time' works on you"
16. "How to spot a psychopath in 30 seconds"
17. "The halo effect: why attractive people get away with more"
18. "Stockholm syndrome explained in 60 seconds"
19. "Why you trust people who are confident (even when they're wrong)"
20. "The power of silence: why saying nothing is the strongest move"
21. "How dictators used dark psychology to control nations"
22. "The Dunning-Kruger effect: the less you know, the smarter you feel"
23. "Why people stay in toxic relationships — trauma bonding explained"
24. "The foot-in-the-door technique: how small yeses lead to big ones"
25. "Dark psychology of advertising: how brands control your behavior"
26. "The bystander effect: why no one helps in a crowd"
27. "How emotional manipulation works in families"
28. "The mere exposure effect: why familiarity breeds liking"
29. "Machiavellian tactics used in corporate politics"
30. "The psychology of fear: how it controls your decisions"

**Personal Finance Hindi (30 Starter Topics):**
1. "SIP kya hai? 500 Rs se crorepati kaise bane"
2. "FD vs SIP — kisme zyada paisa banta hai?"
3. "Income tax kaise bachaye — 5 legal tricks"
4. "Credit card se paisa kaise kamaye (cashback tricks)"
5. "50-30-20 budgeting rule Hindi mein"
6. "Mutual fund kaise select kare — beginner guide"
7. "Emergency fund kitna hona chahiye?"
8. "PPF vs NPS — retirement ke liye kya best hai?"
9. "Gold invest kare ya nahi? 2026 guide"
10. "5 side hustles jo students kar sakte hain"
11. "Compound interest ka magic — Rs 1000 se Rs 1 Crore"
12. "Stock market kaise start kare — zero se hero"
13. "Demat account kya hai — Groww vs Zerodha"
14. "Health insurance kyu zaroori hai — 25 saal mein bhi"
15. "UPI se cashback kaise kamaye — daily"
16. "Term insurance vs endowment plan — kya lein?"
17. "ELSS mutual fund — tax bhi bachaye, paisa bhi badhaye"
18. "Loan EMI calculator — kitna paisa jaata hai interest mein"
19. "IPO kya hai? Apply kaise kare — step by step"
20. "Budget 2026 — aapke pocket pe kya asar?"
21. "Aadhaar se paisa kaise kamaye (5 tarike)"
22. "Freelancing se paise kaise kamaye India mein"
23. "Inflation kya hai — aapka paisa kyu ghatta ja raha hai"
24. "Sukanya Samriddhi Yojana — beti ke liye best scheme"
25. "Crypto invest kare ya nahi — 2026 truth"
26. "Rs 10,000 salary mein save kaise kare"
27. "First salary pe kya kare — 5 rules"
28. "Real estate vs mutual funds — 2026 mein kya best?"
29. "PF (Provident Fund) kaise check kare — online"
30. "Financial freedom kya hai — 5 steps mein samjho"

**Maths Teaching (30 Starter Topics):**
1. "11 se koi bhi number multiply karo — 2 second mein"
2. "Percentage shortcut — 15% of 240 in 3 seconds"
3. "Quadratic equation solve karo — bina formula ke"
4. "Can you solve: 999 × 999 in 5 seconds?"
5. "Trigonometry trick — Sin 30, 60, 90 yaad karo 10 second mein"
6. "Square root nikalo bina calculator ke"
7. "Algebra basics — 10 minutes mein master karo"
8. "Profit and loss — shortcut formula"
9. "LCM and HCF — easiest method ever"
10. "Time and Distance — train problems trick"
11. "Probability kya hai — dice examples se samjho"
12. "Logarithm basics — 5 minutes mein clear"
13. "Simple vs Compound Interest — formula trick"
14. "Circle area and circumference — visual trick"
15. "Matrices multiplication — step by step"
16. "Integration basics — anti-derivative kya hai?"
17. "AP and GP series — nth term formula trick"
18. "Ratio and Proportion — competitive exam trick"
19. "Geometry theorems — visual proofs"
20. "Number system — even, odd, prime tricks"
21. "Permutation vs Combination — when to use which"
22. "Coordinate geometry — distance formula trick"
23. "Surface area and volume — 3D shapes"
24. "Sets and Venn diagrams — visual explanation"
25. "Calculus differentiation — power rule in 30 seconds"
26. "Average problems — shortcut for competitive exams"
27. "BODMAS vs PEMDAS — which is correct?"
28. "Divisibility rules — check if divisible by 7, 11, 13"
29. "Vedic maths — multiply 2-digit numbers instantly"
30. "Binary numbers — how computers count"

### 6.3 Thumbnail Design Templates

Create a reusable thumbnail template per channel. Consistency = brand recognition.

**Design Principles:**
- **Max 5 words** of text on thumbnail (readable at small sizes)
- **High contrast** — text must pop against background
- **Consistent color scheme** — matches your channel branding
- **Emotion in imagery** — surprised faces, dramatic visuals, bold graphics
- **No small details** — thumbnail is viewed at 120x67 pixels on mobile

**Thumbnail Formulas Per Niche:**

| Niche | Background | Text Style | Example |
|---|---|---|---|
| Dark Psychology | Dark/black gradient | Bold red/white text, ALL CAPS | "THEY'RE LYING" over shadowy face |
| Personal Finance | Clean green/blue gradient | White bold text + money icon | "₹1000 → ₹1 CRORE" |
| Maths Teaching | White/blue whiteboard look | Handwritten-style equation | "99 × 99 = ?" with surprised emoji |
| Devotional | Warm golden/saffron glow | Elegant Devanagari text | Krishna image + "गीता सार" |

---

## 7. FIRST VIDEO: GENERATE, REVIEW, UPLOAD

### 7.1 Generate Your First Video

**For Book-to-Shorts pipeline (Dark Psychology / Finance):**
```bash
cd c:/YoutubeShortsAutomation

# 1. Make sure your source book is in books/ folder
# 2. Run the pipeline
python main.py
```

**For Radha Krishna pipeline:**
```bash
cd c:/YoutubeShortsAutomation/radha_krishna

# 1. Write your script in content/today_script.txt
# 2. Run the pipeline
python main.py
```

### 7.2 Review Before Uploading

**NEVER upload the first video without reviewing.** Check:

- [ ] **Audio quality** — Is the voice clear? Speed okay? Pronunciation correct?
- [ ] **Text/Subtitles** — Are they readable? No cut-off text? Proper line breaks?
- [ ] **Video quality** — Sharp images? Smooth transitions? No glitches?
- [ ] **Script content** — Makes sense? Factually accurate? No copyright issues?
- [ ] **Thumbnail** — Eye-catching? Text readable at small size?
- [ ] **Title** — Contains target keyword? Creates curiosity? Under 60 characters?
- [ ] **Description** — Has affiliate links? Has hashtags? Has call-to-action?
- [ ] **Tags** — Relevant? Mix of broad + specific? Under 500 chars total?

### 7.3 First Upload: Do It Manually

**For your first 5-10 videos, upload manually through YouTube Studio:**

1. Go to **YouTube Studio** → **Create** (top-right) → **Upload videos**
2. Select your video file from `output/final_video.mp4`
3. Copy title, description, tags from `output/seo_data.json`
4. Set visibility: **Public** (or **Schedule** for a specific time)
5. Click **Publish**

**Why manual first?**
- You review every video before it goes live
- YouTube trusts channels that start with manual uploads
- You learn the YouTube Studio interface
- You catch any pipeline issues early

### 7.4 First Upload Timing

| Audience | Best First Upload Time | Why |
|---|---|---|
| India (Hindi content) | 6-8 PM IST (weekday) or 10 AM IST (weekend) | Peak mobile usage |
| USA (English content) | 9 AM EST or 4 PM EST | Commute + after-work scrolling |
| Mixed / Global | 12 PM EST / 10:30 PM IST | Catches both audiences |

---

## 8. UPLOAD SCHEDULE & AUTOMATION

### 8.1 Recommended Upload Schedule

**First 2 Weeks: Manual Uploads (2-3 videos/day)**

| Day | Upload 1 | Upload 2 | Upload 3 (optional) |
|---|---|---|---|
| Mon-Fri | 7 AM IST (Short) | 6 PM IST (Short) | 9 PM IST (Long-form, 2x/week) |
| Sat-Sun | 10 AM IST (Short) | 5 PM IST (Short) | — |

**After 2 Weeks: Switch to Automated Pipeline**

Configure your pipeline to auto-upload with scheduled visibility:
```python
# In your upload config
UPLOAD_SCHEDULE = {
    "short_1": {"time": "09:00", "timezone": "EST"},
    "short_2": {"time": "16:00", "timezone": "EST"},
    "long_form": {"time": "06:00", "timezone": "EST"},
}
VISIBILITY = "private"  # Upload as private, schedule to go public
```

### 8.2 Batch Production Strategy

Instead of producing videos one at a time, batch your work:

**Sunday (Content Day):**
1. Write/generate all scripts for the week (14 Shorts + 3-4 Long-form)
2. Review and edit scripts for quality
3. Generate all voiceovers
4. Generate all videos
5. Create all thumbnails

**Monday-Saturday (Upload Day):**
1. Review today's video (30 seconds)
2. Upload or let automation handle it
3. Reply to comments from yesterday's video (5 minutes)
4. Monitor analytics (5 minutes)

**Total daily time commitment after setup: 15-30 minutes per channel.**

---

## 9. SEO & DISCOVERABILITY OPTIMIZATION

### 9.1 Title Optimization

**Formula:** `[Emotional Hook] + [Target Keyword] + [Curiosity Element]`

**Examples by Niche:**
| Niche | Bad Title | Good Title |
|---|---|---|
| Dark Psychology | "Manipulation Tactics" | "3 Signs Someone Is Secretly Manipulating You" |
| Finance | "SIP Explained" | "₹500 SIP → ₹1 Crore: The Math They Won't Teach You" |
| Maths | "Percentage Formula" | "Calculate 15% of Anything in 2 Seconds (No Calculator)" |
| Devotional | "Gita Teaching" | "कृष्ण ने अर्जुन को बताया जीवन का सबसे बड़ा सच" |

**Title Rules:**
- Keep under **60 characters** (truncated on mobile after that)
- Put the **keyword in first 5 words**
- Use **numbers** when possible (3 signs, 5 tricks, 10 seconds)
- Create **curiosity gap** — promise something the viewer needs to click to discover
- **NO clickbait** — title must match content (YouTube penalizes misleading titles)

### 9.2 Description Optimization

**Structure Every Description Like This:**

```
[Line 1: Hook — repeat the value proposition from title]

[Line 2-3: Brief summary of what viewer will learn]

[Line 4: Call to action — Subscribe + Bell icon]

---

[Timestamps — for long-form only]
0:00 Introduction
1:30 Key Concept 1
4:00 Key Concept 2
...

---

[Affiliate Links Section]
📚 Books mentioned in this video:
• [Book Name] — [affiliate link]
• [Book Name] — [affiliate link]

💰 Tools I recommend:
• [Tool] — [affiliate link]

---

[Hashtags — 3 to 5]
#DarkPsychology #Manipulation #HumanBehavior

---

Disclaimer: [If needed — finance/education/affiliate disclaimers]

© [Channel Name] 2026
```

### 9.3 Tags Strategy

**Per-Video Tag Formula (15-20 tags):**
1. **3-5 Exact match keywords** — "dark psychology", "manipulation tactics"
2. **3-5 Related keywords** — "body language", "human behavior", "cognitive biases"
3. **3-5 Long-tail keywords** — "how to spot a manipulator", "signs someone is lying to you"
4. **2-3 Channel/brand tags** — your channel name, niche identifier
5. **2-3 Trending tags** — use your pytrends fetcher to find current trending terms

### 9.4 Hashtags (Different from Tags)

Add 3-5 hashtags in the description — YouTube shows the first 3 above the title:

| Niche | Recommended Hashtags |
|---|---|
| Dark Psychology | #DarkPsychology #Manipulation #Psychology #HumanBehavior #MindGames |
| Personal Finance | #PersonalFinance #MoneyTips #SIP #MutualFunds #FinancialFreedom |
| Maths Teaching | #MathsTricks #JEEPrep #BoardExam #MentalMath #StudyTips |
| Devotional | #RadhaKrishna #BhagavadGita #GeetaSaar #JaiShreeKrishna #Spirituality |

---

## 10. MONETIZATION SETUP

### 10.1 YouTube Partner Program Requirements

| Requirement | Target | How to Track |
|---|---|---|
| Subscribers | 1,000 | YouTube Studio → Dashboard |
| Watch Hours (12 months) | 4,000 hours | YouTube Studio → Analytics → Watch time |
| OR Shorts Views (90 days) | 10 Million | YouTube Studio → Analytics → Shorts |
| Community Guidelines Strikes | 0 | YouTube Studio → Channel → Settings |
| 2-Step Verification | Enabled | Google Account Settings |

### 10.2 Monetization Timeline (Realistic)

| Channel Type | Expected Time to 1K Subs | Expected Time to 4K Watch Hours |
|---|---|---|
| Dark Psychology (Shorts + Long) | 2-4 months | 3-5 months |
| Personal Finance (Hindi) | 3-5 months | 4-6 months |
| Maths Teaching (Shorts + Long) | 2-4 months (exam season faster) | 3-5 months |
| Radha Krishna (Devotional) | 3-6 months | 4-8 months |

### 10.3 AdSense Setup (When Eligible)

1. YouTube Studio → **Monetization** → **Apply**
2. Sign the YouTube Partner Program terms
3. Create or connect **Google AdSense** account
4. Fill in tax information:
   - Indian residents: **PAN card** required
   - Select **Individual** account type
   - For US-targeted channels: Fill **W-8BEN** form (tax treaty benefits)
5. Set payment method:
   - **Bank transfer** (direct to Indian bank account — minimum payout $100/₹8,000)
   - **Wire transfer** (for US AdSense accounts)
6. Wait for review: **1-4 weeks** typically

### 10.4 Affiliate Setup (Start Day 1 — Don't Wait for YPP)

| Program | Signup Link | Requirements | Commission |
|---|---|---|---|
| Amazon Associates (India) | affiliate-program.amazon.in | None | 1-10% |
| Amazon Associates (US) | affiliate-program.amazon.com | Need US tax info | 1-10% |
| Groww Referral | In-app | Active account | ₹200/signup |
| Zerodha Referral | In-app | Active account | ₹200-300/signup |
| Udemy Affiliates | udemy.com/affiliate | Website/YouTube channel | 15-25% |
| Audible | audible.com/affiliate | None | $5-15/trial |

---

## 11. GROWTH PLAYBOOK (FIRST 30 DAYS)

### Day 1-7: Launch Week
- [ ] Upload 2-3 Shorts per day (total 14-21 Shorts by end of week)
- [ ] Upload 1-2 Long-form videos
- [ ] Share videos on WhatsApp, Instagram, Twitter (personal networks)
- [ ] Reply to EVERY comment (builds engagement signal)
- [ ] Post a community poll: "What topic should I cover next?"
- [ ] Join 3-5 Facebook/Reddit groups related to your niche — share videos (don't spam)

### Day 8-14: Find Your Winners
- [ ] Check analytics: Which Shorts got the most views? Which titles had highest CTR?
- [ ] Make 3 more Shorts on the SAME topic as your best performer
- [ ] Experiment with different hook styles (question, statement, challenge)
- [ ] Upload your best Short on Instagram Reels too (cross-platform growth)
- [ ] Start a playlist — group your content by sub-topic

### Day 15-21: Double Down
- [ ] You should have 30-40+ Shorts by now
- [ ] Identify your top 3 video topics — create a "series" around each
- [ ] Start adding affiliate links to ALL descriptions
- [ ] Create and pin a "start here" comment on your most popular video
- [ ] Cross-promote: mention your other channels in end screens

### Day 22-30: Systematize
- [ ] Batch-produce next week's content in one sitting
- [ ] Set up automated pipeline if not already running
- [ ] Review monthly analytics: best day, best time, best topic
- [ ] Plan Month 2 content calendar based on data
- [ ] Total target by Day 30: **60-90 Shorts + 8-12 Long-form**

### Growth Benchmarks (What to Expect)

| Metric | Day 7 | Day 14 | Day 30 | Day 60 | Day 90 |
|---|---|---|---|---|---|
| Total Videos | 15-20 | 35-45 | 70-100 | 150-200 | 250-300 |
| Subscribers | 5-50 | 20-200 | 50-500 | 200-2,000 | 500-5,000 |
| Daily Views | 50-500 | 200-2,000 | 500-5,000 | 2,000-20,000 | 5,000-50,000 |
| Total Views | 200-2,000 | 2,000-15,000 | 10,000-100,000 | 50,000-500,000 | 200,000-2,000,000 |

> These are ranges, not guarantees. Some channels blow up in week 2, others take 3 months. The constant: **channels that upload daily grow faster than those that don't.**

---

## 12. SAFETY & COMPLIANCE CHECKLIST

### Before Every Upload
- [ ] No copyrighted music (use royalty-free only)
- [ ] No copyrighted images (use your own, royalty-free, or AI-generated)
- [ ] AI content disclosed if using realistic AI-generated faces/voices
- [ ] Title matches actual content (no misleading clickbait)
- [ ] No profanity in title, description, or first 30 seconds
- [ ] Affiliate links have disclosure ("contains affiliate links")
- [ ] Finance content has disclaimer ("not financial advice")

### Monthly Channel Health Check
- [ ] Check YouTube Studio for any policy warnings or strikes
- [ ] Verify all videos are still monetized (check yellow $ icons)
- [ ] Review comments for any community guideline issues
- [ ] Ensure upload frequency hasn't dropped (no gaps > 3 days)
- [ ] Verify API quota usage isn't approaching limits
- [ ] Check that OAuth tokens are still valid (refresh if needed)

### Things That Will Get You Banned
1. Uploading the SAME video to multiple channels
2. Using bots for fake views/subscribers
3. Copyright strikes (3 strikes = channel terminated)
4. Spam/misleading content repeatedly
5. Buying subscribers or views
6. Reusing someone else's content without transformation
7. Harassing or bullying other creators/viewers

---

## 13. TROUBLESHOOTING

### Common Issues & Fixes

| Problem | Cause | Solution |
|---|---|---|
| "credentials.json not found" | File missing or wrong path | Download from Google Cloud Console, rename, place in channel folder |
| "Token expired" | OAuth token expired | Delete `token_XX.json`, re-run to re-authenticate |
| "quotaExceeded" | Hit daily API limit | Wait until midnight PT, or use a different Cloud project |
| "uploadLimitExceeded" | Too many uploads/day | New channels have ~15-20 upload/day limit. Reduce count. |
| "Video processing failed" | FFmpeg issue | Check FFmpeg is installed: `ffmpeg -version`. Check video codec. |
| "invalidTags" | Special chars in tags | Pipeline auto-retries 3 times. If persists, check tag content. |
| Low views after 48 hours | Poor hook / title / thumbnail | A/B test: change thumbnail → wait 48 hrs → compare CTR |
| 0 subscribers after 1 week | Normal for new channels | Keep uploading. First 100 subs are always the slowest. |
| Video stuck on "Processing" | Large file or YouTube servers busy | Wait 1-2 hours. If persists, re-upload. |
| "Made for kids" wrongly set | YouTube auto-detected kids content | Go to video settings → Audience → Set "Not made for kids" |
| Edge TTS voice sounds wrong | Wrong voice code | See Voice Selection Guide (Section 5.2). Test before batch-producing. |

### When to Panic vs When to Wait

| Situation | Action |
|---|---|
| Video gets 0 views for 24 hours | WAIT — YouTube needs 24-48 hrs to push Shorts |
| Video gets copyright claim | CHECK — if it's music, swap it. If it's content, dispute if you're in the right |
| Channel gets community strike | APPEAL immediately (40% success rate) |
| Subscriber count drops | WAIT — YouTube purges bot/inactive accounts periodically |
| CPM drops suddenly | WAIT — Q1 CPM is always lower than Q4. Seasonal fluctuation. |
| YouTube removes monetization | APPEAL + FIX — review which policy was violated, fix it, appeal |

---

## 14. CHANNEL LAUNCH CHECKLIST

### Pre-Launch (Complete Before First Upload)
- [ ] Niche selected and validated (Section 1)
- [ ] Google account created (Section 2)
- [ ] YouTube channel created with name and handle (Section 2)
- [ ] Profile picture uploaded (800x800)
- [ ] Banner image uploaded (2560x1440)
- [ ] Channel description written with keywords
- [ ] Channel keywords added (15-25)
- [ ] Upload defaults configured (language, category, comments)
- [ ] Channel country set correctly
- [ ] Phone verification completed (for custom thumbnails)
- [ ] Google Cloud project created
- [ ] YouTube Data API v3 enabled
- [ ] OAuth credentials created and downloaded
- [ ] First-time browser authentication completed
- [ ] Pipeline configured for this channel
- [ ] TTS voice selected and tested
- [ ] Script prompt customized for this niche
- [ ] Thumbnail template created
- [ ] 30-day content calendar prepared
- [ ] Source books/materials placed in books/ folder
- [ ] Background music placed in music/ folder (royalty-free)
- [ ] Affiliate accounts set up

### Launch Day
- [ ] First video generated and REVIEWED
- [ ] Thumbnail created and looks good at small size
- [ ] Title contains target keyword + curiosity element
- [ ] Description has proper structure (hook + CTA + links + hashtags)
- [ ] Tags added (15-20 relevant tags)
- [ ] Video uploaded (manually for first 5-10 videos)
- [ ] Shared on personal social media
- [ ] Channel link saved and bookmarked

### Post-Launch (Daily Routine)
- [ ] Upload 2-3 Shorts per day
- [ ] Reply to all comments
- [ ] Check analytics for 5 minutes
- [ ] Note best-performing topics

### Post-Launch (Weekly Routine)
- [ ] Review weekly analytics (CTR, AVD, top videos)
- [ ] Plan next week's content based on data
- [ ] Upload 1-2 long-form videos
- [ ] Post 1 community poll/question
- [ ] Cross-promote with other channels

---

> **Remember:** The best channel is the one that gets launched. Don't over-plan. Follow this guide step by step, and you'll have a fully functioning, automated YouTube channel within a few hours.

---

> **Related Documents:**  
> - [youtube_setup_guide.md](youtube_setup_guide.md) — Detailed YouTube API setup  
> - [new_account_setup_guide.md](new_account_setup_guide.md) — USA-based account creation  
> - [MILLIONAIRE_BLUEPRINT_2026.md](MILLIONAIRE_BLUEPRINT_2026.md) — Full multi-channel strategy  
> - [radha_krishna/README.md](radha_krishna/README.md) — Devotional channel pipeline docs  
> - [pipeline_commands.md](pipeline_commands.md) — Quick pipeline command reference  

---

> **Document Owner:** Keshav Mittal  
> **Created:** April 21, 2026  
> **Last Updated:** April 21, 2026
