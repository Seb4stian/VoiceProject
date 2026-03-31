"""Entry point — creates the Flask app and registers all route blueprints."""

import os

from dotenv import load_dotenv
from flask import Flask, redirect, request, session, url_for

load_dotenv()


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "voiceproject-dev-secret-key")

    from routes.auth import bp as auth_bp
    from routes.recorder import bp as recorder_bp
    from routes.stt import bp as stt_bp
    from routes.tts import bp as tts_bp
    from routes.sentiment import bp as sentiment_bp
    from routes.chat import bp as chat_bp
    from routes.voice_chat import bp as voice_chat_bp
    from routes.about import bp as about_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(recorder_bp)
    app.register_blueprint(stt_bp)
    app.register_blueprint(tts_bp)
    app.register_blueprint(sentiment_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(voice_chat_bp)
    app.register_blueprint(about_bp)

    @app.before_request
    def require_login():
        if request.endpoint and (
            request.endpoint.startswith("auth.") or request.endpoint == "static"
        ):
            return
        if "user_id" not in session:
            return redirect(url_for("auth.login"))

    @app.context_processor
    def inject_user():
        return {"current_user": session.get("username")}

    # Initialize database tables on startup
    from db import init_db
    try:
        init_db()
    except Exception as e:
        print(f"Warning: Could not initialize database: {e}")

    return app


if __name__ == "__main__":
    app = create_app()
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug, port=5000)
