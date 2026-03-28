"""Sentiment Analysis routes."""

import json
import os

from flask import Blueprint, jsonify, render_template, request
from openai import OpenAI

from shared import (
    CONFIG,
    SENTIMENT_SYSTEM_PROMPT,
    SENTIMENT_USER_PROMPT,
    compute_sentiment_label,
)

bp = Blueprint("sentiment", __name__, url_prefix="/sentiment")


@bp.route("/")
def page():
    return render_template("sentiment.html")


@bp.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "No text provided"}), 400

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return jsonify({"error": "OPENAI_API_KEY environment variable is not set"}), 500

    model = CONFIG.get("openai_model", "gpt-4o-mini")
    client = OpenAI(api_key=api_key)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SENTIMENT_SYSTEM_PROMPT},
                {"role": "user", "content": SENTIMENT_USER_PROMPT + text},
            ],
            temperature=0,
        )
        raw = response.choices[0].message.content.strip()
        result = json.loads(raw)

        score = float(result["score"])
        score = max(-1.0, min(1.0, score))
        label = compute_sentiment_label(score)

        return jsonify({"score": round(score, 2), "label": label})
    except json.JSONDecodeError:
        return jsonify({"error": "Failed to parse model response"}), 500
    except Exception as exc:
        return jsonify({"error": f"Sentiment analysis failed: {exc}"}), 500
