# New Google Account + YouTube Channel — Setup Guide

> **Goal:** Create a fresh Google account and YouTube channel for automated content uploads
> **Time required:** ~10 minutes
> **Cost:** Free

---

## Step 1 — Create a New Google Account

1. Open an **incognito/private browser window** (important — prevents auto-login to your existing account)
2. Go to **https://accounts.google.com/signup**
3. Fill in:
   - First name: your name or brand name
   - Last name: (can be anything)
4. Click **Next**
5. Set your **birthday** and **gender**
6. Click **Next**

### Choose Your Email Address

7. Select **"Create your own Gmail address"**
8. Pick a professional-looking email:
   - Good: `nextlevelmindofficial@gmail.com`, `nextlevelmind2026@gmail.com`
   - Avoid: random numbers, underscores, anything spammy
9. Click **Next**

### Set Password

10. Create a strong password (save it somewhere safe)
11. Click **Next**

### Recovery Info (Optional but Recommended)

12. Add a recovery phone number — helps if you get locked out
13. Add a recovery email (use your existing email)
14. Click **Next**
15. Accept Google's Terms of Service → **I agree**

> Your Google account is now created.

---

## Step 2 — Set Up 2-Step Verification (Important)

Protects your account from being hacked/stolen:

1. Go to **https://myaccount.google.com/security**
2. Click **2-Step Verification** → **Get Started**
3. Enter your phone number → Google sends a code
4. Enter the code → Click **Turn On**

> This prevents someone from stealing your channel.

---

## Step 3 — Create a YouTube Channel

1. Go to **https://www.youtube.com** (still in the same browser, logged into new account)
2. Click your **profile icon** (top-right corner)
3. Click **"Create a channel"**
4. Channel name: **Next Level Mind** (or your brand name)
5. Handle: `@NextLevelMind` (or similar — must be unique)
6. Click **Create Channel**

> Your YouTube channel is now live.

---

## Step 4 — Channel Customization

### Basic Info

1. Go to **YouTube Studio** → https://studio.youtube.com
2. Click **Customization** (left sidebar) → **Basic Info**
3. Set:
   - **Channel name**: Next Level Mind
   - **Handle**: @NextLevelMind
   - **Description**:
     ```
     Level up your mindset every single day.

     We break down the most powerful lessons from psychology, 
     philosophy, and real-world success into short, hard-hitting 
     videos that actually change how you think.

     New videos daily — subscribe and turn on notifications.

     Topics: motivation, self-improvement, discipline, mindset, 
     stoicism, productivity, success habits, mental strength
     ```
   - **Channel URL**: auto-generated (custom URL available after 100 subscribers)
   - **Links**: Add your Instagram, website, etc.

### Keywords (Add Words and Phrases)

4. Scroll to **Keywords** section
5. Paste these:
   ```
   motivation, self improvement, mindset, personal growth, personal development, motivational quotes, life advice, success mindset, mental strength, discipline, productivity, self help, inspirational quotes, daily motivation, growth mindset, dark motivation, sigma mindset, stoicism, psychology facts, life lessons, self worth, wisdom, emotional intelligence, books to read, entrepreneur mindset, hustle, financial freedom, prove them wrong
   ```

### Branding

6. Click **Branding** tab
7. Upload:
   - **Profile picture**: Your channel logo (800x800 recommended)
   - **Banner image**: Channel art (2560x1440 recommended)
   - **Video watermark**: Subscribe button overlay (150x150 PNG)

### Layout

8. Click **Layout** tab
9. Set:
   - **Channel trailer**: leave empty for now (add after 5+ videos)
   - **Featured sections**: "Short videos", "Popular videos"

---

## Step 5 — Channel Settings

1. In YouTube Studio → **Settings** (bottom-left gear icon)

### Upload Defaults

2. Click **Upload defaults** → **Basic info**
   - Visibility: **Private** (your pipeline sets this + schedule)
   - Category: **Education**
   - Language: **English**

3. Click **Upload defaults** → **Advanced settings**
   - License: **Standard YouTube License**
   - Comments: **Hold potentially inappropriate comments for review**

### Channel Settings

4. Click **Channel** → **Basic info**
   - Country: **United States** (or your target audience country)

5. Click **Channel** → **Feature eligibility**
   - Check what features are available (custom thumbnails need phone verification)

---

## Step 6 — Verify Your Channel (Phone Verification)

Required for custom thumbnails and longer uploads:

1. Go to **https://www.youtube.com/verify**
2. Choose verification method: **Text message** or **Phone call**
3. Enter your phone number
4. Enter the verification code
5. Done — you now have access to:
   - Custom thumbnails
   - Videos longer than 15 minutes
   - Live streaming
   - External links in descriptions

---

## Step 7 — Set Up YouTube API (For Automated Uploads)

Follow the full guide in **youtube_setup_guide.md** — specifically:

1. Create Google Cloud Project (Step 3)
2. Enable YouTube Data API v3 (Step 4)
3. Configure OAuth Consent Screen (Step 5)
4. Create OAuth2 Credentials (Step 6)
5. First-time Authentication (Step 7)

> Use the SAME new Google account for everything — Cloud Console, YouTube, and API.

---

## Step 8 — Safety Rules for the New Channel

These rules will prevent your channel from getting removed again:

### Content Rules
- [ ] Stock video backgrounds (NOT pure black) — already configured in pipeline
- [ ] AI adds original insights and commentary — already configured in prompts
- [ ] Never copy/quote books directly — Gemini prompt enforces this
- [ ] Mix content angles — emotional, advice, storytelling, contrarian

### Upload Rules
- [ ] First 2 weeks: upload **manually** (builds trust with YouTube)
- [ ] After 2 weeks: switch to API uploads, max **2 per day**
- [ ] Space uploads **8-12 hours apart** minimum
- [ ] Never upload more than 3 videos in a single day

### Metadata Rules
- [ ] Keep tags under 15 per video (not 30+)
- [ ] Natural titles — no keyword stuffing
- [ ] No affiliate links in descriptions until you have 100+ subscribers
- [ ] Descriptions should look hand-written, not template-generated

### Account Rules
- [ ] Use 2-Step Verification (Step 2 above)
- [ ] Don't create multiple channels on the same account
- [ ] Don't use VPN while uploading — IP consistency matters
- [ ] Check YouTube Studio notifications weekly for policy warnings

---

## Checklist

- [ ] Step 1: New Google account created
- [ ] Step 2: 2-Step Verification enabled
- [ ] Step 3: YouTube channel created with brand name
- [ ] Step 4: Channel customized (description, keywords, branding)
- [ ] Step 5: Upload defaults configured
- [ ] Step 6: Phone verification completed
- [ ] Step 7: YouTube API set up (credentials.json + token.json)
- [ ] Step 8: Safety rules reviewed and understood

---

## What's Next

Once this setup is complete:

1. **First 2 weeks** — upload manually:
   - Run `python main.py` to generate video
   - Find `output/final_video.mp4` and `output/seo_data.json`
   - Upload manually through YouTube Studio
   - Copy title, description, tags from `seo_data.json`

2. **After 2 weeks** — switch to automated uploads:
   - Run full pipeline: `python main.py` (auto-uploads)
   - Monitor YouTube Studio for any policy warnings

3. **Instagram** — upload the same content:
   - Find `output/video_for_reel.mp4` after each pipeline run
   - Upload manually to Instagram Reels with hashtags

---

## Important Notes

- **Do NOT** link this new channel to your old banned Google account in any way
- **Do NOT** use the same browser profile — use incognito or a new Chrome profile
- **Do NOT** reuse old video files from the banned channel
- If your old account was terminated, YouTube may flag new accounts created from the same IP — consider using mobile data for initial account creation
