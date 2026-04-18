import os
from fastapi import APIRouter, HTTPException
from server.services.state import pipeline_state, PROJECT_ROOT
from server.services.pipeline_runner import run_step

router = APIRouter()


@router.post("/generate-thumbnail")
async def generate_thumbnail():
    try:
        await run_step("generate_thumbnail", pipeline_state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    thumb_path = os.path.join(PROJECT_ROOT, "output", "thumbnail.jpg")
    size_kb = 0.0

    if os.path.exists(thumb_path):
        size_kb = os.path.getsize(thumb_path) / 1024

    return {
        "status": "completed",
        "thumbnail_file": "thumbnail.jpg",
        "size_kb": round(size_kb, 1),
    }
