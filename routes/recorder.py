"""Recording routes: upload, list, serve, and home page."""

import os
import uuid

from flask import Blueprint, jsonify, render_template, request, send_from_directory, session

from shared import ALLOWED_EXTENSIONS, allowed_file, get_user_recordings_dir, safe_filename

bp = Blueprint("recorder", __name__)


@bp.route("/")
def index():
    return render_template("index.html")


@bp.route("/upload", methods=["POST"])
def upload():
    audio = request.files.get("audio")
    if audio is None:
        return jsonify({"error": "No audio file provided"}), 400

    user_id = session.get("user_id")
    rec_dir = get_user_recordings_dir(user_id)

    ext = audio.filename.rsplit(".", 1)[-1].lower() if "." in audio.filename else "webm"
    if ext not in ALLOWED_EXTENSIONS:
        ext = "webm"

    filename = f"{uuid.uuid4().hex}.{ext}"
    audio.save(os.path.join(rec_dir, filename))
    return jsonify({"filename": filename}), 201


@bp.route("/recordings", methods=["GET"])
def list_recordings():
    user_id = session.get("user_id")
    rec_dir = get_user_recordings_dir(user_id)
    if not os.path.isdir(rec_dir):
        return jsonify([])
    files = [
        f for f in os.listdir(rec_dir)
        if not f.startswith(".") and allowed_file(f)
    ]
    files.sort(key=lambda f: os.path.getmtime(os.path.join(rec_dir, f)), reverse=True)
    return jsonify(files)


@bp.route("/recordings/<path:filename>", methods=["GET"])
def serve_recording(filename: str):
    user_id = session.get("user_id")
    rec_dir = get_user_recordings_dir(user_id)
    safe = safe_filename(filename)
    if not allowed_file(safe):
        return jsonify({"error": "File type not allowed"}), 400
    if not os.path.isfile(os.path.join(rec_dir, safe)):
        return jsonify({"error": "File not found"}), 404
    return send_from_directory(rec_dir, safe)


@bp.route("/recordings/<path:filename>", methods=["DELETE"])
def delete_recording(filename: str):
    user_id = session.get("user_id")
    rec_dir = get_user_recordings_dir(user_id)
    safe = safe_filename(filename)
    filepath = os.path.join(rec_dir, safe)
    if not os.path.isfile(filepath):
        return jsonify({"error": "File not found"}), 404
    os.remove(filepath)
    return jsonify({"deleted": safe}), 200
