from pydantic import BaseModel, Field
from typing import Optional


class ScriptData(BaseModel):
    hook: str = ""
    body: str = ""
    cta: str = ""


class SeoData(BaseModel):
    youtube_title: str = ""
    description: str = ""
    tags: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    category: str = "Education"
    category_id: str = "27"
    angle_type: str = ""


class GenerateScriptRequest(BaseModel):
    source: str = "book"
    custom_content: Optional[str] = None
    custom_prompt: Optional[str] = None
    book_filename: Optional[str] = None
    video_number: int = 1


class UpdateScriptRequest(BaseModel):
    script: ScriptData
    seo_data: SeoData


class GenerateVoiceoverResponse(BaseModel):
    status: str
    sections: list[dict] = Field(default_factory=list)
    total_duration: float = 0.0


class GenerateVideoResponse(BaseModel):
    status: str
    video_file: str = ""
    duration_seconds: float = 0.0
    size_mb: float = 0.0


class GenerateThumbnailResponse(BaseModel):
    status: str
    thumbnail_file: str = ""
    size_kb: float = 0.0
    method: str = ""


class UploadRequest(BaseModel):
    publish_time_utc: Optional[str] = None
    privacy_status: str = "private"


class UploadResponse(BaseModel):
    status: str
    video_id: str = ""
    video_url: str = ""


class RunPipelineRequest(BaseModel):
    source: str = "book"
    custom_content: Optional[str] = None
    custom_prompt: Optional[str] = None
    video_number: int = 1
    skip_upload: bool = False
    publish_time_utc: Optional[str] = None


class PipelineStep(BaseModel):
    id: str
    label: str
    status: str = "pending"
    error: Optional[str] = None


class PipelineStatusResponse(BaseModel):
    pipeline_status: str = "idle"
    current_step: Optional[str] = None
    steps: list[PipelineStep] = Field(default_factory=list)
    script: Optional[ScriptData] = None
    seo_data: Optional[SeoData] = None
    output_files: dict = Field(default_factory=dict)
    logs: list[str] = Field(default_factory=list)


class SettingsData(BaseModel):
    voice: str = "en-US-GuyNeural"
    voice_rate: str = "-5%"
    voice_pitch: str = "-3Hz"
    script_version: str = "v1"
    gemini_model: str = "gemini-2.5-flash"


class BookInfo(BaseModel):
    filename: str
    display_name: str
    total_pages: int = 0
    current_page: int = 0
    end_page: int = -1
