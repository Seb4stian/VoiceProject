"""ElevenLabs voice cloning helpers (shared across TTS and voice-chat)."""

import os

from elevenlabs import ElevenLabs

from shared import get_recording_files

# Per-user cache: {user_id: (voice_id, files_hash)}
_voice_cache: dict[int, tuple[str, str]] = {}


def _recordings_hash(files: list[str]) -> str:
    parts = [f"{os.path.basename(f)}:{os.path.getsize(f)}" for f in files]
    return "|".join(parts)


def get_or_create_voice(client: ElevenLabs, user_id: int | None = None) -> str:
    """Return a cloned voice_id, creating one if needed. Cached per user."""
    rec_files = get_recording_files(user_id)
    if not rec_files:
        raise ValueError("No recordings found. Record your voice first!")

    current_hash = _recordings_hash(rec_files)
    cache_key = user_id or 0

    if cache_key in _voice_cache:
        cached_id, cached_hash = _voice_cache[cache_key]
        if cached_hash == current_hash:
            return cached_id

    file_handles = [open(f, "rb") for f in rec_files]
    try:
        voice = client.voices.ivc.create(
            name=f"Cloned Voice (user {user_id})",
            description="Voice cloned from local recordings",
            files=file_handles,
        )
    finally:
        for fh in file_handles:
            fh.close()

    _voice_cache[cache_key] = (voice.voice_id, current_hash)
    return voice.voice_id
