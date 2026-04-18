import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from server.services.state import PROJECT_ROOT, pipeline_state
from server.routers import books, script, voiceover, video, thumbnail, upload, pipeline, settings

app = FastAPI(title="YT Shorts Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(books.router, prefix="/api")
app.include_router(script.router, prefix="/api")
app.include_router(voiceover.router, prefix="/api")
app.include_router(video.router, prefix="/api")
app.include_router(thumbnail.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(pipeline.router, prefix="/api")
app.include_router(settings.router, prefix="/api")

output_dir = os.path.join(PROJECT_ROOT, "output")
os.makedirs(output_dir, exist_ok=True)
app.mount("/api/output", StaticFiles(directory=output_dir), name="output")


@app.on_event("startup")
async def startup():
    pipeline_state.load_from_output()


@app.get("/api/health")
async def health():
    return {"status": "ok"}
