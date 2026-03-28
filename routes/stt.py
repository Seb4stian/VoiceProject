"""Speech-to-Text routes."""

import os

from elevenlabs import ElevenLabs
from flask import Blueprint, jsonify, render_template, request

bp = Blueprint("stt", __name__, url_prefix="/stt")


@bp.route("/")
def page():
    return render_template("stt.html")


@bp.route("/transcribe", methods=["POST"])
def transcribe():
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
