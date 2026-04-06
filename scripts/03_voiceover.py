import os
import asyncio
import time
import subprocess
import edge_tts
from dotenv import load_dotenv

load_dotenv()

# Microsoft Edge TTS — completely free, unlimited, no API key needed
# Best voices for motivational content
VOICE = "en-US-GuyNeural"     # Deep, powerful American male — perfect for motivation
RATE  = "-5%"                  # Slightly slower = more powerful and cinematic
PITCH = "-3Hz"                 # Slightly deeper pitch


async def generate_section(text, output_file):
    """Generate voiceover for one section using Edge TTS"""
    communicate = edge_tts.Communicate(
        text=text,
        voice=VOICE,
        rate=RATE,
        pitch=PITCH
    )
    await communicate.save(output_file)
    return os.path.exists(output_file) and os.path.getsize(output_file) > 1000


def main():
    print("=" * 50)
    print("  Voiceover Generator — Microsoft Edge TTS")
    print("  100% Free · Unlimited · No API Key · Local")
    print(f"  Voice: {VOICE}")
    print("=" * 50)

    os.makedirs("output/voiceovers", exist_ok=True)
    sections_dir = "output/sections"

    if not os.path.exists(sections_dir):
        print("  Error: No sections found. Run 02_write_script.py first!")
        return

    section_files = sorted([
        f for f in os.listdir(sections_dir) if f.endswith(".txt")
    ])

    print(f"\n  Found {len(section_files)} script sections\n")

    success_count = 0
    for i, filename in enumerate(section_files, 1):
        section_name = filename.replace(".txt", "")
        output_file  = f"output/voiceovers/{section_name}.mp3"

        # Skip if already generated
        if os.path.exists(output_file) and os.path.getsize(output_file) > 1000:
            print(f"[{i}/{len(section_files)}] Skipping (already exists): {section_name}")
            success_count += 1
            continue

        print(f"[{i}/{len(section_files)}] Generating: {section_name}...")

        with open(f"{sections_dir}/{filename}", "r", encoding="utf-8") as f:
            text = f.read().strip()

        # Run async TTS
        success = asyncio.run(generate_section(text, output_file))

        if success:
            size_kb = os.path.getsize(output_file) // 1024
            print(f"  Saved: {output_file} ({size_kb} KB)")
            success_count += 1
        else:
            print(f"  Failed: {section_name}")

        time.sleep(0.5)

    print("\n" + "=" * 50)
    print(f"  Done! {success_count}/{len(section_files)} sections generated")
    print("  Files saved in output/voiceovers/")
    print("=" * 50)
    print("\n  Next step: Run 04_get_footage.py")


if __name__ == "__main__":
    main()