import json
import os
import threading
import asyncio
from server.models.schemas import PipelineStep, ScriptData, SeoData

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE_FILE = os.path.join(PROJECT_ROOT, "output", "dashboard_state.json")

DEFAULT_STEPS = [
    PipelineStep(id="generate_script", label="Generate Script"),
    PipelineStep(id="generate_voiceover", label="Voiceover"),
    PipelineStep(id="assemble_video", label="Assemble Video"),
    PipelineStep(id="generate_thumbnail", label="Thumbnail"),
    PipelineStep(id="upload", label="Upload"),
]


class PipelineState:
    def __init__(self):
        self._lock = threading.Lock()
        self.version = 0
        self._event_queues: list[asyncio.Queue] = []
        self.reset()

    def reset(self):
        with self._lock:
            self.pipeline_status = "idle"
            self.current_step = None
            self.steps = [s.model_copy() for s in DEFAULT_STEPS]
            self.script = None
            self.seo_data = None
            self.output_files = {}
            self.logs = []
            self.version += 1

    def to_dict(self):
        with self._lock:
            return {
                "pipeline_status": self.pipeline_status,
                "current_step": self.current_step,
                "steps": [s.model_dump() for s in self.steps],
                "script": self.script.model_dump() if self.script else None,
                "seo_data": self.seo_data.model_dump() if self.seo_data else None,
                "output_files": dict(self.output_files),
                "logs": list(self.logs[-200:]),
            }

    def set_step_status(self, step_id: str, status: str, error: str = None):
        with self._lock:
            for s in self.steps:
                if s.id == step_id:
                    s.status = status
                    s.error = error
                    break
            if status == "running":
                self.current_step = step_id
                self.pipeline_status = "running"
            self.version += 1
        self._notify()

    def set_pipeline_status(self, status: str):
        with self._lock:
            self.pipeline_status = status
            if status in ("completed", "error", "idle"):
                self.current_step = None
            self.version += 1
        self._notify()

    def add_log(self, message: str):
        with self._lock:
            self.logs.append(message)
            if len(self.logs) > 500:
                self.logs = self.logs[-300:]
            self.version += 1
        self._notify()

    def set_script(self, script: ScriptData, seo_data: SeoData):
        with self._lock:
            self.script = script
            self.seo_data = seo_data
            self.version += 1
        self._notify()

    def set_output_file(self, key: str, filename: str):
        with self._lock:
            self.output_files[key] = filename
            self.version += 1
        self._notify()

    def load_from_output(self):
        """Load script/seo data from output/ if it exists."""
        output_dir = os.path.join(PROJECT_ROOT, "output")
        seo_path = os.path.join(output_dir, "seo_data.json")
        if os.path.exists(seo_path):
            try:
                with open(seo_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.seo_data = SeoData(**data)
            except Exception:
                pass

        sections_dir = os.path.join(output_dir, "sections")
        if os.path.exists(sections_dir):
            try:
                script = ScriptData()
                hook_path = os.path.join(sections_dir, "01_hook.txt")
                body_path = os.path.join(sections_dir, "02_script.txt")
                cta_path = os.path.join(sections_dir, "03_cta.txt")
                if os.path.exists(hook_path):
                    script.hook = open(hook_path, "r", encoding="utf-8").read()
                if os.path.exists(body_path):
                    script.body = open(body_path, "r", encoding="utf-8").read()
                if os.path.exists(cta_path):
                    script.cta = open(cta_path, "r", encoding="utf-8").read()
                if script.hook or script.body or script.cta:
                    self.script = script
            except Exception:
                pass

        for key, fname in [("video", "final_video.mp4"), ("thumbnail", "thumbnail.jpg"),
                           ("voiceover", "full_voiceover.mp3"), ("subtitles", "subtitles.srt")]:
            if os.path.exists(os.path.join(output_dir, fname)):
                self.output_files[key] = fname

    def subscribe(self) -> asyncio.Queue:
        q = asyncio.Queue()
        self._event_queues.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        if q in self._event_queues:
            self._event_queues.remove(q)

    def _notify(self):
        data = self.to_dict()
        for q in self._event_queues:
            try:
                q.put_nowait(data)
            except Exception:
                pass


pipeline_state = PipelineState()
