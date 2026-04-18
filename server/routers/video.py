import os
from fastapi import APIRouter, HTTPException
from server.services.state import pipeline_state, PROJECT_ROOT
from server.services.pipeline_runner import run_step

router = APIRouter()


@router.post("/generate-video")
async def generate_video():
    try:
        await run_step("assemble_video", pipeline_state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    video_path = os.path.join(PROJECT_ROOT, "output", "final_video.mp4")
    duration = 0.0
    size_mb = 0.0

    if os.path.exists(video_path):
        import subprocess
        try:
            res = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", video_path],
                capture_output=True, text=True, timeout=15,
            )
            duration = float(res.stdout.strip())
        except Exception:
            pass
        size_mb = os.path.getsize(video_path) / (1024 * 1024)

    return {
        "status": "completed",
        "video_file": "final_video.mp4",
        "duration_seconds": round(duration, 1),
        "size_mb": round(size_mb, 1),
    }
