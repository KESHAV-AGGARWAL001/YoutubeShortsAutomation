from fastapi import APIRouter
from server.models.schemas import UploadRequest
from server.services.state import pipeline_state
from server.services.pipeline_runner import run_step

router = APIRouter()


@router.post("/upload")
async def upload_video(req: UploadRequest):
    result = await run_step(
        "upload",
        pipeline_state,
        publish_time_utc=req.publish_time_utc,
        video_number=1,
    )
    return {
        "status": "uploaded",
        "video_id": result.get("video_id", ""),
        "video_url": result.get("video_url", ""),
    }
