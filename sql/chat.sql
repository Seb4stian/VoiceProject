-- ============================================================================
-- Chat session and message queries
-- ============================================================================

-- name: create_session
INSERT INTO chat_sessions (user_id)
VALUES (%s)
RETURNING id;

-- name: end_session
UPDATE chat_sessions
SET ended_at     = CURRENT_TIMESTAMP,
    summary_json = %s,
    takeaway     = %s
WHERE id = %s AND user_id = %s;

-- name: save_message
INSERT INTO chat_messages (session_id, role, content, sentiment_score, sentiment_label)
VALUES (%s, %s, %s, %s, %s);

-- name: get_session_messages
SELECT role, content, sentiment_score, sentiment_label, created_at
FROM chat_messages
WHERE session_id = %s
ORDER BY created_at;

-- name: get_user_takeaways
SELECT cs.takeaway, cs.started_at
FROM chat_sessions cs
WHERE cs.user_id = %s
  AND cs.takeaway IS NOT NULL
  AND cs.ended_at IS NOT NULL
ORDER BY cs.started_at DESC
LIMIT 10;

-- name: get_user_sessions
SELECT id, started_at, ended_at, summary_json, takeaway
FROM chat_sessions
WHERE user_id = %s
ORDER BY started_at DESC;

-- name: get_session_timeline
SELECT id,
       started_at,
       (summary_json->>'overall_sentiment')::REAL AS sentiment_score
FROM chat_sessions
WHERE user_id = %s
  AND ended_at IS NOT NULL
  AND summary_json IS NOT NULL
ORDER BY started_at ASC;
