import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
load_dotenv(os.path.join(BASE_DIR, ".env"), override=True)

# ── Paths ──────────────────────────────────────────────
IMAGE_FOLDER = os.path.join(BASE_DIR, "assets", "images")
MUSIC_FOLDER = os.path.join(BASE_DIR, "assets", "music")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "assets", "output")
CONTENT_FILE = os.path.join(BASE_DIR, "content", "today_script.txt")

# ── Image Slideshow Settings ──────────────────────────
IMAGES_PER_VIDEO = int(os.getenv("RK_IMAGES_PER_VIDEO", "10"))
IMAGE_DURATION = int(os.getenv("RK_IMAGE_DURATION", "3"))
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
VIDEO_FPS = 30
XFADE_DURATION = 1  # crossfade transition duration in seconds

# ── TTS Settings (Edge TTS — free, no API key) ────────
TTS_VOICE = os.getenv("RK_TTS_VOICE", "hi-IN-SwaraNeural")  # sweet Hindi female
TTS_RATE = os.getenv("RK_TTS_RATE", "-5%")
TTS_PITCH = os.getenv("RK_TTS_PITCH", "+2Hz")

# ── Music Settings ────────────────────────────────────
MUSIC_VOLUME = float(os.getenv("RK_MUSIC_VOLUME", "0.15"))

# ── YouTube Upload Settings ───────────────────────────
YOUTUBE_CLIENT_SECRETS_RK = os.getenv(
    "YOUTUBE_CLIENT_SECRETS_RK",
    os.path.join(BASE_DIR, "client_secrets_rk.json"),
)
YOUTUBE_TOKEN_RK = os.path.join(BASE_DIR, "token_rk.json")
YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]
YOUTUBE_CATEGORY_ID = "22"  # People & Blogs

SUPPORTED_IMAGE_FORMATS = (".jpg", ".jpeg", ".png", ".webp")
