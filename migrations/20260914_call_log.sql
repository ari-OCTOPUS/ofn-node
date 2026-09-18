-- ============================================================
-- Migration 001 — painting_call_log
-- Date: 2026-09-14
-- Author: Elaheh
--
-- WHY: Ari's first 10 B2B calls produced real outcome data that
-- has nowhere to live. A single "result" column on
-- painting_b2b_accounts would overwrite on the second attempt
-- and lose attempt history, timing data, and the reason a lead
-- was lost. This table is the Interaction entity from §11.
--
-- SAFE: creates a NEW table only. No ALTER on any existing
-- table, so it is NOT blocked by the pending backup verify.
-- Rollback = DROP TABLE painting_call_log.
-- ============================================================

CREATE TABLE IF NOT EXISTS painting_call_log (
    call_id        TEXT PRIMARY KEY,
    tenant_id      TEXT NOT NULL DEFAULT 'lead',
    account_id     TEXT NOT NULL,

    called_at      TEXT NOT NULL,              -- ISO8601 local Sydney
    call_window    TEXT NOT NULL DEFAULT '',   -- 'morning'|'midday'|'afternoon'
    caller         TEXT NOT NULL DEFAULT 'ari',

    channel        TEXT NOT NULL DEFAULT 'mobile'
                   CHECK (channel IN ('mobile','office','email','other')),
    number_called  TEXT NOT NULL DEFAULT '',
    person_called  TEXT NOT NULL DEFAULT '',

    outcome_code   TEXT NOT NULL
                   CHECK (outcome_code IN
                     ('J','JN','M','N','E','Q','WRONG_SEGMENT','OPS_FAIL')),
    outcome_note   TEXT NOT NULL DEFAULT '',   -- what they actually said
    loss_reason    TEXT NOT NULL DEFAULT '',   -- only for JN / Q / WRONG_SEGMENT

    next_action    TEXT NOT NULL DEFAULT '',
    next_action_at TEXT NOT NULL DEFAULT '',   -- ISO8601 date
    recall_after   TEXT NOT NULL DEFAULT '',   -- long-horizon re-contact date

    attempt_no     INTEGER NOT NULL DEFAULT 1,
    created_at     TEXT NOT NULL,

    FOREIGN KEY (account_id) REFERENCES painting_b2b_accounts(account_id)
);

CREATE INDEX IF NOT EXISTS idx_call_log_account
    ON painting_call_log (tenant_id, account_id, called_at DESC);

CREATE INDEX IF NOT EXISTS idx_call_log_next_action
    ON painting_call_log (tenant_id, next_action_at)
    WHERE next_action_at != '';

CREATE INDEX IF NOT EXISTS idx_call_log_recall
    ON painting_call_log (tenant_id, recall_after)
    WHERE recall_after != '';

-- ============================================================
-- VIEW: latest outcome per account — what the digest reads
-- ============================================================

CREATE VIEW IF NOT EXISTS v_account_last_call AS
SELECT
    c.account_id,
    c.tenant_id,
    c.called_at        AS last_called_at,
    c.outcome_code     AS last_outcome,
    c.outcome_note     AS last_note,
    c.next_action,
    c.next_action_at,
    c.recall_after,
    (SELECT COUNT(*) FROM painting_call_log x
      WHERE x.account_id = c.account_id
        AND x.tenant_id  = c.tenant_id) AS attempts
FROM painting_call_log c
WHERE c.called_at = (
    SELECT MAX(x.called_at) FROM painting_call_log x
     WHERE x.account_id = c.account_id
       AND x.tenant_id  = c.tenant_id
);
