"""Shared configuration, prompts, and helper functions."""

import json
import os

# ── Paths ─────────────────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RECORDINGS_DIR = os.path.join(BASE_DIR, "recordings")
os.makedirs(RECORDINGS_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {"webm", "ogg", "wav", "mp4"}

# ── Config ────────────────────────────────────────────────────────────────────

_config_path = os.path.join(BASE_DIR, "config.json")
with open(_config_path) as _f:
    CONFIG = json.load(_f)

# ── Prompts ───────────────────────────────────────────────────────────────────

_prompts_dir = os.path.join(BASE_DIR, "prompts")


def load_prompt(filename: str) -> str:
    with open(os.path.join(_prompts_dir, filename)) as f:
        return f.read()


SENTIMENT_SYSTEM_PROMPT = load_prompt("sentiment_system.txt")
SENTIMENT_USER_PROMPT = load_prompt("sentiment_user.txt")
CHAT_PSYCHOLOGIST_SYSTEM = load_prompt("chat_psychologist_system.txt")
CHAT_SENTIMENT_PROMPT = load_prompt("chat_sentiment.txt")
CHAT_SUMMARY_PROMPT = load_prompt("chat_summary.txt")
CHAT_TAKEAWAY_PROMPT = load_prompt("chat_takeaway.txt")
VOICE_TONE_PROMPT = load_prompt("voice_tone.txt")

# ── Language map ──────────────────────────────────────────────────────────────

LANGUAGE_NAMES = {
    "en": "English",
    "es": "Spanish",
    "de": "German",
    "fr": "French",
    "ja": "Japanese",
    "pt": "Portuguese",
    "it": "Italian",
    "zh": "Chinese",
    "ko": "Korean",
}


def get_default_language_name() -> str:
    code = CONFIG.get("default_language", "en")
    return LANGUAGE_NAMES.get(code, code)


# ── Recording helpers ─────────────────────────────────────────────────────────


def get_user_recordings_dir(user_id: int) -> str:
    """Return the recordings directory for a specific user, creating it if needed."""
    user_dir = os.path.join(RECORDINGS_DIR, str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    return user_dir


def safe_filename(name: str) -> str:
    """Return only the basename so directory traversal is not possible."""
    return os.path.basename(name)


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_recording_files(user_id: int | None = None) -> list[str]:
    """Return absolute paths of usable recordings (newest first)."""
    rec_dir = get_user_recordings_dir(user_id) if user_id else RECORDINGS_DIR
    if not os.path.isdir(rec_dir):
        return []
    files = [
        os.path.join(rec_dir, f)
        for f in os.listdir(rec_dir)
        if not f.startswith(".") and allowed_file(f)
    ]
    files.sort(key=os.path.getmtime, reverse=True)
    return files


# ── Sentiment scoring helper ──────────────────────────────────────────────────


def compute_sentiment_label(score: float) -> str:
    if score > 0.25:
        return "Good"
    elif score < -0.25:
        return "Bad"
    return "Neutral"


# ── Voice tone scoring helper ─────────────────────────────────────────────────

VOICE_TONE_SCORES = {
    "happy": 0.8,
    "calm": 0.4,
    "surprised": 0.2,
    "neutral": 0.0,
    "anxious": -0.3,
    "sad": -0.6,
    "angry": -0.8,
    "fearful": -0.9,
}


def voice_tone_to_score(tone: str) -> float:
    """Map a voice tone label to a numerical score in the range [-1, 1]."""
    return VOICE_TONE_SCORES.get(tone.lower(), 0.0)
