import os

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(path, override=False):
        if not os.path.isfile(path):
            return
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key = key.strip()
                val = val.strip()
                if override or key not in os.environ:
                    os.environ[key] = val

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
GEMINI_IMAGE_MODEL = os.getenv("KP_GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")

# ── Groq (text fallback — free, 1000 req/day) ───
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("KP_GROQ_MODEL", "llama-3.1-8b-instant")

# ── HuggingFace (image fallback only) ────────────
HF_TOKEN = os.getenv("HF_TOKEN", "")
HF_IMAGE_MODEL = os.getenv("KP_HF_IMAGE_MODEL", "black-forest-labs/FLUX.1-schnell")

# ── Veo Video Generation (Google AI Pro) ─────────
VEO_ENABLED = os.getenv("KP_VEO_ENABLED", "false").lower() == "true"
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
