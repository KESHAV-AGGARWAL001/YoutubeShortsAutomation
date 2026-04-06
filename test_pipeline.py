import subprocess
import sys
import os
import shutil
import datetime

STEPS = [
    ("02_write_script.py",  "Finding topic + writing script (Groq)"),
    ("03_voiceover.py",     "Generating voiceover (Edge TTS)"),
    ("04_get_footage.py",   "Selecting footage (2 random categories)"),
    ("05_make_video.py",    "Assembling video (FFmpeg)"),
    # Notice: 07_upload.py is explicitly skipped!
]

TEMP_FOLDER = "test_output"

def run_step(script, label, step_num, total):
    print(f"\n{'='*50}")
    print(f"  STEP {step_num}/{total}: {label}")
    print(f"{'='*50}")
    result = subprocess.run([sys.executable, f"scripts/{script}"], capture_output=False)
    if result.returncode != 0:
        print(f"\n  ERROR in {script}. Stopping pipeline.")
        sys.exit(1)

def save_to_temp(video_num):
    print(f"\n  Saving test output for Video {video_num}...")
    os.makedirs(TEMP_FOLDER, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if os.path.exists("output/final_video.mp4"):
        dest = f"{TEMP_FOLDER}/test_video_{video_num}_{timestamp}.mp4"
        shutil.copy2("output/final_video.mp4", dest)
        print(f"  ✅ Video saved: {dest}")
        
    if os.path.exists("output/latest_script.txt"):
        dest_txt = f"{TEMP_FOLDER}/test_script_{video_num}_{timestamp}.txt"
        shutil.copy2("output/latest_script.txt", dest_txt)

def clean_output():
    print("  Cleaning 'output/' directory for next run...")
    if os.path.exists("output"):
        for attempt in range(5):
            try:
                shutil.rmtree("output")
                break
            except PermissionError:
                import time; time.sleep(1)
    os.makedirs("output", exist_ok=True)

def run_test_video(video_num):
    print(f"\n{'#'*50}")
    print(f"  TEST VIDEO {video_num}/2")
    print(f"{'#'*50}")
    
    os.environ["VIDEO_NUMBER"] = str(video_num)
    
    total = len(STEPS)
    for i, (script, label) in enumerate(STEPS, 1):
        run_step(script, label, i, total)
        
    save_to_temp(video_num)
    clean_output()

def main():
    print("\n" + "="*50)
    print("  🎓 PDF Book-to-Shorts — TEST MODE")
    print("  Will generate 2 videos but WILL NOT upload.")
    print("="*50)

    clean_output()
    
    run_test_video(1)
    run_test_video(2)

    print("\n" + "="*50)
    print("  🎉 TEST COMPLETE!")
    print(f"  Check the '{TEMP_FOLDER}' directory to watch your generated Shorts.")
    print("="*50)

if __name__ == "__main__":
    main()
