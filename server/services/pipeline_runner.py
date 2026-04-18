import os
import sys
import io
import importlib
import asyncio
import threading
import datetime
from server.services.state import PipelineState, PROJECT_ROOT
from server.services.script_service import generate_script_from_book, generate_script_from_custom, _load_current_script
from server.models.schemas import ScriptData, SeoData


class LogCapture(io.TextIOBase):
    """Captures stdout writes and feeds them to PipelineState logs."""

    def __init__(self, state: PipelineState):
        self.state = state
        self._buffer = ""

    def write(self, text):
        if not text:
            return 0
        self._buffer += text
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            line = line.strip()
            if line:
                self.state.add_log(line)
        return len(text)

    def flush(self):
        if self._buffer.strip():
            self.state.add_log(self._buffer.strip())
            self._buffer = ""


def _run_script_module(module_name: str, state: PipelineState):
    """Import and run a pipeline script's main() with stdout capture."""
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    capture = LogCapture(state)
    sys.stdout = capture
    sys.stderr = capture
    old_cwd = os.getcwd()

    try:
        os.chdir(PROJECT_ROOT)
        scripts_dir = os.path.join(PROJECT_ROOT, "scripts")
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        if PROJECT_ROOT not in sys.path:
            sys.path.insert(0, PROJECT_ROOT)

        mod = importlib.import_module(module_name)
        importlib.reload(mod)
        mod.main()
    except SystemExit as e:
        if e.code and e.code != 0:
            raise RuntimeError(f"{module_name} exited with code {e.code}")
    finally:
        capture.flush()
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        os.chdir(old_cwd)


async def run_step(step_id: str, state: PipelineState, is_full_pipeline: bool = False, **kwargs):
    """Run a single pipeline step.

    When called individually (is_full_pipeline=False), resets pipeline_status
    to idle after completion so buttons remain clickable.
    """
    module_map = {
        "generate_voiceover": "03_voiceover",
        "select_footage": "04_get_footage",
        "assemble_video": "05_make_video",
        "generate_thumbnail": "06_thumbnail",
        "upload": "07_upload",
    }

    state.set_step_status(step_id, "running")
    state.add_log(f"Starting: {step_id}")

    try:
        if step_id == "generate_script":
            source = kwargs.get("source", "book")
            custom_content = kwargs.get("custom_content")
            custom_prompt = kwargs.get("custom_prompt")
            video_number = kwargs.get("video_number", 1)

            if source == "custom" and custom_content:
                script, seo = await asyncio.to_thread(
                    generate_script_from_custom, custom_content, custom_prompt, video_number
                )
            else:
                script, seo = await asyncio.to_thread(
                    generate_script_from_book, video_number
                )
            state.set_script(script, seo)
            state.set_step_status(step_id, "completed")
            if not is_full_pipeline:
                state.set_pipeline_status("idle")
            return {"script": script, "seo_data": seo}

        elif step_id == "assemble_video":
            await asyncio.to_thread(_run_script_module, "04_get_footage", state)
            await asyncio.to_thread(_run_script_module, "05_make_video", state)
            video_path = os.path.join(PROJECT_ROOT, "output", "final_video.mp4")
            if os.path.exists(video_path):
                size_mb = os.path.getsize(video_path) / (1024 * 1024)
                state.set_output_file("video", "final_video.mp4")
                state.set_step_status(step_id, "completed")
                if not is_full_pipeline:
                    state.set_pipeline_status("idle")
                return {"video_file": "final_video.mp4", "size_mb": round(size_mb, 1)}
            else:
                raise RuntimeError("Video file not created")

        elif step_id == "upload":
            publish_time = kwargs.get("publish_time_utc")
            if publish_time:
                os.environ["PUBLISH_TIME_UTC"] = publish_time
            else:
                future = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=15)
                os.environ["PUBLISH_TIME_UTC"] = future.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            os.environ["VIDEO_NUMBER"] = str(kwargs.get("video_number", 1))

            await asyncio.to_thread(_run_script_module, "07_upload", state)
            state.set_step_status(step_id, "completed")
            if not is_full_pipeline:
                state.set_pipeline_status("idle")
            return {"status": "uploaded"}

        elif step_id in module_map:
            module_name = module_map[step_id]
            await asyncio.to_thread(_run_script_module, module_name, state)

            if step_id == "generate_thumbnail":
                thumb_path = os.path.join(PROJECT_ROOT, "output", "thumbnail.jpg")
                if os.path.exists(thumb_path):
                    state.set_output_file("thumbnail", "thumbnail.jpg")

            if step_id == "generate_voiceover":
                vo_dir = os.path.join(PROJECT_ROOT, "output", "voiceovers")
                if os.path.exists(vo_dir) and any(f.endswith(".mp3") for f in os.listdir(vo_dir)):
                    state.set_output_file("voiceover", "voiceovers")

            state.set_step_status(step_id, "completed")
            if not is_full_pipeline:
                state.set_pipeline_status("idle")
            return {"status": "completed"}

        else:
            raise ValueError(f"Unknown step: {step_id}")

    except Exception as e:
        state.set_step_status(step_id, "error", str(e))
        state.add_log(f"ERROR in {step_id}: {e}")
        if not is_full_pipeline:
            state.set_pipeline_status("idle")
        raise


async def run_full_pipeline(state: PipelineState, **kwargs):
    """Run all pipeline steps sequentially."""
    state.reset()
    state.set_pipeline_status("running")

    step_configs = [
        ("generate_script", {
            "source": kwargs.get("source", "book"),
            "custom_content": kwargs.get("custom_content"),
            "custom_prompt": kwargs.get("custom_prompt"),
            "video_number": kwargs.get("video_number", 1),
        }),
        ("generate_voiceover", {}),
        ("assemble_video", {}),
        ("generate_thumbnail", {}),
    ]

    if not kwargs.get("skip_upload", False):
        step_configs.append(("upload", {
            "publish_time_utc": kwargs.get("publish_time_utc"),
            "video_number": kwargs.get("video_number", 1),
        }))

    for step_id, step_kwargs in step_configs:
        try:
            await run_step(step_id, state, is_full_pipeline=True, **step_kwargs)
        except Exception as e:
            state.set_pipeline_status("error")
            state.add_log(f"Pipeline stopped at {step_id}: {e}")
            return

    state.set_pipeline_status("completed")
    state.add_log("Pipeline completed successfully!")
