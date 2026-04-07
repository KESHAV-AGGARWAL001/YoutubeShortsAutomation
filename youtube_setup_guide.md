# YouTube API — Complete Setup Guide (From Scratch)

> **Goal:** Set up automated YouTube video uploads using YouTube Data API v3
> **Time required:** ~20 minutes
> **Cost:** Free (10,000 quota units/day — enough for ~5-6 uploads/day)

---

## Step 1 — Create a Google Account

1. Go to **https://accounts.google.com/signup**
2. Create an account (or use your existing Google account)
3. Make sure you can log in to **https://www.youtube.com** with this account

---

## Step 2 — Create a YouTube Channel

1. Go to **https://www.youtube.com**
2. Click your profile icon (top-right) → **Create a channel**
3. Channel name: your brand name (e.g. **Next Level Mind**)
4. Click **Create Channel**
5. Go to **YouTube Studio** → **Customization** → **Basic Info**
6. Add your channel description, keywords, and links

> Your channel is now ready for uploads.

---

## Step 3 — Create a Google Cloud Project

1. Go to **https://console.cloud.google.com**
2. Log in with the same Google account from Step 1
3. Click the project dropdown (top-left, next to "Google Cloud") → **New Project**
4. Project name: `YouTubeBot` (or anything you want)
5. Click **Create**
6. Wait for the project to be created (10-15 seconds)
7. Make sure the new project is selected in the top-left dropdown

---

## Step 4 — Enable YouTube Data API v3

1. In Google Cloud Console → left sidebar → **APIs & Services** → **Library**
2. Search for **YouTube Data API v3**
3. Click on it → Click **Enable**
4. Wait for it to enable (5-10 seconds)

---

## Step 5 — Configure OAuth Consent Screen

> This is required before you can create credentials.

1. Left sidebar → **APIs & Services** → **OAuth consent screen**
2. Click **Get Started** or **Configure Consent Screen**
3. App name: `YouTubeBot`
4. User support email: your email
5. Developer contact email: your email
6. Click **Save and Continue**

### Add Scopes:

7. Click **Add or Remove Scopes**
8. Search for and add these scopes:
   - `https://www.googleapis.com/auth/youtube`
   - `https://www.googleapis.com/auth/youtube.force-ssl`
   - `https://www.googleapis.com/auth/youtube.upload`
9. Click **Update** → **Save and Continue**

### Add Test Users:

10. Click **Add Users**
11. Add your Gmail address (the one linked to your YouTube channel)
12. Click **Save and Continue**

> **IMPORTANT:** While the app is in "Testing" mode, only the test users you add can authenticate. This is fine for personal automation.

---

## Step 6 — Create OAuth2 Credentials

1. Left sidebar → **APIs & Services** → **Credentials**
2. Click **+ Create Credentials** → **OAuth client ID**
3. Application type: **Desktop app**
4. Name: `YouTubeBot Desktop`
5. Click **Create**
6. A popup will show your **Client ID** and **Client Secret**
7. Click **Download JSON** — this downloads a file like `client_secret_XXXXX.json`
8. **Rename** this file to `credentials.json`
9. **Move** it to your project root folder (e.g. `D:\YouTubeBot\credentials.json`)

```
Your project folder should look like:
D:\YouTubeBot\
├── credentials.json    ← the file you just downloaded and renamed
├── main.py
├── scripts/
│   ├── 02_write_script.py
│   ├── 03_voiceover.py
│   ├── ...
│   └── 07_upload.py
├── .env
└── ...
```

---

## Step 7 — First-Time Authentication

The first time you run the upload script, it will open a browser window for you to log in.

1. Run the upload script:

```powershell
cd D:\YouTubeBot
python scripts/07_upload.py
```

2. A browser window will open → log in with your Google account
3. You'll see a warning: **"Google hasn't verified this app"**
   - Click **Advanced** → **Go to YouTubeBot (unsafe)**
   - This is normal for personal/test apps
4. Click **Allow** for all permissions
5. Click **Allow** again to confirm
6. The browser will say **"The authentication flow has completed"**
7. Go back to your terminal — the upload should continue

> After first login, a `token.json` file is saved in `output/token.json`. Future uploads will use this token automatically — no browser login needed.

---

## Step 8 — Set Environment Variables

Open your `.env` file (in your project root) and add:

```
GEMINI_API_KEY=your_gemini_api_key_here
YOUTUBE_CLIENT_SECRET=credentials.json
```

> `YOUTUBE_CLIENT_SECRET` points to your credentials file. If you placed it in the project root and named it `credentials.json`, the default value works automatically.

---

## Step 9 — Verify Everything Works

Run this test to make sure YouTube API is working:

```powershell
cd D:\YouTubeBot
python -c "
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

creds = Credentials.from_authorized_user_file('output/token.json')
youtube = build('youtube', 'v3', credentials=creds)

# Get your channel info
response = youtube.channels().list(part='snippet,statistics', mine=True).execute()
channel = response['items'][0]

print(f'Channel: {channel[\"snippet\"][\"title\"]}')
print(f'Subscribers: {channel[\"statistics\"][\"subscriberCount\"]}')
print(f'Videos: {channel[\"statistics\"][\"videoCount\"]}')
print(f'Views: {channel[\"statistics\"][\"viewCount\"]}')
print()
print('SETUP COMPLETE - Ready for automation!')
"
```

If you see your channel name and stats — **you're done!**

---

## Step 10 — Verify Channel for Thumbnails (Optional)

Custom thumbnails require channel verification:

1. Go to **https://www.youtube.com/verify**
2. Verify with your phone number
3. Once verified, the upload script will automatically upload thumbnails

> Without verification, videos upload fine — only custom thumbnails are skipped.

---

## Checklist

Use this to track your progress:

- [ ] Step 1: Google account created/logged in
- [ ] Step 2: YouTube channel created
- [ ] Step 3: Google Cloud project created
- [ ] Step 4: YouTube Data API v3 enabled
- [ ] Step 5: OAuth consent screen configured with scopes + test users
- [ ] Step 6: OAuth2 credentials created + `credentials.json` saved to project root
- [ ] Step 7: First-time browser authentication completed + `token.json` generated
- [ ] Step 8: `.env` file has `YOUTUBE_CLIENT_SECRET=credentials.json`
- [ ] Step 9: Verification test shows channel name and stats
- [ ] Step 10: (Optional) Channel verified for custom thumbnails

---

## Quota Limits

YouTube Data API v3 has a daily quota of **10,000 units**:

| Operation | Cost | How many per day |
|-----------|------|-----------------|
| Video upload | 1,600 units | ~6 uploads/day |
| Thumbnail set | 50 units | ~200/day |
| Caption upload | 400 units | ~25/day |
| Playlist insert | 50 units | ~200/day |

**Your daily pipeline:**
- 2 Shorts + 1 Long-form = 3 uploads = 4,800 units (upload)
- 3 thumbnails = 150 units
- 3 caption uploads = 1,200 units
- **Total: ~6,150 units/day** (well within the 10,000 limit)

> If you need more quota, go to **APIs & Services** → **YouTube Data API v3** → **Quotas** → **Request increase**.

---

## Common Errors & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| "credentials.json not found" | File missing or wrong path | Download from Google Cloud Console → Credentials → Download JSON → rename to `credentials.json` |
| "Access blocked: app not verified" | OAuth consent screen not set up | Complete Step 5 — add scopes and test users |
| "The caller does not have permission" | Wrong Google account or scopes | Delete `output/token.json`, re-run upload to re-authenticate with correct account |
| "Token has been expired or revoked" | Token expired (after ~7 days of no use) | Delete `output/token.json`, re-run upload to get a fresh token |
| "quotaExceeded" | Daily API quota used up | Wait until midnight Pacific Time (quota resets) or request increase |
| "invalidTags" | Tags contain # or special characters | Already fixed in the pipeline — 3-attempt retry strips invalid tags automatically |
| "uploadLimitExceeded" | Too many uploads in 24 hours | YouTube limits new channels to ~15-20 uploads/day — reduce upload count |
| "video too long" | Video exceeds 15 minutes | Verify your account at youtube.com/verify to unlock 12-hour uploads |
| "insufficientPermissions" | Missing YouTube scope | Delete `output/token.json`, check Step 5 scopes, re-authenticate |
| Browser doesn't open for auth | Running on a server/headless | Use `--console` flag or set up auth on a local machine first, then copy `token.json` |

---

## Token Refresh

The OAuth2 token (`output/token.json`) auto-refreshes when it expires — the upload script handles this automatically:

```python
if creds and creds.expired and creds.refresh_token:
    creds.refresh(Request())
```

You only need to re-authenticate manually if:
- You delete `output/token.json`
- You revoke access from your Google account settings
- The refresh token itself expires (~6 months of inactivity)

---

## Running the Pipelines

### Shorts (2 videos/day):
```powershell
cd D:\YouTubeBot
python main.py
```

### Long-Form (1 video/day):
```powershell
cd D:\YouTubeBot
python long_form_main.py
```

### Test Long-Form (no upload):
```powershell
cd D:\YouTubeBot
python test_long_form.py
```

### Manual Upload (if pipeline upload failed):
```powershell
cd D:\YouTubeBot
python scripts/07_upload.py          # Shorts
python scripts/long_07_upload.py     # Long-form
```

---

## Project Structure

```
D:\YouTubeBot\
├── credentials.json              ← YouTube OAuth2 credentials (Step 6)
├── .env                          ← API keys and config
├── main.py                       ← Shorts pipeline runner (2/day)
├── long_form_main.py             ← Long-form pipeline runner (1/day)
├── test_long_form.py             ← Long-form test (no upload)
├── books/
│   ├── your_book.pdf             ← Source book for content
│   ├── progress.json             ← Shorts page tracker
│   └── long_progress.json        ← Long-form page tracker
├── scripts/
│   ├── 02_write_script.py        ← Shorts script generator (Gemini)
│   ├── 03_voiceover.py           ← Voiceover (Edge TTS)
│   ├── 04_get_footage.py         ← Background setup
│   ├── 05_make_video.py          ← Shorts video assembly (9:16)
│   ├── 06_thumbnail.py           ← Shorts thumbnail
│   ├── 07_upload.py              ← Shorts YouTube upload
│   ├── long_02_write_script.py   ← Long-form script generator
│   ├── long_05_make_video.py     ← Long-form video assembly (16:9)
│   ├── long_06_thumbnail.py      ← Long-form thumbnail
│   └── long_07_upload.py         ← Long-form YouTube upload
├── music/
│   └── background.mp3            ← Background music track
├── output/                       ← Generated files (auto-cleaned)
│   ├── token.json                ← YouTube auth token (auto-generated)
│   ├── final_video.mp4           ← Latest video
│   ├── seo_data.json             ← Title, description, tags
│   └── ...
└── archive/                      ← Backed up videos
```

---

## What Happens After Setup

Once setup is complete, your daily automation runs:

```
main.py runs daily:
  Video 1 → YouTube Short (9 AM EST) — with subtitles
  Video 2 → YouTube Short (4 PM EST) — with subtitles

long_form_main.py runs daily:
  Video 3 → YouTube Long-form (6 AM EST) — 7-8 min, 16:9, centered text
```

All videos include:
- AI-generated scripts from your book (Gemini)
- Professional voiceover (Edge TTS)
- Centered subtitles on black background
- SEO-optimized title, description, tags
- Amazon Affiliate links in description
- SRT captions uploaded for search indexing
- Dark cinematic thumbnails
