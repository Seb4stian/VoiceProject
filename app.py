"""Entry point — creates the Flask app and registers all route blueprints."""

import os

from dotenv import load_dotenv
from flask import Flask

load_dotenv()


def create_app() -> Flask:
    app = Flask(__name__)

    from routes.recorder import bp as recorder_bp
    from routes.stt import bp as stt_bp
    from routes.tts import bp as tts_bp
    from routes.sentiment import bp as sentiment_bp
    from routes.chat import bp as chat_bp
    from routes.voice_chat import bp as voice_chat_bp

    app.register_blueprint(recorder_bp)
    app.register_blueprint(stt_bp)
    app.register_blueprint(tts_bp)
    app.register_blueprint(sentiment_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(voice_chat_bp)

    return app


if __name__ == "__main__":
    app = create_app()
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug, port=5000)
