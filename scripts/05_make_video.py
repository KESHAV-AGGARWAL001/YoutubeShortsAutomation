"""
05_make_video.py — Video Assembler

Approach:
  1. Merge all voiceover MP3 sections into one full_voiceover.mp3
  2. Loop ONE background stock clip for the full voiceover duration
  3. Create CLEAN video (no subtitles) → video_clean.mp4
  4. Burn timed subtitles onto clean video → video_no_music.mp4
  5. Burn subscribe end card onto last 10s → video_no_music.mp4
  6. Mix background music into both versions:
     - final_video.mp4     → YouTube (with subtitles + end card)
     - video_for_reel.mp4  → Instagram (no subtitles, reel burns its own)
"""

import subprocess
import os
import json
import shutil
import textwrap
import re
import time
import random


# ── End Card — Subscribe overlay for YouTube version ─────────────────

END_CARD_DURATION = 10  # Show end card for last 10 seconds

FONT_PATHS = [
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/calibrib.ttf",
    "C:/Windows/Fonts/verdanab.ttf",
]

END_CARD_TAGLINES = [
    "Your future self will thank you",
    "This is just the beginning",
    "One video a day changes everything",
    "Level up your mind every single day",
    "The grind never stops",
    "Stay hungry. Stay focused.",
    "Your journey starts here",
    "Keep pushing. Keep growing.",
    "Discipline beats motivation",
    "Small steps. Big results.",
]


def get_duration(file):
    """Get duration of any media file in seconds"""
    try:
        result = subprocess.run([
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            file
        ], capture_output=True, text=True, timeout=15)
        return float(result.stdout.strip())
    except Exception:
        return 0.0


def merge_voiceovers():
    """
    Merge all voiceover MP3 sections into one file.
    Re-encodes to a single MP3 to eliminate frame-padding drift
    that causes subtitle desync when using stream-copy concat.
    """
    sections = sorted([
        f"output/voiceovers/{f}"
        for f in os.listdir("output/voiceovers")
        if f.endswith(".mp3")
    ])

    if not sections:
        print("  ERROR: No voiceover files found!")
        return None, 0, []

    # Write concat list with absolute paths
    with open("output/audio_list.txt", "w") as f:
        for s in sections:
            safe = os.path.abspath(s).replace("\\", "/")
            f.write(f"file '{safe}'\n")

    # Re-encode (not stream copy) to eliminate MP3 frame padding gaps
    # that accumulate and cause subtitle timing drift
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", "output/audio_list.txt",
        "-c:a", "libmp3lame", "-q:a", "2",
        "output/full_voiceover.mp3"
    ], capture_output=True)

    duration = get_duration("output/full_voiceover.mp3")
    print(f"  Voiceover merged: {duration:.1f}s ({duration/60:.1f} mins)")
    return "output/full_voiceover.mp3", duration, sections


def recalculate_timings(section_files):
    """
    Recalculate subtitle timings by probing each voiceover MP3's
    actual duration and building cumulative offsets.

    This runs AFTER merging, so timings match the re-encoded audio
    exactly — no MP3 padding drift.
    """
    sections_dir = "output/sections"
    timings = []
    cursor = 0.0

    for mp3_path in section_files:
        name = os.path.splitext(os.path.basename(mp3_path))[0]
        txt_file = os.path.join(sections_dir, f"{name}.txt")

        dur = get_duration(mp3_path)
        if dur <= 0:
            continue

        text = ""
        if os.path.exists(txt_file):
            with open(txt_file, "r", encoding="utf-8") as f:
                text = f.read().strip()

        timings.append({
            "name":  name,
            "text":  text,
            "start": round(cursor, 3),
            "end":   round(cursor + dur, 3)
        })
        cursor += dur

    print(f"  Recalculated timings for {len(timings)} sections (total {cursor:.1f}s)")
    return timings


def get_selected_clip():
    """
    Read the single background clip selected by 04_get_footage.py.
    Falls back to any clip in stock/ if the theme file is missing.
    """
    theme_file = "output/video_theme.json"
    if os.path.exists(theme_file):
        with open(theme_file) as f:
            data = json.load(f)
        clip = data.get("selected_clip")
        if clip and os.path.exists(clip):
            return clip

    # Fallback: grab any stock clip
    for root, dirs, files in os.walk("stock"):
        for f in files:
            if f.lower().endswith(".mp4"):
                return os.path.join(root, f)

    return None


def load_section_timings():
    """Load section subtitle timings from 04_get_footage.py output."""
    timing_file = "output/section_timings.json"
    if os.path.exists(timing_file):
        with open(timing_file, encoding="utf-8") as f:
            return json.load(f)
    return []


def seconds_to_srt_time(seconds):
    """Convert seconds to SRT timestamp format: HH:MM:SS,mmm"""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"


def clean_text_for_srt(text):
    """
    Clean text for SRT subtitle format.
    Remove any problematic characters, normalize quotes/apostrophes.
    """
    # Normalize unicode quotes/apostrophes to plain ASCII
    text = text.replace("\u2018", "'")   # left single quote
    text = text.replace("\u2019", "'")   # right single quote
    text = text.replace("\u201c", '"')   # left double quote
    text = text.replace("\u201d", '"')   # right double quote
    text = text.replace("\u2013", "-")   # en dash
    text = text.replace("\u2014", "-")   # em dash
    text = text.replace("\u2026", "...")  # ellipsis
    # Collapse whitespace
    text = " ".join(text.split())
    return text


def build_srt_file(timings):
    """
    Build an SRT subtitle file from section timings.

    Each section's text is split into short lines (~50 chars).
    Each line is shown for roughly equal time within that section.

    SRT is a clean, standard format — no escaping headaches,
    no command-line length limits, handles all Unicode properly.
    """
    srt_path = os.path.abspath("output/subtitles.srt").replace("\\", "/")
    counter = 1

    with open("output/subtitles.srt", "w", encoding="utf-8") as f:
        for section in timings:
            sec_start = section["start"]
            sec_end   = section["end"]
            sec_dur   = sec_end - sec_start
            text      = section["text"]

            if not text.strip() or sec_dur <= 0:
                continue

            # Clean text
            text = clean_text_for_srt(text)

            # Wrap the entire section text into narrow lines (perfect for vertical constraints)
            wrapped_lines = textwrap.wrap(text, width=28)
            
            if not wrapped_lines:
                wrapped_lines = [text[:28]]

            # Group into blocks of up to 4 lines as requested
            blocks = []
            for i in range(0, len(wrapped_lines), 4):
                block = "\n".join(wrapped_lines[i:i+4])
                blocks.append(block)

            # Time per block
            block_dur = sec_dur / len(blocks)

            for i, block in enumerate(blocks):
                line_start = sec_start + i * block_dur
                line_end   = sec_start + (i + 1) * block_dur

                start_ts = seconds_to_srt_time(line_start)
                end_ts   = seconds_to_srt_time(line_end)

                f.write(f"{counter}\n")
                f.write(f"{start_ts} --> {end_ts}\n")
                f.write(f"{block}\n")
                f.write("\n")
                counter += 1

    print(f"  SRT subtitle file: {counter - 1} entries")
    return srt_path


def assemble_video(voiceover_path, voiceover_duration, timings=None):
    """
    Build TWO versions of the video (without music):
      1. video_clean.mp4     — NO subtitles (source for Instagram Reel)
      2. video_no_music.mp4  — WITH subtitles (source for YouTube)

    The clean version is created first, then subtitles are burned
    on top of it for YouTube. This ensures the reel creator gets
    a subtitle-free source to burn its own Instagram-optimized text.
    """
    # ── Background source ──────────────────────────────────────────
    print(f"  Using pure black background as requested.")

    # ── Build SRT subtitle file ──────────────────────────────────────
    if not timings:
        timings = load_section_timings()
    srt_path = None
    if timings:
        print(f"  Building subtitle file for {len(timings)} sections...")
        srt_path = build_srt_file(timings)
    else:
        print("  No section timings found — skipping subtitles")

    # No video filter needed for pure black natively rendered at 1080x1920

    # ── STEP A: Create CLEAN video (no subtitles) ────────────────────
    # This is the source for Instagram Reels — reel burns its own subs
    print(f"  Assembling {voiceover_duration:.1f}s of clean video (no subtitles)...")

    result_clean = subprocess.run([
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=c=black:s=1080x1920:r=30:d={voiceover_duration}",
        "-i", voiceover_path,
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-map", "0:v",
        "-map", "1:a",
        "-c:a", "aac",
        "-b:a", "128k",
        "output/video_clean.mp4"
    ], capture_output=True, text=True)

    if not os.path.exists("output/video_clean.mp4"):
        print(f"  FFmpeg STDERR:\n{result_clean.stderr[-1500:]}")
        return False

    size_mb = os.path.getsize("output/video_clean.mp4") // (1024 * 1024)
    print(f"  Clean video (no subs): {size_mb} MB")

    # ── STEP B: Burn subtitles onto clean video ──────────────────────
    # This version is for YouTube — large text at the bottom
    if srt_path and os.path.exists("output/subtitles.srt"):
        srt_escaped = srt_path.replace("\\", "/").replace(":", "\\:")
        style = (
            "FontName=Arial,"
            "FontSize=14,"
            "PrimaryColour=&H00FFFFFF,"
            "OutlineColour=&H00000000,"
            "BackColour=&H80000000,"
            "Outline=2,"
            "Shadow=1,"
            "MarginV=0,"
            "Alignment=10,"
            "Bold=1"
        )
        vf_subs = f"subtitles='{srt_escaped}':force_style='{style}'"

        print(f"  Burning YouTube subtitles (bottom, large)...")

        result_subs = subprocess.run([
            "ffmpeg", "-y",
            "-i", "output/video_clean.mp4",
            "-vf", vf_subs,
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-c:a", "copy",
            "output/video_no_music.mp4"
        ], capture_output=True, text=True)

        if os.path.exists("output/video_no_music.mp4"):
            size_mb = os.path.getsize("output/video_no_music.mp4") // (1024 * 1024)
            print(f"  YouTube video (with subs): {size_mb} MB")
        else:
            # Subtitle burn failed — use clean version as fallback
            print("  Subtitle burn failed — using clean video for YouTube too")
            shutil.copy2("output/video_clean.mp4", "output/video_no_music.mp4")
    else:
        # No subtitles to burn — YouTube version = clean version
        print("  No subtitles — YouTube version is same as clean version")
        shutil.copy2("output/video_clean.mp4", "output/video_no_music.mp4")

    return True


def safe_cleanup(filepath, action="delete", dest=None):
    """
    Safely delete or rename a file with retries.
    On Windows, FFmpeg may hold a file lock briefly after exit.
    This retries a few times before giving up gracefully.
    """
    for attempt in range(5):
        try:
            if action == "delete":
                os.remove(filepath)
            elif action == "rename" and dest:
                os.rename(filepath, dest)
            return True
        except PermissionError:
            time.sleep(1)
    # Give up silently — temp file left behind is harmless
    print(f"  Note: Could not {action} {os.path.basename(filepath)} (file in use) — skipping cleanup")
    return False


def get_font_path():
    """Return the first available bold font on Windows."""
    for fp in FONT_PATHS:
        if os.path.exists(fp):
            return fp
    return None


def escape_font_path(fp):
    """Escape font path for FFmpeg drawtext (handle Windows drive colon)."""
    fp = fp.replace("\\", "/")
    fp = re.sub(r"^([A-Za-z]):/", r"\1\\:/", fp)
    return fp


def burn_end_card(video_path, total_duration):
    """
    Burn a subscribe end card onto the last 10 seconds of the YouTube video.

    Overlay elements (staggered reveal):
      t+0.0s:  Dark overlay + big red "SUBSCRIBE" text
      t+1.5s:  Channel name "NextLevelMind"
      t+3.0s:  Random motivational tagline
      t+4.5s:  "Like · Share · Turn on Notifications"

    Only applied to the YouTube version (video_no_music.mp4).
    The reel source (video_clean.mp4) stays untouched.
    """
    if total_duration <= END_CARD_DURATION + 5:
        print("  Video too short for end card — skipping")
        return True

    end_start = total_duration - END_CARD_DURATION
    font_path = get_font_path()
    fp = f":fontfile='{escape_font_path(font_path)}'" if font_path else ""
    tagline = random.choice(END_CARD_TAGLINES)
    temp_out = video_path.replace(".mp4", "_ec_temp.mp4")

    # Staggered reveal timings
    t0 = round(end_start, 2)        # overlay + SUBSCRIBE
    t1 = round(end_start + 1.5, 2)  # channel name
    t2 = round(end_start + 3.0, 2)  # motivational tagline
    t3 = round(end_start + 4.5, 2)  # CTA line
    te = round(total_duration, 2)

    # Escape tagline for drawtext (apostrophes break single-quote delimiters)
    tagline_safe = tagline.replace("'", "\u2019")

    vf_parts = [
        # Semi-transparent dark overlay
        f"drawbox=x=0:y=0:w=iw:h=ih:color=black@0.65:t=fill"
        f":enable='between(t,{t0},{te})'",

        # Big red SUBSCRIBE text
        f"drawtext=text='SUBSCRIBE'"
        f"{fp}:fontsize=80:fontcolor=#FF0000"
        f":bordercolor=white:borderw=3"
        f":x=(w-text_w)/2:y=(h/2)-130"
        f":enable='between(t,{t0},{te})'",

        # Channel name
        f"drawtext=text='NextLevelMind'"
        f"{fp}:fontsize=48:fontcolor=white"
        f":bordercolor=black:borderw=2"
        f":x=(w-text_w)/2:y=(h/2)-20"
        f":enable='between(t,{t1},{te})'",

        # Motivational tagline (random from list)
        f"drawtext=text='{tagline_safe}'"
        f"{fp}:fontsize=30:fontcolor=white@0.9"
        f":x=(w-text_w)/2:y=(h/2)+60"
        f":enable='between(t,{t2},{te})'",

        # CTA — Like / Share / Notifications
        f"drawtext=text='Like \u00b7 Share \u00b7 Turn on Notifications'"
        f"{fp}:fontsize=26:fontcolor=white@0.7"
        f":x=(w-text_w)/2:y=(h/2)+130"
        f":enable='between(t,{t3},{te})'",
    ]

    vf = ",".join(vf_parts)
    print(f"  Tagline: \"{tagline}\"")

    result = subprocess.run([
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", vf,
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-c:a", "copy",
        temp_out
    ], capture_output=True, text=True)

    if os.path.exists(temp_out) and os.path.getsize(temp_out) > 10000:
        try:
            os.replace(temp_out, video_path)
        except PermissionError:
            time.sleep(2)
            try:
                os.replace(temp_out, video_path)
            except Exception:
                print("  Could not replace — end card saved as temp file")
                return False
        size_mb = os.path.getsize(video_path) // (1024 * 1024)
        print(f"  End card burned: last {END_CARD_DURATION}s ({size_mb} MB)")
        return True

    print("  End card burn failed — continuing without end card")
    if result.stderr:
        print(f"  FFmpeg: {result.stderr[-500:]}")
    safe_cleanup(temp_out)
    return False


def mix_music_into(input_video, output_video, label=""):
    """
    Mix background music into a video file.
    Voice 100% + music 18%. Video stream copied (no re-encode).
    Returns True if output was created successfully.
    """
    music_file = "music/background.mp3"

    if not os.path.exists(music_file):
        # No music — just copy
        shutil.copy2(input_video, output_video)
        return True

    result = subprocess.run([
        "ffmpeg", "-y",
        "-i", input_video,
        "-stream_loop", "-1",
        "-i", music_file,
        "-filter_complex",
        (
            "[0:a]volume=1.0[voice];"
            "[1:a]volume=0.18,aloop=loop=-1:size=2e+09[music];"
            "[voice][music]amix=inputs=2:duration=first:dropout_transition=2[aout]"
        ),
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "128k",
        output_video
    ], capture_output=True, text=True)

    if os.path.exists(output_video):
        return True

    # Fallback — copy without music
    shutil.copy2(input_video, output_video)
    return True


def mix_background_music():
    """
    Mix background music into both video versions:
      1. video_no_music.mp4 (with subs) → final_video.mp4 (YouTube)
      2. video_clean.mp4 (no subs)      → video_for_reel.mp4 (Instagram)
    """
    music_file = "music/background.mp3"

    if not os.path.exists(music_file):
        print("  No background music found — using voice only")
        print("  Add a track to music/background.mp3 for cinematic effect")

    # ── YouTube version: subtitles + music ────────────────────────────
    print("  Mixing music into YouTube version...")
    mix_music_into("output/video_no_music.mp4", "output/final_video.mp4")

    if os.path.exists("output/final_video.mp4"):
        size_mb = os.path.getsize("output/final_video.mp4") // (1024 * 1024)
        print(f"  YouTube video (subs + music): {size_mb} MB")
    else:
        print("  Music mix failed — saving without music")
        safe_cleanup("output/video_no_music.mp4", action="rename", dest="output/final_video.mp4")

    # ── Reel version: NO subtitles + music ────────────────────────────
    if os.path.exists("output/video_clean.mp4"):
        print("  Mixing music into reel version (no subtitles)...")
        mix_music_into("output/video_clean.mp4", "output/video_for_reel.mp4")

        if os.path.exists("output/video_for_reel.mp4"):
            size_mb = os.path.getsize("output/video_for_reel.mp4") // (1024 * 1024)
            print(f"  Reel source  (clean + music): {size_mb} MB")
    else:
        print("  No clean video found — reel will use final_video.mp4 (with subs)")

    # ── Cleanup intermediates ─────────────────────────────────────────
    if os.path.exists("output/video_no_music.mp4"):
        safe_cleanup("output/video_no_music.mp4")
    if os.path.exists("output/video_clean.mp4"):
        safe_cleanup("output/video_clean.mp4")

    return True


def main():
    print("=" * 50)
    print("  Video Assembler — FFmpeg")
    print("  loop bg + clean + subs + end card + music")
    print("=" * 50)

    # Step 1 — Merge voiceover sections
    print("\n[1/5] Merging voiceover sections...")
    voiceover_path, duration, section_files = merge_voiceovers()
    if not voiceover_path:
        return

    # Step 2 — Recalculate subtitle timings (fixes audio-text desync)
    print("\n[2/5] Recalculating subtitle timings...")
    timings = recalculate_timings(section_files)

    # Step 3 — Assemble video (clean + with subs)
    print("\n[3/5] Assembling video (clean + YouTube subtitles)...")
    if not assemble_video(voiceover_path, duration, timings):
        return

    # Step 4 — End card removed to prevent text overlap
    print("\n[4/5] Skipping end card (overwriting disabled)...")
    if os.path.exists("output/video_no_music.mp4"):
        pass
    else:
        print("  No video_no_music.mp4 found.")

    # Step 5 — Mix background music (both versions)
    print("\n[5/5] Mixing background music (YouTube + Reel versions)...")
    mix_background_music()

    if not os.path.exists("output/final_video.mp4"):
        print("\n  ERROR: final_video.mp4 not created!")
        return

    final_size = os.path.getsize("output/final_video.mp4") // (1024 * 1024)
    final_dur  = get_duration("output/final_video.mp4")

    print("\n" + "=" * 50)
    print(f"  Done! Both versions ready")
    print(f"  Duration : {final_dur:.1f}s ({final_dur/60:.1f} mins)")
    print(f"  YouTube  : output/final_video.mp4 ({final_size} MB)")
    if os.path.exists("output/video_for_reel.mp4"):
        reel_size = os.path.getsize("output/video_for_reel.mp4") // (1024 * 1024)
        print(f"  Reel src : output/video_for_reel.mp4 ({reel_size} MB)")
    print("=" * 50)
    print("\n  Next step: Run 06_thumbnail.py")


if __name__ == "__main__":
    main()