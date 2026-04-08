"""
long_05_make_video.py — Long-Form Video Assembler (16:9 horizontal)

Approach:
  1. Merge all voiceover MP3 sections into one full_voiceover.mp3
  2. Create 1920x1080 black background video for full duration
  3. Build SRT subtitles with wider text (50 chars/line, centered)
  4. Burn subtitles centered on screen (ASS Alignment=5)
  5. Mix background music (voice 100% + music 18%)
  6. Output: output/final_video.mp4

Specs: 1920x1080 (16:9), pure black bg, centered white text, 20px font
"""

import subprocess
import os
import json
import shutil
import textwrap
import re
import time
import random


END_CARD_DURATION = 10

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
    sections = sorted([
        f"output/voiceovers/{f}"
        for f in os.listdir("output/voiceovers")
        if f.endswith(".mp3")
    ])

    if not sections:
        print("  ERROR: No voiceover files found!")
        return None, 0, []

    with open("output/audio_list.txt", "w") as f:
        for s in sections:
            safe = os.path.abspath(s).replace("\\", "/")
            f.write(f"file '{safe}'\n")

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


def seconds_to_srt_time(seconds):
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"


def clean_text_for_srt(text):
    text = text.replace("\u2018", "'")
    text = text.replace("\u2019", "'")
    text = text.replace("\u201c", '"')
    text = text.replace("\u201d", '"')
    text = text.replace("\u2013", "-")
    text = text.replace("\u2014", "-")
    text = text.replace("\u2026", "...")
    text = " ".join(text.split())
    return text


def build_srt_file(timings):
    """
    Build SRT subtitle file for 16:9 horizontal with PHRASE-BY-PHRASE display.
    Shows 1-2 lines at a time (not paragraphs) for visual pacing and retention.
    40 chars per line — readable on 1920x1080 without being cramped.

    Duration per block is weighted by WORD COUNT so that blocks with more
    words get proportionally more screen time — prevents text racing ahead
    of or lagging behind the voiceover.
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

            text = clean_text_for_srt(text)

            # Phrase-by-phrase: 40 chars wide, 2 lines per block
            wrapped_lines = textwrap.wrap(text, width=40)

            if not wrapped_lines:
                wrapped_lines = [text[:40]]

            # Group into blocks of 2 lines max
            blocks = []
            for i in range(0, len(wrapped_lines), 2):
                block = "\n".join(wrapped_lines[i:i+2])
                blocks.append(block)

            # Weight duration by word count per block (not equal)
            word_counts = [len(b.split()) for b in blocks]
            total_words = sum(word_counts) or 1

            cursor = sec_start
            for i, block in enumerate(blocks):
                weight = word_counts[i] / total_words
                block_dur = sec_dur * weight
                line_start = cursor
                line_end = cursor + block_dur
                cursor = line_end

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
    Build 16:9 horizontal video (1920x1080) with centered subtitles.
    """
    print(f"  Using pure black background (1920x1080)")

    if not timings:
        timing_file = "output/section_timings.json"
        if os.path.exists(timing_file):
            with open(timing_file, encoding="utf-8") as f:
                timings = json.load(f)
        else:
            timings = []

    srt_path = None
    if timings:
        print(f"  Building subtitle file for {len(timings)} sections...")
        srt_path = build_srt_file(timings)
    else:
        print("  No section timings found — skipping subtitles")

    # Create clean video (no subtitles) — 1920x1080 horizontal
    print(f"  Assembling {voiceover_duration:.1f}s of 16:9 video...")

    result_clean = subprocess.run([
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=c=black:s=1920x1080:r=30:d={voiceover_duration}",
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

    # Burn subtitles — CENTERED on screen (Alignment=5 = middle-center in ASS)
    if srt_path and os.path.exists("output/subtitles.srt"):
        srt_escaped = srt_path.replace("\\", "/").replace(":", "\\:")
        style = (
            "FontName=Arial,"
            "FontSize=18,"
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

        print(f"  Burning centered subtitles (16:9 format)...")

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
            print(f"  Video with centered subs: {size_mb} MB")
        else:
            print("  Subtitle burn failed — using clean video as fallback")
            shutil.copy2("output/video_clean.mp4", "output/video_no_music.mp4")
    else:
        print("  No subtitles — using clean version")
        shutil.copy2("output/video_clean.mp4", "output/video_no_music.mp4")

    return True


def safe_cleanup(filepath, action="delete", dest=None):
    for attempt in range(5):
        try:
            if action == "delete":
                os.remove(filepath)
            elif action == "rename" and dest:
                os.rename(filepath, dest)
            return True
        except PermissionError:
            time.sleep(1)
    print(f"  Note: Could not {action} {os.path.basename(filepath)} — skipping cleanup")
    return False


def get_font_path():
    for fp in FONT_PATHS:
        if os.path.exists(fp):
            return fp
    return None


def escape_font_path(fp):
    fp = fp.replace("\\", "/")
    fp = re.sub(r"^([A-Za-z]):/", r"\1\\:/", fp)
    return fp


def burn_end_card(video_path, total_duration):
    """Burn subscribe end card onto last 10 seconds (16:9 layout)."""
    if total_duration <= END_CARD_DURATION + 5:
        print("  Video too short for end card — skipping")
        return True

    end_start = total_duration - END_CARD_DURATION
    font_path = get_font_path()
    fp = f":fontfile='{escape_font_path(font_path)}'" if font_path else ""
    tagline = random.choice(END_CARD_TAGLINES)
    temp_out = video_path.replace(".mp4", "_ec_temp.mp4")

    t0 = round(end_start, 2)
    t1 = round(end_start + 1.5, 2)
    t2 = round(end_start + 3.0, 2)
    t3 = round(end_start + 4.5, 2)
    te = round(total_duration, 2)

    tagline_safe = tagline.replace("'", "\u2019")

    vf_parts = [
        f"drawbox=x=0:y=0:w=iw:h=ih:color=black@0.65:t=fill"
        f":enable='between(t,{t0},{te})'",

        f"drawtext=text='SUBSCRIBE'"
        f"{fp}:fontsize=100:fontcolor=#FF0000"
        f":bordercolor=white:borderw=3"
        f":x=(w-text_w)/2:y=(h/2)-130"
        f":enable='between(t,{t0},{te})'",

        f"drawtext=text='IronMindset'"
        f"{fp}:fontsize=56:fontcolor=white"
        f":bordercolor=black:borderw=2"
        f":x=(w-text_w)/2:y=(h/2)-20"
        f":enable='between(t,{t1},{te})'",

        f"drawtext=text='{tagline_safe}'"
        f"{fp}:fontsize=36:fontcolor=white@0.9"
        f":x=(w-text_w)/2:y=(h/2)+60"
        f":enable='between(t,{t2},{te})'",

        f"drawtext=text='Like \u00b7 Share \u00b7 Turn on Notifications'"
        f"{fp}:fontsize=30:fontcolor=white@0.7"
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
    safe_cleanup(temp_out)
    return False


def mix_music_into(input_video, output_video):
    music_file = "music/background.mp3"

    if not os.path.exists(music_file):
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

    shutil.copy2(input_video, output_video)
    return True


def mix_background_music():
    music_file = "music/background.mp3"

    if not os.path.exists(music_file):
        print("  No background music found — copying voice-only version...")
    else:
        print("  Mixing music into video...")
    mix_music_into("output/video_no_music.mp4", "output/final_video.mp4")

    if os.path.exists("output/final_video.mp4"):
        size_mb = os.path.getsize("output/final_video.mp4") // (1024 * 1024)
        print(f"  Final video (subs + music): {size_mb} MB")
    else:
        print("  Music mix failed — saving without music")
        safe_cleanup("output/video_no_music.mp4", action="rename", dest="output/final_video.mp4")

    # Cleanup intermediates
    if os.path.exists("output/video_no_music.mp4"):
        safe_cleanup("output/video_no_music.mp4")
    if os.path.exists("output/video_clean.mp4"):
        safe_cleanup("output/video_clean.mp4")

    return True


def main():
    print("=" * 50)
    print("  Long-Form Video Assembler — 16:9 Horizontal")
    print("  1920x1080 · Black BG · Centered Text")
    print("=" * 50)

    # Step 1 — Merge voiceover sections
    print("\n[1/5] Merging voiceover sections...")
    voiceover_path, duration, section_files = merge_voiceovers()
    if not voiceover_path:
        return

    # Step 2 — Recalculate subtitle timings + fix drift
    print("\n[2/5] Recalculating subtitle timings...")
    timings = recalculate_timings(section_files)

    # Fix timing drift: scale all timings to match actual merged audio duration
    if timings:
        timings_total = timings[-1]["end"]
        if timings_total > 0 and abs(timings_total - duration) > 0.1:
            scale = duration / timings_total
            print(f"  Drift fix: {timings_total:.2f}s → {duration:.2f}s (scale: {scale:.4f})")
            for t in timings:
                t["start"] = round(t["start"] * scale, 3)
                t["end"]   = round(t["end"] * scale, 3)

    # Step 3 — Assemble 16:9 video
    print("\n[3/5] Assembling 16:9 video with centered subtitles...")
    if not assemble_video(voiceover_path, duration, timings):
        return

    # Step 4 — End card
    print("\n[4/5] Burning end card (subscribe overlay)...")
    if os.path.exists("output/video_no_music.mp4"):
        burn_end_card("output/video_no_music.mp4", duration)

    # Step 5 — Mix background music
    print("\n[5/5] Mixing background music...")
    mix_background_music()

    if not os.path.exists("output/final_video.mp4"):
        print("\n  ERROR: final_video.mp4 not created!")
        return

    final_size = os.path.getsize("output/final_video.mp4") // (1024 * 1024)
    final_dur  = get_duration("output/final_video.mp4")

    print("\n" + "=" * 50)
    print(f"  Done! Long-form video ready")
    print(f"  Resolution : 1920x1080 (16:9)")
    print(f"  Duration   : {final_dur:.1f}s ({final_dur/60:.1f} mins)")
    print(f"  File       : output/final_video.mp4 ({final_size} MB)")
    print("=" * 50)
    print("\n  Next step: Run long_06_thumbnail.py")


if __name__ == "__main__":
    main()
