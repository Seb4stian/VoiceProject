"""Psychology Chat routes (text-based)."""

import json
import os

from flask import Blueprint, jsonify, render_template, request
from flask import session as flask_session
from openai import OpenAI

from db import (
    create_chat_session,
    end_chat_session,
    get_session_timeline,
    get_user_takeaways,
    save_chat_message,
)
from shared import (
    CHAT_PSYCHOLOGIST_SYSTEM,
    CHAT_SENTIMENT_PROMPT,
    CHAT_SUMMARY_PROMPT,
    CHAT_TAKEAWAY_PROMPT,
    CONFIG,
    SENTIMENT_SYSTEM_PROMPT,
    compute_sentiment_label,
    get_default_language_name,
)

bp = Blueprint("chat", __name__, url_prefix="/chat")


def _build_system_prompt(user_id: int) -> str:
    """Build the system prompt, enriched with takeaways from previous sessions."""
    base = CHAT_PSYCHOLOGIST_SYSTEM
    takeaways = get_user_takeaways(user_id)
    if not takeaways:
        return base

    history_lines = []
    for i, t in enumerate(reversed(takeaways), 1):
        date_str = t["started_at"].strftime("%Y-%m-%d") if t["started_at"] else "unknown"
        history_lines.append(f"- Session {i} ({date_str}): {t['takeaway']}")

    history_block = "\n".join(history_lines)
    return (
        f"{base}\n\n"
        f"[IMPORTANT — Patient history from previous sessions. "
        f"Use this context to continue the therapeutic relationship naturally. "
        f"Do NOT repeat introductory questions if you already know the answers.]\n"
        f"{history_block}"
    )


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

    user_id = flask_session.get("user_id")
    chat_session_id = create_chat_session(user_id)
    system_prompt = _build_system_prompt(user_id)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Start the conversation. Greet the patient in {lang}."},
            ],
            temperature=0.7,
        )
        greeting = response.choices[0].message.content.strip()
        save_chat_message(chat_session_id, "assistant", greeting)
        return jsonify({"reply": greeting, "session_id": chat_session_id})
    except Exception as exc:
        return jsonify({"error": f"Failed to start chat: {exc}"}), 500


@bp.route("/message", methods=["POST"])
def message():
    """Process a user message: get AI reply (in the user's language) and sentiment score."""
    data = request.get_json(silent=True) or {}
    history = data.get("history", [])
    user_msg = (data.get("message") or "").strip()
    chat_session_id = data.get("session_id")
    voice_tone = data.get("voice_tone")
    voice_tone_score = data.get("voice_tone_score")

    if not user_msg:
        return jsonify({"error": "No message provided"}), 400

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return jsonify({"error": "OPENAI_API_KEY environment variable is not set"}), 500

    model = CONFIG.get("openai_model", "gpt-4o-mini")
    client = OpenAI(api_key=api_key)

    user_id = flask_session.get("user_id")
    system_prompt = _build_system_prompt(user_id)

    messages = [{"role": "system", "content": system_prompt}]
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

        if chat_session_id:
            save_chat_message(
                chat_session_id, "user", user_msg, score, label,
                voice_tone, voice_tone_score,
            )
            save_chat_message(chat_session_id, "assistant", reply)

        result = {
            "reply": reply,
            "sentiment": {"score": round(score, 2), "label": label},
        }
        if voice_tone:
            result["voice_tone"] = {
                "tone": voice_tone,
                "score": voice_tone_score,
            }
        return jsonify(result)
    except Exception as exc:
        return jsonify({"error": f"Chat failed: {exc}"}), 500


@bp.route("/summary", methods=["POST"])
def summary():
    """Generate a psychological summary in the configured default language."""
    data = request.get_json(silent=True) or {}
    history_data = data.get("history", [])
    chat_session_id = data.get("session_id")

    if not history_data:
        return jsonify({"error": "No conversation to summarize"}), 400

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return jsonify({"error": "OPENAI_API_KEY environment variable is not set"}), 500

    model = CONFIG.get("openai_model", "gpt-4o-mini")
    lang = get_default_language_name()
    client = OpenAI(api_key=api_key)

    transcript = ""
    for entry in history_data:
        role_label = "Patient" if entry["role"] == "user" else "Psychologist"
        line = f"{role_label}: {entry['content']}"
        if entry["role"] == "user" and entry.get("voice_tone"):
            line += f" [Voice tone: {entry['voice_tone']}]"
        transcript += line + "\n"

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

        # Generate a takeaway and persist the session
        if chat_session_id:
            takeaway_text = ""
            try:
                takeaway_response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are a clinical psychologist. Write a concise takeaway."},
                        {"role": "user", "content": CHAT_TAKEAWAY_PROMPT + raw},
                    ],
                    temperature=0.3,
                )
                takeaway_text = takeaway_response.choices[0].message.content.strip()
            except Exception:
                takeaway_text = result.get("summary", "")

            user_id = flask_session.get("user_id")
            end_chat_session(chat_session_id, user_id, raw, takeaway_text)

        return jsonify(result)
    except json.JSONDecodeError:
        return jsonify({"error": "Failed to parse summary response"}), 500
    except Exception as exc:
        return jsonify({"error": f"Summary generation failed: {exc}"}), 500


@bp.route("/history", methods=["GET"])
def history():
    """Return the sentiment and voice tone timeline for all completed sessions."""
    user_id = flask_session.get("user_id")
    rows = get_session_timeline(user_id)
    timeline = [
        {
            "session_id": r["id"],
            "date": r["started_at"].isoformat() if r["started_at"] else None,
            "sentiment_score": float(r["sentiment_score"]) if r["sentiment_score"] is not None else 0,
            "voice_tone_score": round(float(r["avg_voice_tone_score"]), 2) if r.get("avg_voice_tone_score") is not None else None,
        }
        for r in rows
    ]
    return jsonify(timeline)
