"""ElevenLabs voice cloning helpers (shared across TTS and voice-chat)."""

import os

from elevenlabs import ElevenLabs

from shared import get_recording_files

# Cache so we only clone once per server lifetime
_cloned_voice_id: str | None = None
_cloned_files_hash: str | None = None


def _recordings_hash(files: list[str]) -> str:
    parts = [f"{os.path.basename(f)}:{os.path.getsize(f)}" for f in files]
    return "|".join(parts)


def get_or_create_voice(client: ElevenLabs) -> str:
    """Return a cloned voice_id, creating one if needed."""
    global _cloned_voice_id, _cloned_files_hash

    rec_files = get_recording_files()
    if not rec_files:
        raise ValueError("No recordings found. Record your voice first!")

    current_hash = _recordings_hash(rec_files)
    if _cloned_voice_id and _cloned_files_hash == current_hash:
        return _cloned_voice_id

    file_handles = [open(f, "rb") for f in rec_files]
    try:
        voice = client.voices.ivc.create(
            name="My Cloned Voice",
            description="Voice cloned from local recordings",
            files=file_handles,
        )
    finally:
        for fh in file_handles:
            fh.close()

    _cloned_voice_id = voice.voice_id
    _cloned_files_hash = current_hash
    return _cloned_voice_id
