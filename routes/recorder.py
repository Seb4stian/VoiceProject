"""Recording routes: upload, list, serve, and home page."""

import os
import uuid

from flask import Blueprint, jsonify, render_template, request, send_from_directory

from shared import ALLOWED_EXTENSIONS, RECORDINGS_DIR, allowed_file, safe_filename

bp = Blueprint("recorder", __name__)


@bp.route("/")
def index():
    return render_template("index.html")


@bp.route("/upload", methods=["POST"])
def upload():
    audio = request.files.get("audio")
    if audio is None:
        return jsonify({"error": "No audio file provided"}), 400

    ext = audio.filename.rsplit(".", 1)[-1].lower() if "." in audio.filename else "webm"
    if ext not in ALLOWED_EXTENSIONS:
        ext = "webm"

    filename = f"{uuid.uuid4().hex}.{ext}"
    audio.save(os.path.join(RECORDINGS_DIR, filename))
    return jsonify({"filename": filename}), 201


@bp.route("/recordings", methods=["GET"])
def list_recordings():
    files = [
        f for f in os.listdir(RECORDINGS_DIR)
        if not f.startswith(".") and allowed_file(f)
    ]
    files.sort(key=lambda f: os.path.getmtime(os.path.join(RECORDINGS_DIR, f)), reverse=True)
    return jsonify(files)


@bp.route("/recordings/<path:filename>", methods=["GET"])
def serve_recording(filename: str):
    safe = safe_filename(filename)
    if not allowed_file(safe):
        return jsonify({"error": "File type not allowed"}), 400
    if not os.path.isfile(os.path.join(RECORDINGS_DIR, safe)):
        return jsonify({"error": "File not found"}), 404
    return send_from_directory(RECORDINGS_DIR, safe)
