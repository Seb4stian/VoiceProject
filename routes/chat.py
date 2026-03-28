"""Psychology Chat routes (text-based)."""

import json
import os

from flask import Blueprint, jsonify, render_template, request
from openai import OpenAI

from shared import (
    CHAT_PSYCHOLOGIST_SYSTEM,
    CHAT_SENTIMENT_PROMPT,
    CHAT_SUMMARY_PROMPT,
    CONFIG,
    SENTIMENT_SYSTEM_PROMPT,
    compute_sentiment_label,
    get_default_language_name,
)

bp = Blueprint("chat", __name__, url_prefix="/chat")


@bp.route("/")
def page():
    return render_template("chat.html")


@bp.route("/start", methods=["POST"])
def start():
    """Return the psychologist's opening greeting in the configured language."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return jsonify({"error": "OPENAI_API_KEY environment variable is not set"}), 500

    model = CONFIG.get("openai_model", "gpt-4o-mini")
    lang = get_default_language_name()
    client = OpenAI(api_key=api_key)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": CHAT_PSYCHOLOGIST_SYSTEM},
                {"role": "user", "content": f"Start the conversation. Greet the patient in {lang}."},
            ],
            temperature=0.7,
        )
        greeting = response.choices[0].message.content.strip()
        return jsonify({"reply": greeting})
    except Exception as exc:
        return jsonify({"error": f"Failed to start chat: {exc}"}), 500


@bp.route("/message", methods=["POST"])
def message():
    """Process a user message: get AI reply (in the user's language) and sentiment score."""
    data = request.get_json(silent=True) or {}
    history = data.get("history", [])
    user_msg = (data.get("message") or "").strip()
    if not user_msg:
        return jsonify({"error": "No message provided"}), 400

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return jsonify({"error": "OPENAI_API_KEY environment variable is not set"}), 500

    model = CONFIG.get("openai_model", "gpt-4o-mini")
    client = OpenAI(api_key=api_key)

    messages = [{"role": "system", "content": CHAT_PSYCHOLOGIST_SYSTEM}]
    for entry in history:
        messages.append({"role": entry["role"], "content": entry["content"]})
    messages.append({"role": "user", "content": user_msg})

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
        )
        reply = response.choices[0].message.content.strip()

        sentiment_response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SENTIMENT_SYSTEM_PROMPT},
                {"role": "user", "content": CHAT_SENTIMENT_PROMPT + user_msg},
            ],
            temperature=0,
        )
        raw_sentiment = sentiment_response.choices[0].message.content.strip()
        sentiment_data = json.loads(raw_sentiment)
        score = float(sentiment_data["score"])
        score = max(-1.0, min(1.0, score))
        label = compute_sentiment_label(score)

        return jsonify({
            "reply": reply,
            "sentiment": {"score": round(score, 2), "label": label},
        })
    except Exception as exc:
        return jsonify({"error": f"Chat failed: {exc}"}), 500


@bp.route("/summary", methods=["POST"])
def summary():
    """Generate a psychological summary in the configured default language."""
    data = request.get_json(silent=True) or {}
    history = data.get("history", [])
    if not history:
        return jsonify({"error": "No conversation to summarize"}), 400

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return jsonify({"error": "OPENAI_API_KEY environment variable is not set"}), 500

    model = CONFIG.get("openai_model", "gpt-4o-mini")
    lang = get_default_language_name()
    client = OpenAI(api_key=api_key)

    transcript = ""
    for entry in history:
        role_label = "Patient" if entry["role"] == "user" else "Psychologist"
        transcript += f"{role_label}: {entry['content']}\n"

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": f"You are a clinical psychologist. Respond only with valid JSON. Write ALL text values in {lang}."},
                {"role": "user", "content": CHAT_SUMMARY_PROMPT + transcript},
            ],
            temperature=0.3,
        )
        raw = response.choices[0].message.content.strip()
        result = json.loads(raw)
        return jsonify(result)
    except json.JSONDecodeError:
        return jsonify({"error": "Failed to parse summary response"}), 500
    except Exception as exc:
        return jsonify({"error": f"Summary generation failed: {exc}"}), 500
