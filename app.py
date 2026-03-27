import io
import os
import uuid

from dotenv import load_dotenv
from elevenlabs import ElevenLabs

load_dotenv()
from flask import Flask, jsonify, render_template, request, send_file, send_from_directory

app = Flask(__name__)

RECORDINGS_DIR = os.path.join(os.path.dirname(__file__), "recordings")
os.makedirs(RECORDINGS_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {"webm", "ogg", "wav", "mp4"}

# ElevenLabs voice clone cache (voice_id, file hash) so we only clone once
_cloned_voice_id: str | None = None
_cloned_files_hash: str | None = None


def _safe_filename(name: str) -> str:
    """Return only the basename so directory traversal is not possible."""
    return os.path.basename(name)


def _allowed(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    """Receive an audio blob from the browser and save it to the recordings folder."""
    audio = request.files.get("audio")
    if audio is None:
        return jsonify({"error": "No audio file provided"}), 400

    ext = audio.filename.rsplit(".", 1)[-1].lower() if "." in audio.filename else "webm"
    if ext not in ALLOWED_EXTENSIONS:
        ext = "webm"

    filename = f"{uuid.uuid4().hex}.{ext}"
    save_path = os.path.join(RECORDINGS_DIR, filename)
    audio.save(save_path)

    return jsonify({"filename": filename}), 201


@app.route("/recordings", methods=["GET"])
def list_recordings():
    """Return a JSON list of saved recording filenames, newest first."""
    files = [
        f
        for f in os.listdir(RECORDINGS_DIR)
        if not f.startswith(".") and _allowed(f)
    ]
    files.sort(key=lambda f: os.path.getmtime(os.path.join(RECORDINGS_DIR, f)), reverse=True)
    return jsonify(files)


@app.route("/recordings/<path:filename>", methods=["GET"])
def serve_recording(filename: str):
    """Serve a specific recording file."""
    safe = _safe_filename(filename)
    if not _allowed(safe):
        return jsonify({"error": "File type not allowed"}), 400
    full_path = os.path.join(RECORDINGS_DIR, safe)
    if not os.path.isfile(full_path):
        return jsonify({"error": "File not found"}), 404
    return send_from_directory(RECORDINGS_DIR, safe)


# ── Speech-to-Text routes ────────────────────────────────────────────────────

@app.route("/stt")
def stt_page():
    """Serve the speech-to-text page."""
    return render_template("stt.html")


@app.route("/stt/transcribe", methods=["POST"])
def stt_transcribe():
    """Record audio from the browser, send to ElevenLabs STT, return text."""
    audio = request.files.get("audio")
    if audio is None:
        return jsonify({"error": "No audio file provided"}), 400

    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        return jsonify({"error": "ELEVENLABS_API_KEY environment variable is not set"}), 500

    client = ElevenLabs(api_key=api_key)

    try:
        result = client.speech_to_text.convert(
            file=audio.stream,
            model_id="scribe_v1",
            language_code=request.form.get("language", "en"),
        )
        return jsonify({"text": result.text})
    except Exception as exc:
        return jsonify({"error": f"Transcription failed: {exc}"}), 500


# ── Text-to-Speech routes ────────────────────────────────────────────────────

def _get_recording_files() -> list[str]:
    """Return absolute paths of usable recordings (newest first)."""
    files = [
        os.path.join(RECORDINGS_DIR, f)
        for f in os.listdir(RECORDINGS_DIR)
        if not f.startswith(".") and _allowed(f)
    ]
    files.sort(key=os.path.getmtime, reverse=True)
    return files


def _recordings_hash(files: list[str]) -> str:
    """Simple hash based on filenames + sizes to detect changes."""
    parts = [f"{os.path.basename(f)}:{os.path.getsize(f)}" for f in files]
    return "|".join(parts)


def _get_or_create_voice(client: ElevenLabs) -> str:
    """Return a cloned voice_id, creating one if needed."""
    global _cloned_voice_id, _cloned_files_hash

    rec_files = _get_recording_files()
    if not rec_files:
        raise ValueError("No recordings found. Record your voice first!")

    current_hash = _recordings_hash(rec_files)
    if _cloned_voice_id and _cloned_files_hash == current_hash:
        return _cloned_voice_id

    # Open file handles for the API call
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


@app.route("/tts")
def tts_page():
    """Serve the text-to-speech page."""
    return render_template("tts.html")


@app.route("/tts/speak", methods=["POST"])
def tts_speak():
    """Convert text to speech using the cloned voice and return audio."""
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "No text provided"}), 400

    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        return jsonify({"error": "ELEVENLABS_API_KEY environment variable is not set"}), 500

    client = ElevenLabs(api_key=api_key)

    try:
        voice_id = _get_or_create_voice(client)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"error": f"Voice cloning failed: {exc}"}), 500

    SUPPORTED_LANGUAGES = {"en", "de", "ja"}
    language = data.get("language", "en")
    if language not in SUPPORTED_LANGUAGES:
        language = "en"

    try:
        audio_iter = client.text_to_speech.convert(
            text=text,
            voice_id=voice_id,
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128",
            language_code=language,
        )
        audio_bytes = b"".join(audio_iter)
    except Exception as exc:
        return jsonify({"error": f"Text-to-speech failed: {exc}"}), 500

    return send_file(
        io.BytesIO(audio_bytes),
        mimetype="audio/mpeg",
        download_name="speech.mp3",
    )


if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug, port=5000)
