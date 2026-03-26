import os
import uuid
from flask import Flask, jsonify, render_template, request, send_from_directory

app = Flask(__name__)

RECORDINGS_DIR = os.path.join(os.path.dirname(__file__), "recordings")
os.makedirs(RECORDINGS_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {"webm", "ogg", "wav", "mp4"}


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


if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug, port=5000)
