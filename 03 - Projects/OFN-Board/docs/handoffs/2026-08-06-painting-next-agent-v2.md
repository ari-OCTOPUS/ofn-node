# Handoff v2 — Painting Next Agent

Start from Obsidian vault /home/ari/ofn.
Read v2 mega prompt and checklist before code.

Files:
- docs/prompts/PAINTING-NEXT-AGENT-MEGAPROMPT-v2.md
- docs/operations/PAINTING-PHONE-QUOTE-CHECKLIST-v2.md

Next: verify Telegram access, then test lead to quote draft.
Safety: keep OFN_WIRE_OUTBOUND=0 until canary approval.

## Update 2026-08-06 (session 2) — gap #1 closed + boot flag cleared

- **Gap #1 done.** Leads now use `kernel/painting_math.lead_priority()` (was
  the dead keyword heuristic). New `painting_leads.score_json` column carries
  the model payload (same shape as B2B/tenders); `update_lead` recomputes on
  relevant-field change; reads prefer stored `score_json`, fall back for old
  rows. Migration is in `lead_store.MIGRATIONS` AND registered in `boot.py`
  (that second wiring cleared a pre-existing `schema:painting(critical)` flag
  that was forcing SAFE MODE — node now boots `boot OK 27/27`, NORMAL).
- Tests: +4 in `test_painting_store.py`; suite 1500 passed + 5 skip; restart
  + healthz verified on the wire.
- **Weights are starting heuristics, not business truth** — retune once real
  Armin intake data exists.
- **Still blocked on phone access:** ~~`OFN_BOT_TOKEN_LEAD` and
  `OFN_BOT_TOKEN_OWNER` are NOT_SET → no Telegram session can be issued.~~
  **RESOLVED same session:** Armin set both tokens. Verified live against
  Telegram `getMe` (`ok=true`). Service restarted, `boot OK 27/27`,
  allowlists intact (owner=1, lead=1). Remaining: the **actual phone login
  test must be done by Armin from his device** (a real Telegram launch) —
  only he can do it. Next agent: wait for his phone-test result, or if he
  reports success, proceed to creating a test lead and the intake flow.
- Drift note: `OFN_WIRE_EMAIL`/`OFN_WIRE_PUBLISH` are ON in node.env but not
  read by Python; harmless today (outbox + store-status enforce safety).
- Out of scope this session: pricing state machine, structured painting
  fields (property_type, interior_exterior, surface_condition, etc.), quote
  draft template, missing-info engine, lead.html Flight-Deck UI, lead outbox.
  Proposed as the next session, still gated behind WIRE_OUTBOUND=0 + owner OK.
