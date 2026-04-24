import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
load_dotenv(os.path.join(BASE_DIR, ".env"), override=True)

# ── Paths ──────────────────────────────────────────────
IMAGE_FOLDER = os.path.join(BASE_DIR, "assets", "images")
MUSIC_FOLDER = os.path.join(BASE_DIR, "music")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "assets", "output")
POEMS_FOLDER = os.path.join(BASE_DIR, "poems")
FONTS_FOLDER = os.path.join(BASE_DIR, "fonts")

# ── Video Settings ─────────────────────────────────────
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
VIDEO_FPS = 30
IMAGES_PER_VIDEO = int(os.getenv("KP_IMAGES_PER_VIDEO", "6"))
XFADE_DURATION = 0.8

# ── TTS Settings (Edge TTS — free) ────────────────────
TTS_VOICE = os.getenv("KP_TTS_VOICE", "en-US-AnaNeural")
TTS_RATE = os.getenv("KP_TTS_RATE", "-15%")
TTS_PITCH = os.getenv("KP_TTS_PITCH", "+3Hz")

# ── Music Settings ────────────────────────────────────
MUSIC_VOLUME = float(os.getenv("KP_MUSIC_VOLUME", "0.20"))

# ── Gemini Settings ───────────────────────────────────
GEMINI_API_KEY = os.getenv("KP_GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("KP_GEMINI_MODEL", "gemini-2.5-pro")
GEMINI_IMAGE_MODEL = os.getenv("KP_GEMINI_IMAGE_MODEL", "gemini-2.0-flash-exp")

# ── HuggingFace Fallback ─────────────────────────
HF_TOKEN = os.getenv("HF_TOKEN", "")
HF_TEXT_MODEL = os.getenv("KP_HF_TEXT_MODEL", "mistralai/Mistral-7B-Instruct-v0.3")
HF_IMAGE_MODEL = os.getenv("KP_HF_IMAGE_MODEL", "stabilityai/stable-diffusion-xl-base-1.0")

# ── Veo Video Generation (Google AI Pro) ─────────
VEO_ENABLED = os.getenv("KP_VEO_ENABLED", "true").lower() == "true"
VEO_MODEL = os.getenv("KP_VEO_MODEL", "veo-3.1-generate-preview")
VEO_LITE_MODEL = "veo-3.1-lite-generate-preview"
VEO_USE_LITE = os.getenv("KP_VEO_USE_LITE", "false").lower() == "true"
VEO_TIMEOUT = int(os.getenv("KP_VEO_TIMEOUT", "300"))
VEO_ENHANCE_PROMPT = os.getenv("KP_VEO_ENHANCE_PROMPT", "true").lower() == "true"
VEO_MAX_WORKERS = int(os.getenv("KP_VEO_MAX_WORKERS", "4"))

# ── YouTube Upload Settings ───────────────────────────
YOUTUBE_CLIENT_SECRETS_KP = os.getenv(
    "YOUTUBE_CLIENT_SECRETS_KP",
    os.path.join(BASE_DIR, "client_secrets_kp.json"),
)
YOUTUBE_TOKEN_KP = os.path.join(BASE_DIR, "token_kp.json")
YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]
YOUTUBE_CATEGORY_ID = "24"  # Entertainment (kids content)

CHANNEL_NAME = "LittleStarFactory"

SUPPORTED_IMAGE_FORMATS = (".jpg", ".jpeg", ".png", ".webp")

# ── Poem Categories & Music Mood Mapping ──────────────
POEM_CATEGORIES = [
    "nursery_rhyme",
    "animal",
    "counting",
    "bedtime",
    "alphabet",
    "colors",
    "action",
    "seasonal",
]

CATEGORY_MUSIC_MOOD = {
    "nursery_rhyme": "playful",
    "animal": "upbeat",
    "counting": "upbeat",
    "bedtime": "calm",
    "alphabet": "playful",
    "colors": "playful",
    "action": "upbeat",
    "seasonal": "magical",
}

# ── Subtitle Style ────────────────────────────────────
SUBTITLE_FONT_SIZE = 48
SUBTITLE_FONT_COLOR = "#FFDD00"
SUBTITLE_OUTLINE_COLOR = "#000000"
SUBTITLE_OUTLINE_WIDTH = 3

# ── Default Tags ──────────────────────────────────────
DEFAULT_TAGS = [
    "kids poems", "nursery rhymes", "children songs",
    "kids learning", "toddler videos", "preschool",
    "learn colors", "ABC", "counting", "bedtime stories",
    "kids shorts", "children", "baby songs", "rhymes",
    "educational", "kids education", "learn english",
    "animation for kids", "poems for kids", "kindergarten",
]
