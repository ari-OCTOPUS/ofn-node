# PIPELINE-DESIGN — AIRTASKER-WATCH (Phases 1–3, design only; nothing wired)

GOV_VERSION=V8 · LADDER=L2 · lane: AIRTASKER-WATCH-20260908 · 2026-09-08

## Phase 1 — digest pipeline (parse → leads → card)

```
owner's Gmail ──(Airtasker task-alert email)──▶ imap_listener cycle (board138, 15 min)
   │
   ├─ classify(): NEW branch BEFORE the noise fall-through:
   │     if is_airtasker_sender(sender): kind="alert" → airtasker_alert_parser
   │     (existing behaviour for every other unknown sender unchanged)
   │
   ├─ parse_alert_message() → TaskRef list  [module written, 8/8 tests green]
   │
   ├─ insert → painting.sqlite (source_id="airtasker",
   │            unique key = task_id/task url; re-encounter = no-op dedupe)
   │
   ├─ direction gate: supply_risk=True rows NEVER become lead cards
   │            (PAINT-L5-001 wrong_recipient kill metric)
   │
   └─ owner_notify card → Telegram outbox WITH receipt:
         "🎨 <title> | <budget> | <location> | <score-basis> | <url>"
         missing fields render "—" (never guessed — parser contract)
```

Not wired yet, by design: touching `imap_listener.py`/ofn-node is outside this
lane's write scope. Wiring = one owner GO in a follow-up lane with pre-image
receipt per GOV-V7 protection 3. **No telegram send will be triggered by this
lane.**

## Phase 2 — draft pen (design sketch)

- Trigger: owner replies "draft" to a task card (owner-originated; nothing
  autonomous).
- Path: task fields + owner profile + `rate_card_builder.py` output →
  board138 local model (`qwen2.5:7b` already local; llama :8081 alt) →
  draft text → Telegram to owner ONLY. Owner edits & pastes into Airtasker
  manually. Auto-POST/offer: never (red line).
- Win-probability scoring: deferred until ≥30 owner decisions on real cards
  (UNDERPOWERED); starts as transparent rule-based rank (budget present,
  location match, recency, supply_risk=False).

## Phase 3 — rhythm histogram (design sketch)

- After ≥2 weeks of alerts: histogram of posted times (posted_at only when
  literally observed; else alert-arrival time as a *lower bound*, labelled as
  such) → suggest 2 daily check windows for the owner. Report-only artefact.

## Latency metric (the lane's goal)

`posted→seen` = owner-seen timestamp (TG card open, manual) − task posted time
(observed, not inferred). All values unverified until instrumented; n≥30
before quoting anything.
