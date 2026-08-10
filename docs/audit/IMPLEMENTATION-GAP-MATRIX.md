# Implementation Gap Matrix

> Verified against code 2026-08-08. Items marked ✅ were previously listed
> as MISSING and are now fully implemented and tested.

| Area | Status (2026-08-08) | Evidence |
|---|---|---|
| Lead CRM | ✅ FIXED — full scoring wired | `lead_store.py:500` calls `lead_priority()` from `painting_math.py:59`; tests in `test_painting_store.py` |
| Digital marketing panel | ✅ FIXED — GET + POST run | `http_api.py:667` (GET marketing), `http_api.py:1008` (POST run) |
| B2B account engine | ✅ FIXED — two models (strata/fitout) | `lead_store.py:156-179` (table), `painting_math.py:89-111` (`b2b_account_score`); submit blocked by design |
| Tender radar | ✅ FIXED — score + checklist, no submit | `lead_store.py:193-204` (table), `painting_math.py:114-133` (`tender_score`); auto-submit blocked `lead_store.py:924` |
| Vendor onboarding | ✅ FIXED — readiness pack fields | `lead_store.py:953-979` (`create_vendor_application`); submit blocked `lead_store.py:961` |
| Instagram/GBP publish | ⚠️ STILL ABSENT — no adapter exists | Only 3 platform adapters exist: `bluesky.py`, `email_ses.py`, `telegram_channel.py` (all dry-run behind OwnerRelease). Instagram/GBP are "planned" rows in the source registry only — **no read-only audit adapter, no OAuth, nothing.** Previous doc said "present but disconnected" which was incorrect. |
| Fugu Ultra deep tasks | ✅ FIXED — gated by owner approval | `run.py:285-289` (wiring), `routing.py:168-172` (deep needs owner approval) |
| Official connector health | ⚠️ STILL OPEN — only /healthz exists | `http_api.py:316` returns only `{"ok": True}`. No per-connector health endpoint. |
| Advanced GNN/RL | ✅ CORRECT — rule engine in use | No GNN/RL/PPO/DQN in codebase (grep confirmed). Rule engine: `painting_math.py` + `routing.py`. |
| Kill switch | ✅ NEW (2026-08-08) — wired and tested | `node.py:engage_kill/release_kill`, `http_api.py` 2 endpoints, 23 tests in `test_kill_switch.py` |
| Live board metrics | ✅ NEW (2026-08-08) — sysmetrics + endpoint | `ofn/adapters/sysmetrics.py`, `GET /api/v1/owner/metrics` |
| Service-failure alert | ✅ NEW (2026-08-08) — log + opt-in Telegram | `ofn/adapters/alert.py`, `deploy/systemd/ofn-alert.service` (OnFailure on ofn.service) |

## Connector / observability (verified 2026-08-10, after P0+P1)

| Area | Status (2026-08-10) | Evidence |
|---|---|---|
| Durable webhook inbox | ✅ IMPLEMENTED — hash-only storage | `marketing_inbox.py` stores `body_sha256` + `body_size`, never raw payloads (P0 finding 4) |
| Inbox state machine | ✅ IMPLEMENTED — claim/processing/held | `marketing_inbox.py: claim_next`, `mark_processed`, `recover_stale` (P1 finding 28) |
| Dry-run processor | ✅ IMPLEMENTED — shape-validate only | `inbox_processor.py: process_inbox_once`, no outbound (P1 finding 39) |
| Webhook tenant cross-check | ✅ IMPLEMENTED — path vs Host | `http_api.py` webhook route: path tenant + host mismatch → 403 (P1 finding 9) |
| Replay digest | ✅ FIXED — SHA-256 of whole initData | `http_api.py:_auth` no longer uses `[-64:]` suffix (P1 finding 11) |
| Connector metrics | ✅ WIRED — per-connector counters | `node.py:handle_webhook` records; `owner_observability` exposes snapshot (P1 findings 42, 83) |
| Owner observability endpoint | ✅ NEW — inbox + metrics + gaps | `GET /api/v1/owner/observability`, owner-only, no-store (P1 finding 84) |
| Partner precondition gate | ✅ CLOSED by default | `config.py` default closed gates include `partner_precondition` (P0 finding 3) |
| Kill switch on all enqueues | ✅ FIXED — `_gate_enqueue` helper | All direct enqueue paths check kill first (P0 finding 2, 6) |
| Studio chat scrub | ✅ FIXED — PII before persist | `node.py:studio_assistant_chat` scrubs user + assistant text (P1 finding 12) |
| Backup media verification | ✅ FIXED — count + bytes | `backup.py:verify_backup` compares media tree against manifest (P1 finding 22) |
| memory.sqlite backup | ✅ ADDED (Ari approved) | `backup_job.py` includes `cfg.memory_path` (P1 finding 53) |
