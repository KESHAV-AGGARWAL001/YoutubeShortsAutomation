from fastapi import APIRouter, HTTPException
from server.models.schemas import UploadRequest
from server.services.state import pipeline_state
from server.services.pipeline_runner import run_step

router = APIRouter()


@router.post("/upload")
async def upload_video(req: UploadRequest):
    try:
        result = await run_step(
            "upload",
            pipeline_state,
            publish_time_utc=req.publish_time_utc,
            video_number=1,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "status": "uploaded",
        "video_id": result.get("video_id", ""),
        "video_url": result.get("video_url", ""),
    }
