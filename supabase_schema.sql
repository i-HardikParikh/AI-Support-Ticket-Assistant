-- ─────────────────────────────────────────────────────────
--  AI Support Ticket Assistant — Supabase Schema
--  Run this once in your Supabase SQL editor to create tables
-- ─────────────────────────────────────────────────────────

-- 1. Tickets table — one row per support ticket processed
CREATE TABLE IF NOT EXISTS tickets (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    raw_text            TEXT NOT NULL,
    sender_email        TEXT,
    sender_name         TEXT,
    source              TEXT DEFAULT 'api',         -- api | email | webhook

    -- AI output
    category            TEXT NOT NULL,
    draft_reply         TEXT NOT NULL,
    escalation          BOOLEAN NOT NULL DEFAULT false,
    reason              TEXT NOT NULL,
    confidence          FLOAT NOT NULL,

    -- Status tracking
    status              TEXT NOT NULL DEFAULT 'pending',  -- pending | resolved | escalated | ai_failed

    -- Agent actions (filled after feedback)
    agent_action        TEXT,                        -- approved | edited | escalated | dismissed
    corrected_category  TEXT,                        -- if agent corrected the category
    edited_reply        TEXT,                        -- if agent edited the draft
    agent_note          TEXT,                        -- any internal note from agent

    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at         TIMESTAMPTZ
);

-- 2. Feedback table — one row per agent action (for detailed audit trail)
CREATE TABLE IF NOT EXISTS feedback (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id           UUID NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    action              TEXT NOT NULL,               -- approved | edited | escalated | dismissed
    corrected_category  TEXT,
    edited_reply        TEXT,
    agent_note          TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 3. Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_tickets_status      ON tickets(status);
CREATE INDEX IF NOT EXISTS idx_tickets_category    ON tickets(category);
CREATE INDEX IF NOT EXISTS idx_tickets_created_at  ON tickets(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tickets_escalation  ON tickets(escalation);
CREATE INDEX IF NOT EXISTS idx_feedback_ticket_id  ON feedback(ticket_id);

-- 4. Enable Row Level Security (optional but recommended for production)
-- ALTER TABLE tickets ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE feedback ENABLE ROW LEVEL SECURITY;

-- 5. Sample data to test the dashboard immediately
INSERT INTO tickets (raw_text, category, draft_reply, escalation, reason, confidence, status, source)
VALUES
  ('I was charged twice this month, please refund.', 'billing', 'We apologise for the duplicate charge and have raised a refund request.', false, 'Standard billing dispute, no legal language.', 0.93, 'resolved', 'api'),
  ('The dashboard is broken since this morning, nothing loads.', 'bug report', 'We are aware of this issue and our team is working on a fix urgently.', true, 'Production system affected, team blocking issue.', 0.91, 'escalated', 'email'),
  ('Can you add CSV export to the analytics page?', 'feature request', 'Thank you for the suggestion! We have logged this for the product team.', false, 'Feature request, no urgency.', 0.88, 'resolved', 'api'),
  ('I cannot log into my account, password reset is not working.', 'account issue', 'We have manually triggered a password reset for your account.', false, 'Standard account access issue.', 0.90, 'pending', 'api'),
  ('We are about to launch and your API is down. Fix this NOW.', 'bug report', 'We are treating this as a critical incident and escalating immediately.', true, 'Production launch blocked, high urgency language.', 0.97, 'escalated', 'email');

  