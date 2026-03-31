"""Text-to-Speech routes."""

import io
import os

from elevenlabs import ElevenLabs
from flask import Blueprint, jsonify, render_template, request, send_file
from flask import session as flask_session

from shared import LANGUAGE_NAMES
from voice import get_or_create_voice

bp = Blueprint("tts", __name__, url_prefix="/tts")


@bp.route("/")
def page():
    return render_template("tts.html")


@bp.route("/speak", methods=["POST"])
def speak():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "No text provided"}), 400

    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        return jsonify({"error": "ELEVENLABS_API_KEY environment variable is not set"}), 500

    client = ElevenLabs(api_key=api_key)

    try:
        voice_id = get_or_create_voice(client, flask_session.get("user_id"))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"error": f"Voice cloning failed: {exc}"}), 500

    SUPPORTED_LANGUAGES = set(LANGUAGE_NAMES.keys())
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
