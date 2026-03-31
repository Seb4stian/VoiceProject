-- ============================================================================
-- VoiceProject — PostgreSQL table definitions
-- Database: VoiceProject
-- Run:  psql -U edcastr -d VoiceProject -f sql/create_tables.sql
-- ============================================================================

CREATE TABLE IF NOT EXISTS users (
    id            SERIAL       PRIMARY KEY,
    username      VARCHAR(50)  UNIQUE NOT NULL,
    email         VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chat_sessions (
    id            SERIAL    PRIMARY KEY,
    user_id       INTEGER   NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    started_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at      TIMESTAMP,
    summary_json  JSONB,
    takeaway      TEXT
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id              SERIAL      PRIMARY KEY,
    session_id      INTEGER     NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role            VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    content         TEXT        NOT NULL,
    sentiment_score REAL,
    sentiment_label VARCHAR(20),
    created_at      TIMESTAMP   DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id   ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id);
