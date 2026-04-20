import os
import subprocess
import random
from config import (
    OUTPUT_FOLDER, VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS,
    IMAGE_DURATION, XFADE_DURATION,
)


def _escape_path(path):
    return path.replace("\\", "/").replace(":", "\\:")


def _get_duration(filepath):
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_format", filepath],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return 0
    import json
    data = json.loads(result.stdout)
    return float(data.get("format", {}).get("duration", 0))


def build_slideshow(image_paths, output_path=None, target_duration=None):
    """
    Build a silent slideshow video from images with Ken Burns zoom + xfade.

    If target_duration is provided, adjusts per-image duration to fill it.
    Otherwise uses IMAGE_DURATION from config.
    """
    if not image_paths:
        raise ValueError("No images provided")

    output_path = output_path or os.path.join(OUTPUT_FOLDER, "slideshow.mp4")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    n = len(image_paths)

    if target_duration:
        total_xfade = XFADE_DURATION * (n - 1)
        available = target_duration + total_xfade
        per_image = max(2, available / n)
    else:
        per_image = IMAGE_DURATION

    # Each clip's effective duration in the timeline (accounting for xfade overlap)
    effective_per_image = per_image
    total_duration = n * effective_per_image - (n - 1) * XFADE_DURATION

    print(f"  Building slideshow: {n} images, {per_image:.1f}s each, "
          f"{total_duration:.1f}s total")

    inputs = []
    filter_parts = []

    for i, img_path in enumerate(image_paths):
        inputs.extend(["-loop", "1", "-t", str(per_image),
                       "-i", img_path])

        # Ken Burns: random zoom direction (in or out)
        zoom_in = random.choice([True, False])
        if zoom_in:
            zoom_expr = "1+0.04*t"
            x_expr = f"iw/2-(iw/({zoom_expr}))/2"
            y_expr = f"ih/2-(ih/({zoom_expr}))/2"
        else:
            zoom_expr = "1.15-0.04*t"
            x_expr = f"iw/2-(iw/({zoom_expr}))/2"
            y_expr = f"ih/2-(ih/({zoom_expr}))/2"

        filter_parts.append(
            f"[{i}:v]scale={VIDEO_WIDTH * 2}:{VIDEO_HEIGHT * 2},"
            f"zoompan=z='{zoom_expr}':x='{x_expr}':y='{y_expr}':"
            f"d={int(per_image * VIDEO_FPS)}:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:"
            f"fps={VIDEO_FPS},"
            f"setsar=1,format=yuv420p[v{i}]"
        )

    # Chain xfade transitions between all clips
    if n == 1:
        filter_complex = filter_parts[0].replace(f"[v0]", "[vout]")
    else:
        xfade_chain = []
        for i in range(n):
            xfade_chain.append(filter_parts[i])

        prev = "v0"
        for i in range(1, n):
            offset = i * effective_per_image - i * XFADE_DURATION
            out_label = "vout" if i == n - 1 else f"xf{i}"
            xfade_chain.append(
                f"[{prev}][v{i}]xfade=transition=fade:"
                f"duration={XFADE_DURATION}:offset={offset:.3f}[{out_label}]"
            )
            prev = out_label

        filter_complex = ";\n".join(xfade_chain)

    cmd = (
        ["ffmpeg", "-y"]
        + inputs
        + [
            "-filter_complex", filter_complex,
            "-map", "[vout]",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-an",
            output_path,
        ]
    )

    print("  Running ffmpeg slideshow build...")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

    if result.returncode != 0:
        print(f"  FFmpeg stderr:\n{result.stderr[-500:]}")
        raise RuntimeError(f"Slideshow build failed (exit code {result.returncode})")

    duration = _get_duration(output_path)
    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"  Slideshow created: {duration:.1f}s, {size_mb:.1f}MB")

    return output_path


if __name__ == "__main__":
    from image_picker import pick_random_images
    images = pick_random_images()
    build_slideshow(images)
