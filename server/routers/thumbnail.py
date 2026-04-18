import os
from fastapi import APIRouter
from server.services.state import pipeline_state, PROJECT_ROOT
from server.services.pipeline_runner import run_step

router = APIRouter()


@router.post("/generate-thumbnail")
async def generate_thumbnail():
    await run_step("generate_thumbnail", pipeline_state)

    thumb_path = os.path.join(PROJECT_ROOT, "output", "thumbnail.jpg")
    size_kb = 0.0
    method = "unknown"

    if os.path.exists(thumb_path):
        size_kb = os.path.getsize(thumb_path) / 1024

    return {
        "status": "completed",
        "thumbnail_file": "thumbnail.jpg",
        "size_kb": round(size_kb, 1),
        "method": method,
    }
