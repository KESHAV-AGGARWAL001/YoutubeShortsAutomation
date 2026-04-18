from fastapi import APIRouter, HTTPException
from server.models.schemas import GenerateScriptRequest, UpdateScriptRequest
from server.services.state import pipeline_state
from server.services.script_service import save_script, _load_current_script
from server.services.pipeline_runner import run_step

router = APIRouter()


@router.post("/generate-script")
async def generate_script(req: GenerateScriptRequest):
    try:
        result = await run_step(
            "generate_script",
            pipeline_state,
            source=req.source,
            custom_content=req.custom_content,
            custom_prompt=req.custom_prompt,
            video_number=req.video_number,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    script = result["script"]
    seo = result["seo_data"]
    return {
        "status": "completed",
        "script": script.model_dump(),
        "seo_data": seo.model_dump(),
    }


@router.get("/script")
async def get_script():
    script, seo_data = _load_current_script()
    return {
        "script": script.model_dump(),
        "seo_data": seo_data.model_dump(),
    }


@router.put("/script")
async def update_script(req: UpdateScriptRequest):
    save_script(req.script, req.seo_data)
    pipeline_state.set_script(req.script, req.seo_data)
    return {"status": "updated"}
