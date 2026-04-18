import os
from fastapi import APIRouter
from server.services.state import pipeline_state, PROJECT_ROOT
from server.services.pipeline_runner import run_step

router = APIRouter()


@router.post("/generate-voiceover")
async def generate_voiceover():
    await run_step("generate_voiceover", pipeline_state)

    voiceovers_dir = os.path.join(PROJECT_ROOT, "output", "voiceovers")
    sections = []
    total_duration = 0.0

    if os.path.exists(voiceovers_dir):
        import subprocess
        for fname in sorted(os.listdir(voiceovers_dir)):
            if fname.endswith(".mp3"):
                fpath = os.path.join(voiceovers_dir, fname)
                try:
                    result = subprocess.run(
                        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                         "-of", "default=noprint_wrappers=1:nokey=1", fpath],
                        capture_output=True, text=True, timeout=10,
                    )
                    dur = float(result.stdout.strip())
                except Exception:
                    dur = 0.0

                size_kb = os.path.getsize(fpath) / 1024
                sections.append({
                    "name": os.path.splitext(fname)[0],
                    "duration_seconds": round(dur, 1),
                    "size_kb": round(size_kb, 1),
                })
                total_duration += dur

    return {
        "status": "completed",
        "sections": sections,
        "total_duration": round(total_duration, 1),
    }
