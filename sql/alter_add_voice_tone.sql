-- ============================================================================
-- Migration: Add voice_tone columns to chat_messages
-- Run:  psql -U edcastr -d VoiceProject -f sql/alter_add_voice_tone.sql
-- ============================================================================

ALTER TABLE chat_messages
    ADD COLUMN IF NOT EXISTS voice_tone       VARCHAR(30),
    ADD COLUMN IF NOT EXISTS voice_tone_score REAL;
