import os
import asyncio
import edge_tts
from config import OUTPUT_FOLDER, TTS_VOICE, TTS_RATE, TTS_PITCH


async def _generate_voiceover(text, output_file):
    communicate = edge_tts.Communicate(
        text=text,
        voice=TTS_VOICE,
        rate=TTS_RATE,
        pitch=TTS_PITCH,
    )
    await communicate.save(output_file)
    return os.path.exists(output_file) and os.path.getsize(output_file) > 1000


def generate_voiceover(text, output_path=None):
    """
    Generate voiceover from text using Edge TTS.
    Uses hi-IN-SwaraNeural — a sweet, calm Hindi female voice.
    """
    output_path = output_path or os.path.join(OUTPUT_FOLDER, "voiceover.mp3")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    print(f"  Voice: {TTS_VOICE} | Rate: {TTS_RATE} | Pitch: {TTS_PITCH}")
    print(f"  Text length: {len(text)} characters")

    success = asyncio.run(_generate_voiceover(text, output_path))

    if not success:
        raise RuntimeError("TTS generation failed — output file missing or too small")

    size_kb = os.path.getsize(output_path) / 1024
    print(f"  Voiceover saved: {size_kb:.0f}KB")

    return output_path


def get_voiceover_duration(filepath):
    import subprocess, json
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_format", filepath],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Cannot probe audio: {filepath}")
    data = json.loads(result.stdout)
    return float(data["format"]["duration"])


if __name__ == "__main__":
    sample = "हरे कृष्ण हरे कृष्ण, कृष्ण कृष्ण हरे हरे। हरे राम हरे राम, राम राम हरे हरे।"
    generate_voiceover(sample)
    print("  Done!")
