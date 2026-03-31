-- ============================================================================
-- User-related queries
-- ============================================================================

-- name: create_user
INSERT INTO users (username, email, password_hash)
VALUES (%s, %s, %s)
RETURNING id;

-- name: get_user_by_username
SELECT id, username, email, password_hash
FROM users
WHERE username = %s;

-- name: get_user_by_id
SELECT id, username, email
FROM users
WHERE id = %s;

-- name: check_username_exists
SELECT EXISTS(SELECT 1 FROM users WHERE username = %s);

-- name: check_email_exists
SELECT EXISTS(SELECT 1 FROM users WHERE email = %s);
