# Safety Invariants

> All 10 verified against code 2026-08-08. No violations found.

1. ✅ No external publication, email, SMS, DM, quote send, tender submit, portal signup, fee payment, or terms acceptance without owner approval. — `gates.py:54-57` (kill switch first), `release_switch.py:82-117`, `lead_store.py:924,961` (tender/vendor submit blocked).
2. ✅ Public contact data is research evidence, not marketing consent. — `consent.py:199-238`, `painting_math.py:83,109` (high risk → RESEARCH_ONLY). Sources default `read_only_first`.
3. ✅ Unknown consent, unknown token health, missing policy result, or closed kill switch means BLOCK. — `consent.py:220-226`, `release_switch.py:82`, `http_api.py:266-270` (empty allowlist = nobody).
4. ⚠️ Every mutation writes an audit/ledger event or returns failure. — Holds in practice but is **caller-discipline**, not an enforced global assert. Every current caller does write, but there is no mechanism preventing a future caller from forgetting.
5. ✅ Every external side-effect needs an idempotency key before execution. — `outbox.py:99`, `base.py:24`, `release_switch.py:114-115`.
6. ✅ Fugu Ultra is reserved for explicitly classified deep tasks; never for routine panel reads or polling. — `routing.py:168-172`.
7. ✅ Raw secrets, raw private PII, exact addresses, bank details, and raw customer media do not enter prompts, logs, tests, or owner-safe summaries. — `scrub.py:32-53` (email/secret/card/phone/ABN/TFN/IP). Known limitation: cannot scrub names/addresses (documented at `scrub.py:14-21`).
8. ✅ B2B vendor/tender workflows remain draft/checklist/research until owner performs final portal action. — `lead_store.py:924,961`.
9. ✅ No scraping of Google Maps/GBP or protected portal data. — No scraping code exists (grep confirmed).
10. ✅ Tests must pass before service restart or enabling any new unit/timer. — 1553 passed, 5 skipped (2026-08-08). Service restarted only after green.
