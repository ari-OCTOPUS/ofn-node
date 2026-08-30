# OCTOPUS MiniApp Confirm Audit — 2026-08-24

## Verdict: **PARTIAL**

Approvals sometimes hit **real durable code**, but they do **not** reach real effectors for proposal confirms. Stalled-card پذیرش from the MiniApp lifecycle list is currently **non-functional** because the decide id is stripped.

## Top findings

1. **Undefined titles (راکد list)**  
   - UI (`miniapp/app.js` `renderLifecycle`) renders `c.rfc_id` as the card title line.  
   - API (`miniapp_state.get_lifecycle_state` → `_lifecycle_public_stalled_rows`, 2026-08-06) intentionally returns only `{created_ts, age_days}` (no `rfc_id`, no summary).  
   - Result: every stalled row title becomes the literal string `undefined`. State has **39** `SUBMITTED` cards in `pending-cards.json` (ages ~8–12+ days) matching the screenshot class.

2. **تأیید (`proposal.approve`) reaches DB, not effector**  
   - Path: `POST /api/actions` → `OpsActionEngine` → `decide_proposal` → `INSERT ... event_type='owner-decision'`.  
   - Snapshot `outcomes.db`: **18** owner-decisions; **0** have any later event (`effects_after=0`).  
   - Targets present: `P-091b88a78346` and `P-ad115622f2ab` (leg `ziman-gallery`) both `delivered` then `owner-decision/approved` on 2026-08-23 UTC; no follow-on effector row.  
   - UI text «ثبت شد؛ هنوز هیچ اثری پشت آن ثبت نشده» is therefore **correct**, not a display bug. Code comments state `owner-decision` has one writer and zero readers.

3. **پذیرش (`rfc.approve`) backend exists; MiniApp cannot feed it**  
   - Handler writes via `pending_card_recovery.persist_rfc_verdict`; doctor/PCR claim→apply→ack path exists.  
   - Because `rfc_id` is omitted from `/api/lifecycle`, buttons post `rfc_id="undefined"` → blocked/not found. So lifecycle پذیرش does not reach real apply.

4. **Decision nonce ledger is shadow-only**  
   - `miniapp_decision_ledger.py`: «No live route imports this module yet.»  
   - `_shadow_consume_decision_nonce` default-off; live `/api/actions` does not call it.

## Exact next fix

1. Fix stalled list contract: return an actionable opaque handle (or carefully allowlisted id) + short label; stop rendering missing `rfc_id` as `undefined`; disable buttons without handle.  
2. Add a real consumer for `owner-decision` → durable outbox/effector for the owning leg (start with ziman-gallery), then emit a follow-on outcomes event so the MiniApp «اثر» line becomes true.  
3. Leave decision-nonce as canary until shadow-verified; do not confuse ledger consume with effector apply.

## Constraints

No live Telegram send. No invented runtime. No secrets in this pack (tokens/nonces from card store not exported).
