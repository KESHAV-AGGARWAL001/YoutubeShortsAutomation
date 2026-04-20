import os
import subprocess
import random
import json
from config import OUTPUT_FOLDER, MUSIC_FOLDER, MUSIC_VOLUME


def _get_duration(filepath):
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_format", filepath],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Cannot probe file: {filepath}")
    data = json.loads(result.stdout)
    return float(data["format"]["duration"])


def _get_random_music():
    if not os.path.isdir(MUSIC_FOLDER):
        return None
    tracks = [
        os.path.join(MUSIC_FOLDER, f)
        for f in os.listdir(MUSIC_FOLDER)
        if f.lower().endswith((".mp3", ".wav", ".m4a", ".aac"))
    ]
    return random.choice(tracks) if tracks else None


def composite_video(slideshow_path, voiceover_path, output_path=None):
    """
    Merge slideshow video + voiceover audio + optional background music.
    Trims or loops the video to match voiceover duration exactly.
    """
    output_path = output_path or os.path.join(OUTPUT_FOLDER, "final_video.mp4")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    vo_duration = _get_duration(voiceover_path)
    vid_duration = _get_duration(slideshow_path)

    print(f"  Voiceover: {vo_duration:.1f}s | Slideshow: {vid_duration:.1f}s")

    music_file = _get_random_music()
    if music_file:
        print(f"  Background music: {os.path.basename(music_file)} "
              f"(volume: {int(MUSIC_VOLUME * 100)}%)")
    else:
        print("  No background music found, proceeding without it")

    # Build the merge command
    # -stream_loop -1 loops the video if voiceover is longer
    # -t trims everything to voiceover duration
    if music_file:
        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", "-1", "-i", slideshow_path,
            "-i", voiceover_path,
            "-stream_loop", "-1", "-i", music_file,
            "-filter_complex",
            f"[1:a]volume=1.0[voice];"
            f"[2:a]volume={MUSIC_VOLUME}[music];"
            f"[voice][music]amix=inputs=2:duration=first:dropout_transition=2[aout]",
            "-map", "0:v",
            "-map", "[aout]",
            "-t", str(vo_duration),
            "-c:v", "libx264", "-preset", "medium", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            output_path,
        ]
    else:
        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", "-1", "-i", slideshow_path,
            "-i", voiceover_path,
            "-map", "0:v",
            "-map", "1:a",
            "-t", str(vo_duration),
            "-c:v", "libx264", "-preset", "medium", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            output_path,
        ]

    print("  Compositing final video...")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

    if result.returncode != 0:
        print(f"  FFmpeg stderr:\n{result.stderr[-500:]}")
        raise RuntimeError(f"Video compositing failed (exit code {result.returncode})")

    final_duration = _get_duration(output_path)
    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"  Final video: {final_duration:.1f}s, {size_mb:.1f}MB")

    return output_path


if __name__ == "__main__":
    slideshow = os.path.join(OUTPUT_FOLDER, "slideshow.mp4")
    voiceover = os.path.join(OUTPUT_FOLDER, "voiceover.mp3")
    if os.path.exists(slideshow) and os.path.exists(voiceover):
        composite_video(slideshow, voiceover)
    else:
        print("  Run slideshow_builder and tts_generator first")
