# Instagram Reels API — Complete Setup Guide (From Scratch)

> **Goal:** Set up automated Instagram Reel uploads using Meta's Graph API
> **Time required:** ~30 minutes
> **Cost:** Free

---

## Step 1 — Create a New Facebook Account

1. Go to **https://www.facebook.com/r.php**
2. Use your **real name** (Meta bans fake names — you'll lose API access)
3. Use an email you have access to (for verification)
4. Verify your email when the code arrives
5. **Important:** Add a profile photo and complete basic setup — brand new empty accounts get flagged by Meta and can't access Developer tools

---

## Step 2 — Create a Facebook Page

1. Once logged in, go to **https://www.facebook.com/pages/create**
2. Page name: your brand name (e.g. **IronMindset**)
3. Category: **Motivational Speaker** or **Personal Blog**
4. Click **Create Page**

> You don't need to post anything on this page. It just needs to exist for the API to work.

---

## Step 3 — Switch Instagram to Business/Creator + Link to Facebook

1. Open **Instagram app** on your phone
2. Go to **Settings** → **Account type and tools**
3. Switch to **Creator** or **Business** account (if not already)
4. It will ask you to **connect a Facebook Page** → select the page from Step 2
5. If it doesn't ask automatically:
   - Go to **Settings** → **Business** → **Connected accounts** → **Facebook**
   - Select your Facebook Page

### How to verify the link:
- On Facebook: Go to your Page → **Settings** → **Linked Accounts** → you should see your Instagram username

---

## Step 4 — Register as a Meta Developer

1. Go to **https://developers.facebook.com**
2. Click **Get Started**
3. Log in with the Facebook account from Step 1
4. Accept the Meta Developer Terms
5. Verify your identity (phone number or email)
6. You're now a registered Meta Developer

---

## Step 5 — Create a Meta App

1. Click **My Apps** (top-right corner) → **Create App**
2. Use case → select **Other** → click **Next**
3. App type → select **Business** → click **Next**
4. Fill in:
   - App name: `ReelBot` (or anything you want)
   - Contact email: your email
5. Click **Create App**
6. You'll land on the **App Dashboard**

---

## Step 6 — Add Instagram Graph API to Your App

1. On the App Dashboard → left sidebar → click **Add Product**
2. Find **Instagram Graph API** in the product list
3. Click **Set Up**
4. It now appears in your left sidebar

---

## Step 7 — Generate Access Tokens

> **IMPORTANT:** Steps 7a and 7b must be done within 5 minutes.
> The short-lived token expires in 1 hour, so don't wait.

### Step 7a — Get a Short-Lived Token

1. Go to **https://developers.facebook.com/tools/explorer**
2. Top-right dropdown → select your app (`ReelBot`)
3. Click **Add a Permission** and add these one by one:
   - `instagram_basic`
   - `instagram_content_publish`
   - `pages_show_list`
   - `pages_read_engagement`
4. Click **Generate Access Token**
5. A popup will appear → **Authorize everything** → click **Done**
6. Copy the token shown in the text box immediately

### Step 7b — Exchange for a Long-Lived Token (60 days)

1. Go to App Dashboard → **Settings** → **Basic**
2. Note your **App ID**
3. Click **Show** next to **App Secret** → copy it
4. Open **PowerShell** and run:

```powershell
$APP_ID = "paste_your_app_id_here"
$APP_SECRET = "paste_your_app_secret_here"
$SHORT_TOKEN = "paste_the_token_from_step_7a_here"

$url = "https://graph.facebook.com/v21.0/oauth/access_token?grant_type=fb_exchange_token&client_id=$APP_ID&client_secret=$APP_SECRET&fb_exchange_token=$SHORT_TOKEN"

$result = Invoke-RestMethod -Uri $url
Write-Host "`nLONG-LIVED TOKEN (save this):`n" $result.access_token
```

5. Copy the long-lived token it prints — **this lasts 60 days**
6. Save it somewhere safe (you'll need it in Step 9)

### If you get an error:
- **"Invalid OAuth access token"** → your short-lived token expired. Go back to Step 7a and generate a new one, then do 7b immediately.
- **"Error validating application"** → double-check your App ID and App Secret.

---

## Step 8 — Get Your Instagram Business Account ID

### Step 8a — Get your Facebook Page ID

Run in PowerShell:

```powershell
$TOKEN = "paste_your_long_lived_token_here"

$pages = Invoke-RestMethod -Uri "https://graph.facebook.com/v21.0/me/accounts?access_token=$TOKEN"
$pages.data | ForEach-Object { Write-Host "Page:" $_.name " | ID:" $_.id }
```

This will print something like:
```
Page: IronMindset | ID: 123456789012345
```

Copy the **ID** number.

### Step 8b — Get your Instagram Business Account ID

Run in PowerShell (replace `PAGE_ID` with the ID from 8a):

```powershell
$TOKEN = "paste_your_long_lived_token_here"
$PAGE_ID = "paste_page_id_from_step_8a"

$ig = Invoke-RestMethod -Uri "https://graph.facebook.com/v21.0/$PAGE_ID`?fields=instagram_business_account&access_token=$TOKEN"
Write-Host "`nINSTAGRAM BUSINESS ACCOUNT ID:" $ig.instagram_business_account.id
```

This will print something like:
```
INSTAGRAM BUSINESS ACCOUNT ID: 17841400000000000
```

Copy this ID.

---

## Step 9 — Save Credentials to .env

Open your `.env` file (in your project root: `D:\YouTubeBot\.env`) and add these two lines:

```
INSTAGRAM_TOKEN=your_long_lived_token_from_step_7b
INSTAGRAM_ID=your_instagram_id_from_step_8b
```

---

## Step 10 — Verify Everything Works

Run this final test in PowerShell:

```powershell
$TOKEN = "paste_your_long_lived_token"
$IG_ID = "paste_your_instagram_id"

$r = Invoke-RestMethod -Uri "https://graph.facebook.com/v21.0/$IG_ID`?fields=username,media_count&access_token=$TOKEN"
Write-Host "`nUsername:" $r.username
Write-Host "Total Posts:" $r.media_count
Write-Host "`nSETUP COMPLETE - Ready for automation!"
```

If you see your Instagram username and post count — **you're done!**

---

## Checklist

Use this to track your progress:

- [ ] Step 1: Facebook account created
- [ ] Step 2: Facebook Page created
- [ ] Step 3: Instagram switched to Business/Creator + linked to Page
- [ ] Step 4: Registered as Meta Developer
- [ ] Step 5: Meta App created
- [ ] Step 6: Instagram Graph API added to app
- [ ] Step 7a: Short-lived token generated
- [ ] Step 7b: Exchanged for long-lived token (60 days)
- [ ] Step 8a: Facebook Page ID retrieved
- [ ] Step 8b: Instagram Business Account ID retrieved
- [ ] Step 9: INSTAGRAM_TOKEN and INSTAGRAM_ID saved to .env
- [ ] Step 10: Verification test passed

---

## Common Errors & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| "Invalid OAuth access token" | Short-lived token expired | Generate a new one in Graph Explorer, exchange within 5 min |
| "Error validating application" | Wrong App ID or App Secret | Go to App Dashboard → Settings → Basic, re-copy both |
| "OAuthException code 2500" | Token expired or not copied fully | Regenerate and exchange immediately |
| "instagram_business_account is null" | Instagram not linked to Facebook Page | Redo Step 3 — link Instagram to your Page |
| "Requires business validation" | App is in Development mode | App Dashboard → toggle to Live mode at the top |
| Pages list is empty | Page not created or wrong account | Make sure you're logged into the right Facebook account |

---

## Token Refresh (Every 60 Days)

Your long-lived token expires after 60 days. To refresh it, run:

```powershell
$OLD_TOKEN = "paste_your_current_long_lived_token"

$r = Invoke-RestMethod -Uri "https://graph.facebook.com/v21.0/oauth/access_token?grant_type=fb_exchange_token&client_id=YOUR_APP_ID&client_secret=YOUR_APP_SECRET&fb_exchange_token=$OLD_TOKEN"

Write-Host "NEW TOKEN:" $r.access_token
```

Replace the old token in your `.env` file with the new one.

> The upload script will be built with automatic token refresh so you won't need to do this manually.

---

## What Happens After Setup

Once setup is complete, the automation pipeline will be updated to:

1. Upload YouTube Short (with subtitles) → YouTube
2. Upload Instagram Reel (clean, no subs) → Instagram
3. Same content, 2 platforms, 4 posts per day, fully automated

```
main.py runs daily:
  Video 1 → YouTube (9 AM EST) + Instagram Reel
  Video 2 → YouTube (4 PM EST) + Instagram Reel
```
