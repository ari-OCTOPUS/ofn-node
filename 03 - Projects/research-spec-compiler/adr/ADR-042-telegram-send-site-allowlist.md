# ADR-042 — Telegram send-site allowlist (Phase 0 first)

- **Status:** PROPOSED — Phase 0 instrumented 2026-08-13; allowlist not yet approved
- **Date:** 2026-08-13
- **Preserves:** existing `tg_send_log` receipts · PolicyGate talk path · no second send primitive
- **Does not:** deny any site yet · edit `telegram_center/center.py` (worklock)

## Problem

Static audit `python _ops/tg_send_audit.py --json` (2026-08-13):

| field | value | meaning in `tg_send_audit.py` |
|---|---|---|
| total_sites | 100 | AST Call of `send` / `send_text` under `_ops` (tests skipped) |
| certain | 0 | **literal integer `topic_id=` only** (`test_tg_send_audit.py:24-26`) |
| conditional | 82 | runtime expression (may be None live) |
| absent | 2 | no topic_id |
| dm | 16 | owner DM routing |
| proven_rate | 0.0 | `certain / total` — **not** “no message ever left the host” |

`proven_rate=0.0` is therefore a **topic_id static-proof** gap, not a proof that zero sites fire. Live volume already goes to `_ops/state/tg-send-log.jsonl` (`OCTOPUS_TG_SEND_LOG=1`, `tg_api.py:516-519`, `approval_channel.py:_send_receipt`) **without caller file:line**.

Allowlisting or denying the 84 conditional+absent sites **before** knowing which of them run is wasted work: denying dead code does nothing.

## Decision

### Phase 0 (before allowlist) — ACCEPTED to implement now

```text
Phase 0 (before allowlist):
  From each of the 100 sites, know whether it was *called*.
  Append-only log (no behaviour change).
  Collect ≥48h of natural runtime.
  Only sites that actually fire enter the allowlist table.
  The rest of the 82 conditional + 2 absent are DEAD_CODE_CANDIDATE,
  not "denied".
```

**Implementation (Improve, don't rewrite 84 call sites):**

Both live senders already choke here:

- `_ops/telegram_center/tg_api.py` `TgClient.send`
- `_ops/budget/approval_channel.py` `TelegramApprovalChannel.send_text`

Phase 0 records `inspect.stack()` at those two entries (`tg_site_fire_log.record_call`). Catalog of the 84 watchlist rows: `_ops/tg_site_fire_catalog.json`. Log: `state/tg-site-fire.jsonl`. Flag: `OCTOPUS_TG_SITE_FIRE_LOG=1` in `OCTOPUS-flags.cmd`.

84 inline patches in `center.py` were **not** applied (HANDOFF worklock).

### Phase 1 (after 48h) — not started

Build allowlist from fired watchlist keys only. Unfired watchlist → `DEAD_CODE_CANDIDATE`. Do not mark them denied.

## Rollback

`set OCTOPUS_TG_SITE_FIRE_LOG=0` + restart. Send paths byte-identical aside from the skipped `record_call`.

## Non-claims

No claim that proven_rate measures delivery. No deny of any send site in this ADR.

## Evidence

- Audit JSON: desktop `octopus_audit_report/telegram_send_sites.json`
- Tests (unregistered): `_ops/tests/test_tg_site_fire_log.py` PASS 2026-08-13
- Report later: `python _ops/scripts/tg_site_fire_report.py`
