# Cycle-7 Painting pointer
run_id: revenue-cycle-7-20260827
task_id: C7-PAINT-PTR
idempotency_key: cycle7:painting:live-truth
INTERNAL_PATH: F:\backup\06-EVIDENCE\OCTOPUS-OWNER-BOARD-2026-08-27\LIVE-TRUTH.md
HOLD_EXTERNAL=yes | no Snapp contact | no send

Claims:
- C6 01-painting-runbook.md sha b0343083 (do not rebuild)
- Live: ofn.service :8792 / lead.master-painting.com /home/ari/.local/share/ofn/painting.sqlite
- Quote: send_lead_quote → outbox lead:quote manual. No customer send.
- Fugu DAY1 inbox empty, not running. tradequote_local not on 138.
- C4 CONTACT_STATUS=UNKNOWN Stay HOLD.

OCTOPUS uses the live ofn lead leg. Do not mint a fifth CRM.
