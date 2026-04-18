import json
import asyncio
from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import StreamingResponse
from server.models.schemas import RunPipelineRequest
from server.services.state import pipeline_state
from server.services.pipeline_runner import run_full_pipeline

router = APIRouter()

_pipeline_task: asyncio.Task = None


@router.get("/status")
async def get_status():
    return pipeline_state.to_dict()


@router.get("/status/stream")
async def status_stream():
    queue = pipeline_state.subscribe()

    async def event_generator():
        try:
            yield f"data: {json.dumps(pipeline_state.to_dict())}\n\n"
            while True:
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=30)
                    yield f"data: {json.dumps(data)}\n\n"
                except asyncio.TimeoutError:
                    yield f": keepalive\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            pipeline_state.unsubscribe(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/run-pipeline")
async def run_pipeline(req: RunPipelineRequest):
    global _pipeline_task

    if pipeline_state.pipeline_status == "running":
        return {"status": "already_running", "message": "Pipeline is already running"}

    _pipeline_task = asyncio.create_task(
        run_full_pipeline(
            pipeline_state,
            source=req.source,
            custom_content=req.custom_content,
            custom_prompt=req.custom_prompt,
            video_number=req.video_number,
            skip_upload=req.skip_upload,
            publish_time_utc=req.publish_time_utc,
        )
    )

    return {"status": "started"}


@router.post("/cancel-pipeline")
async def cancel_pipeline():
    global _pipeline_task
    if _pipeline_task and not _pipeline_task.done():
        _pipeline_task.cancel()
        pipeline_state.set_pipeline_status("idle")
        pipeline_state.add_log("Pipeline cancelled by user")
        return {"status": "cancelled"}
    return {"status": "not_running"}


@router.post("/reset")
async def reset_pipeline():
    pipeline_state.reset()
    return {"status": "reset"}
