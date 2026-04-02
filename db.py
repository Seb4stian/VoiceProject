"""Database connection and query functions for PostgreSQL."""

import os

import psycopg2
from psycopg2.extras import RealDictCursor

from shared import CONFIG

_SQL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sql")


def _load_queries(filename: str) -> dict[str, str]:
    """Parse named SQL queries from a file (marked with ``-- name: xxx``)."""
    path = os.path.join(_SQL_DIR, filename)
    with open(path) as f:
        text = f.read()

    queries: dict[str, str] = {}
    current_name: str | None = None
    current_lines: list[str] = []

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("-- name:"):
            if current_name:
                queries[current_name] = "\n".join(current_lines).strip()
            current_name = stripped.replace("-- name:", "").strip()
            current_lines = []
        elif current_name is not None:
            current_lines.append(line)

    if current_name:
        queries[current_name] = "\n".join(current_lines).strip()

    return queries


_user_queries = _load_queries("users.sql")
_chat_queries = _load_queries("chat.sql")


# ── Connection ────────────────────────────────────────────────────────────────


def get_connection():
    """Return a new PostgreSQL connection using config.json + .env settings."""
    db_cfg = CONFIG["database"]
    return psycopg2.connect(
        host=db_cfg["host"],
        port=db_cfg["port"],
        dbname=db_cfg["name"],
        user=db_cfg["user"],
        password=os.environ.get("DB_PASSWORD", ""),
    )


def init_db():
    """Run create_tables.sql to ensure all tables exist."""
    ddl_path = os.path.join(_SQL_DIR, "create_tables.sql")
    with open(ddl_path) as f:
        ddl = f.read()
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(ddl)
        conn.commit()
    finally:
        conn.close()


# ── User queries ──────────────────────────────────────────────────────────────


def create_user(username: str, email: str, password_hash: str) -> int:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(_user_queries["create_user"], (username, email, password_hash))
            user_id = cur.fetchone()[0]
        conn.commit()
        return user_id
    finally:
        conn.close()


def get_user_by_username(username: str) -> dict | None:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(_user_queries["get_user_by_username"], (username,))
            return cur.fetchone()
    finally:
        conn.close()


def get_user_by_id(user_id: int) -> dict | None:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(_user_queries["get_user_by_id"], (user_id,))
            return cur.fetchone()
    finally:
        conn.close()


def username_exists(username: str) -> bool:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(_user_queries["check_username_exists"], (username,))
            return cur.fetchone()[0]
    finally:
        conn.close()


def email_exists(email: str) -> bool:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(_user_queries["check_email_exists"], (email,))
            return cur.fetchone()[0]
    finally:
        conn.close()


# ── Chat queries ──────────────────────────────────────────────────────────────


def create_chat_session(user_id: int) -> int:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(_chat_queries["create_session"], (user_id,))
            session_id = cur.fetchone()[0]
        conn.commit()
        return session_id
    finally:
        conn.close()


def end_chat_session(session_id: int, user_id: int, summary_json: str, takeaway: str):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                _chat_queries["end_session"],
                (summary_json, takeaway, session_id, user_id),
            )
        conn.commit()
    finally:
        conn.close()


def save_chat_message(
    session_id: int,
    role: str,
    content: str,
    sentiment_score: float | None = None,
    sentiment_label: str | None = None,
    voice_tone: str | None = None,
    voice_tone_score: float | None = None,
):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                _chat_queries["save_message"],
                (session_id, role, content, sentiment_score, sentiment_label,
                 voice_tone, voice_tone_score),
            )
        conn.commit()
    finally:
        conn.close()


def get_session_messages(session_id: int) -> list[dict]:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(_chat_queries["get_session_messages"], (session_id,))
            return cur.fetchall()
    finally:
        conn.close()


def get_user_takeaways(user_id: int) -> list[dict]:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(_chat_queries["get_user_takeaways"], (user_id,))
            return cur.fetchall()
    finally:
        conn.close()


def get_user_sessions(user_id: int) -> list[dict]:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(_chat_queries["get_user_sessions"], (user_id,))
            return cur.fetchall()
    finally:
        conn.close()


def get_session_timeline(user_id: int) -> list[dict]:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(_chat_queries["get_session_timeline"], (user_id,))
            return cur.fetchall()
    finally:
        conn.close()
