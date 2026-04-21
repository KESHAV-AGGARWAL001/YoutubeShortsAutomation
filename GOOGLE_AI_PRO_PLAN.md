# Google AI Pro — Usage Plan for NextLevelMind YouTube Automation

**Created:** 2026-04-21
**Channel:** NextLevelMind (motivation/mindset niche)
**Goal:** Hit YPP eligibility — 500 subscribers + 3M Shorts views in 90 days

---

## Current Pipeline Model Usage

| Script | Current Model | Purpose |
|--------|--------------|---------|
| `02_write_script.py` | gemini-2.5-flash | Shorts script generation |
| `02_write_script_v2.py` | gemini-2.5-flash | Retention-optimized script gen |
| `long_02_write_script.py` | gemini-2.5-flash | Long-form script generation |
| `competitor_analysis.py` | gemini-2.5-flash | Competitor pattern analysis |
| `community_post.py` | gemini-2.5-flash | Community post text + image |
| `06_thumbnail.py` | gemini-3.1-flash-image-preview | Thumbnail generation |
| `long_06_thumbnail.py` | gemini-3.1-flash-image-preview | Long-form thumbnail |
| `multi_language.py` | gemini-2.5-flash | Multi-language translation |
| `generate_story_series.py` | gemini-2.5-flash | Story series scripts |
| `carousel/generate_carousel.py` | gemini-2.5-flash | Carousel content |

**Fallback model across all:** gemini-2.0-flash

---

## Google AI Pro Benefits — Mapped to Pipeline

### 1. Gemini Model Upgrade (gemini-2.5-flash → gemini-2.5-pro)

**What:** AI Pro gives higher rate limits on Gemini 2.5 Pro. Upgrading the primary model from Flash to Pro means better script quality — stronger hooks, tighter language, more viral titles.

**Impact:** Higher quality scripts = better retention = more views per Short.

**Files to change:**
- `scripts/02_write_script.py` — MODEL line
- `scripts/02_write_script_v2.py` — GEMINI_MODEL line
- `scripts/long_02_write_script.py` — MODEL line
- `scripts/competitor_analysis.py` — TEXT_MODEL line
- `scripts/community_post.py` — TEXT_MODEL line
- `scripts/multi_language.py` — TEXT_MODEL line
- `generate_story_series.py` — MODEL line
- `carousel/generate_carousel.py` — MODEL line
- `server/models/schemas.py` — gemini_model default
- `frontend/src/components/SettingsPanel.tsx` — gemini_model default

**Keep Flash as fallback:** gemini-2.5-flash replaces gemini-2.0-flash as the fallback model (still free-tier compatible).

**Risk:** Pro may be slightly slower per request. Batch runs (21 shorts/week) may take longer. Monitor API latency.

---

### 2. Flow — AI-Generated Video Backgrounds

**What:** Flow is Google's generative video tool. Instead of looping the same stock footage from `stock/`, generate unique AI video clips per topic. Each Short gets a custom background matching its content.

**Impact:** Unique visuals per video → algorithm sees original content → better push. No more reused stock footage flags.

**Integration plan:**
1. Create `scripts/04_flow_footage.py` as an alternative to `04_get_footage.py`
2. Takes the script topic/hook as input
3. Generates a prompt like "cinematic dark background, person walking alone in rain, motivation aesthetic"
4. Calls Flow API (text-to-video) → downloads 15s clip to `output/`
5. Falls back to stock footage if Flow is unavailable or generation fails
6. Add `USE_FLOW_BACKGROUNDS=true` toggle in `.env`

**Availability note:** Flow currently supports text-to-video. Check if API access is available or if it's web-only. If web-only, this becomes a manual pre-generation workflow.

**Limit:** 5 concurrent generations. For batch runs, queue sequentially.

---

### 3. Google Drive Archive Sync (5 TB Storage)

**What:** AI Pro includes 5 TB storage. The `archive/` folder grows fast at 28 videos/week (~50-100 MB each = 1.4-2.8 GB/week).

**Impact:** Local disk doesn't fill up. Videos backed up to cloud. Can access from anywhere.

**Integration plan:**
1. Create `scripts/drive_sync.py`
2. Uses Google Drive API (same OAuth flow as YouTube API)
3. After each batch run, uploads new files from `archive/` to a "NextLevelMind/Archive" Drive folder
4. Organizes by date: `Archive/2026-04/day1_short1_20260421.mp4`
5. Deletes local archive files older than 7 days after confirmed upload
6. Add to batch_main.py as final step (optional, non-fatal)

**Auth:** Reuse existing `credentials.json` — just add Drive scope: `https://www.googleapis.com/auth/drive.file`

---

### 4. NotebookLM — Deep Book Analysis (Manual Workflow)

**What:** Upload books to NotebookLM before adding them to the `books/` folder. Get AI-generated summaries, key insights, and audio overviews.

**Impact:** Better understanding of book content → more insightful scripts that go beyond surface-level advice.

**Workflow:**
1. Upload new book PDF to NotebookLM
2. Generate Audio Overview → listen for key themes
3. Ask NotebookLM: "What are the 10 most counterintuitive ideas in this book?"
4. Save output as `books/{book_name}_insights.txt`
5. Modify `02_write_script.py` to read `_insights.txt` alongside raw PDF pages → feed both into Gemini prompt

**Limit with AI Pro:** Up to 300 sources per notebook, higher limits on all features.

---

### 5. Deep Research — Weekly Trend Discovery (Manual Workflow)

**What:** Use Deep Research in Gemini to find emerging topics, viral formats, and underserved niches in the motivation/self-improvement space.

**Impact:** Feeds into `competitor_analysis.py` insights. Discovers trends before they peak.

**Weekly workflow:**
1. Every Sunday, run Deep Research query: "What motivation and self-improvement topics are trending on YouTube Shorts this week? What formats are getting the most views?"
2. Save key findings to `output/trend_research.json`
3. `competitor_analysis.py` already reads competitor insights — extend it to also read trend research
4. Run `competitor_analysis.py` → then `batch_main.py`

---

### 6. Whisk — AI Thumbnail Variations (Future)

**What:** Generate unique thumbnail images using Whisk instead of the current dark cinematic template from `06_thumbnail.py`.

**Impact:** More thumbnail variety → better A/B testing data → higher CTR.

**Integration plan:**
1. Current thumbnails use Gemini image generation with a fixed dark cinematic style
2. Whisk could generate multiple style variations per video
3. Upload best-performing style via YouTube API
4. Requires Whisk API access (check availability)

**Note:** Whisk Animate (image-to-video) could also generate short animated thumbnails for community posts.

---

### 7. Google Cloud Credits ($10/month)

**What:** Monthly Google Cloud credits from Developer Program premium.

**Usage options:**
- **YouTube Data API quota increase** — default quota may limit batch uploads. Credits can buy higher quota.
- **Cloud Scheduler + Cloud Run** — run `batch_main.py` automatically every Sunday night on a cloud VM. Fully hands-free weekly production.
- **Cloud Storage** — alternative to Google Drive for video archive.

**Best use for now:** YouTube API quota increase (if hitting limits with 21+ uploads/week).

---

### 8. Google AI Studio — Higher Limits

**What:** AI Pro gives higher limits on Gemini models in AI Studio.

**Impact:** If running pipeline through Google AI Studio's API endpoint instead of the standard Gemini API, you get higher rate limits. This matters for batch_main.py which makes 28+ Gemini calls per weekly run.

**Action:** Verify that the `GEMINI_API_KEY` in `.env` is linked to your AI Pro account to automatically get higher limits.

---

### 9. 1,000 Monthly AI Credits

**What:** Credits that can be used across Google AI services when baseline quota is exhausted.

**Usage priority:**
1. Gemini API overages (when batch runs hit rate limits)
2. Flow video generation
3. Google AI Studio experiments

**Monitor:** Track credit usage at one.google.com/ai/credits

---

## Implementation Priority

| Priority | Integration | Effort | Impact on YPP |
|----------|------------|--------|---------------|
| 1 | Gemini 2.5 Pro model upgrade | Low (change 10 lines) | High — better scripts |
| 2 | Google Drive archive sync | Medium (new script) | Medium — prevents disk issues |
| 3 | Flow video backgrounds | Medium-High (new script + API) | High — unique content |
| 4 | NotebookLM book analysis | Manual workflow | Medium — deeper scripts |
| 5 | Deep Research weekly trends | Manual workflow | Medium — trend-jacking |
| 6 | Cloud Run automation | Medium (infra setup) | High — fully hands-free |
| 7 | Whisk thumbnails | High (API TBD) | Medium — CTR improvement |

---

## Next Steps

1. Verify `GEMINI_API_KEY` is linked to AI Pro account
2. Upgrade all scripts from gemini-2.5-flash → gemini-2.5-pro
3. Build `scripts/drive_sync.py` for archive backup
4. Test Flow API availability for video generation
5. Start weekly NotebookLM + Deep Research workflow
