"""Authentication routes: login, register, logout."""

import re
from functools import wraps

from flask import Blueprint, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from db import create_user, email_exists, get_user_by_username, username_exists

bp = Blueprint("auth", __name__, url_prefix="/auth")


def login_required(f):
    """Decorator that redirects to login when the user is not authenticated."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""

    if not username or not password:
        return render_template("login.html", error="Please fill in all fields.")

    user = get_user_by_username(username)
    if user is None or not check_password_hash(user["password_hash"], password):
        return render_template("login.html", error="Invalid username or password.")

    session["user_id"] = user["id"]
    session["username"] = user["username"]
    return redirect(url_for("recorder.index"))


@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    username = (request.form.get("username") or "").strip()
    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""
    confirm = request.form.get("confirm") or ""

    if not username or not email or not password:
        return render_template("register.html", error="Please fill in all fields.")

    if password != confirm:
        return render_template("register.html", error="Passwords do not match.")

    if len(password) < 6:
        return render_template("register.html", error="Password must be at least 6 characters.")

    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        return render_template(
            "register.html",
            error="Username can only contain letters, numbers, and underscores.",
        )

    if username_exists(username):
        return render_template("register.html", error="Username already taken.")

    if email_exists(email):
        return render_template("register.html", error="Email already registered.")

    pw_hash = generate_password_hash(password)
    create_user(username, email, pw_hash)

    return redirect(url_for("auth.login", registered="1"))


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
