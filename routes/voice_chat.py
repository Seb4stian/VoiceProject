"""Voice Chat routes — combines TTS, STT, and psychology chat."""

import io
import json
import os

from elevenlabs import ElevenLabs
from flask import Blueprint, jsonify, render_template, request, send_file
from flask import session as flask_session
from openai import OpenAI

from shared import CONFIG, VOICE_TONE_PROMPT, voice_tone_to_score
from voice import get_or_create_voice

bp = Blueprint("voice_chat", __name__, url_prefix="/voice-chat")


@bp.route("/")
def page():
    return render_template("voice_chat.html")


@bp.route("/speak", methods=["POST"])
def speak():
    """TTS for the voice chat — auto-detects language from text."""
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

    try:
        audio_iter = client.text_to_speech.convert(
            text=text,
            voice_id=voice_id,
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128",
        )
        audio_bytes = b"".join(audio_iter)
    except Exception as exc:
        return jsonify({"error": f"Text-to-speech failed: {exc}"}), 500

    return send_file(
        io.BytesIO(audio_bytes),
        mimetype="audio/mpeg",
        download_name="speech.mp3",
    )


@bp.route("/transcribe", methods=["POST"])
def transcribe():
    """STT for the voice chat — auto-detects language, also detects emotional tone."""
    audio = request.files.get("audio")
    if audio is None:
        return jsonify({"error": "No audio file provided"}), 400

    el_key = os.environ.get("ELEVENLABS_API_KEY")
    if not el_key:
        return jsonify({"error": "ELEVENLABS_API_KEY environment variable is not set"}), 500

    # Read audio bytes so we can reuse the stream
    audio_bytes = audio.stream.read()

    client = ElevenLabs(api_key=el_key)

    try:
        result = client.speech_to_text.convert(
            file=io.BytesIO(audio_bytes),
            model_id="scribe_v1",
        )
        text = result.text
    except Exception as exc:
        return jsonify({"error": f"Transcription failed: {exc}"}), 500

    # Analyze emotional tone from the transcribed text
    voice_tone = None
    voice_tone_score = None
    if text and text.strip():
        try:
            oai_key = os.environ.get("OPENAI_API_KEY")
            if oai_key:
                oai_client = OpenAI(api_key=oai_key)
                model = CONFIG.get("openai_model", "gpt-4o-mini")
                tone_response = oai_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are an emotion analysis expert. Respond only with valid JSON."},
                        {"role": "user", "content": VOICE_TONE_PROMPT + text.strip()},
                    ],
                    temperature=0,
                )
                raw_tone = tone_response.choices[0].message.content.strip()
                tone_data = json.loads(raw_tone)
                voice_tone = tone_data.get("tone", "neutral").lower()
                if voice_tone not in ("happy", "sad", "angry", "anxious", "calm", "neutral", "fearful", "surprised"):
                    voice_tone = "neutral"
                voice_tone_score = voice_tone_to_score(voice_tone)
        except Exception:
            pass  # Tone analysis is best-effort; don't block transcription

    return jsonify({
        "text": text,
        "voice_tone": voice_tone,
        "voice_tone_score": voice_tone_score,
    })
