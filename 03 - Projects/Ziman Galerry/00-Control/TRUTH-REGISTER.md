---
type: control
project: ZIMAN
status: active
updated: 2026-07-12
source: FOUNDATION-PHASE2 audit (file inspection session)
---

# TRUTH REGISTER — Ziman (Phase 2 audit)

| # | Claim | Classification | Evidence | Confidence | Action |
|---|---|---|---|---|---|
| T1 | `_ops/legs/ziman_leg.py` exists, propose-only, D4 guard, HARD_GATED set | VERIFIED_FACT | file read 2026-07-12 | 0.98 | none |
| T2 | `wiring.py → make_ziman_leg()` behind `OCTOPUS_WIRE_ZIMAN`, inside `PAPER_FULL_FLAGS` | VERIFIED_FACT | wiring.py read | 0.98 | none |
| T3 | `budgets.yaml → projects.ZIMAN {floor:1}`; ZIMAN in `core_members`; partners Ari 70 / Mother 30 | VERIFIED_FACT | budgets.yaml read | 0.98 | none |
| T4 | telegram_center leg key `ziman`, display "Ziman Galerry", gateway-only, owner allowlist, STOP-TG-CENTER | VERIFIED_FACT | center.py read | 0.95 | none |
| T5 | 3 copies of ziman-agent config (Projects / _code / _launchpad) are **identical** | VERIFIED_FACT | 3× ziman.yaml read, same bytes | 0.95 | pick authority (RQ-01) |
| T6 | Leg resolves agent root by priority: Projects → _code → _launchpad | VERIFIED_FACT | `_resolve_agent_root()` in ziman_leg.py | 0.95 | Projects copy = runtime authority for leg |
| T7 | Capacity 30/week marked "[Measured]" in yaml | STALE_CLAIM / CONFLICT | yaml vs owner-unverified; observed rate ≈6.25/wk (INFERENCE) | 0.5 | fail-closed: treat as UNVERIFIED until owner revalidates |
| T8 | current_inventory: 20 in yaml vs 50 ready products (OWNER_INPUT) | CONFLICT | yaml + STATUS.md | 0.5 | reconcile in inventory snapshot v1 |
| T9 | 50 ready products = 50 SKUs or weekly capacity | FALSE_INFERENCE_BLOCKED | CATALOG.md rules | 0.9 | qualification test QC-01/02 |
| T10 | Recorded sales = 0 | OWNER/FILES | STATUS.md | 0.8 | none |
| T11 | test_ziman_leg.py suite green | REPORTED_NOT_RERUN | file read only — **no shell execution available this session** | 0.6 | owner runs: `python -m pytest _ops/tests/test_ziman_leg.py -q` |
| T12 | ZimanLeg has no send/publish/pay methods | VERIFIED_FACT (static) | code read + test asserts | 0.95 | none |
| T13 | D4 fail-closed: ceiling ≤ 0 → volume campaigns rejected | VERIFIED_FACT (static) | `campaign_check()` code | 0.95 | none |
| T14 | Ziman cannot set heart rate / policy / permissions | VERIFIED_FACT (static) | leg has no pacemaker/setpoint writes; heart_beat separate flag | 0.9 | none |
| T15 | Photo batch at `08 - Assets/Photos/WhatsApp-2026/` | REPORTED (STATUS/CATALOG) | not enumerated this session | 0.6 | read-only index in Phase 2 |
| T16 | **Ziman tests actually RUN GREEN this session (supersedes T11):** `test_ziman_leg` 17/17 + `test_ziman_phase2`+`test_ziman_wiring` 23/23 = **40/40**; smoke OK | VERIFIED_FACT (executed) | shell exec 2026-07-12 (calibration audit) | 0.95 | T11 → VERIFIED. ⚠ run Ziman files individually; whole `_ops/tests/` dir crashes pytest collection (a script-style test `sys.exit()`s on import) |
| T17 | `capacity_fail_closed()`/`anti_misread_guard`/`compute_atp` (ziman_phase2) imported ONLY by their own test — UNWIRED from live D4 gate | VERIFIED_FACT (static+grep) | `ziman_leg.py` has no `ziman_phase2` import; `campaign_check` uses raw yaml 30 | 0.95 | CF-06 fix (gated) |
| T18 | 4th code tree `_launchpad/second-brain-live/` has real outward SEND (Telegram+WhatsApp) + live `.env` + committed owner PII + DeepSeek key mislabeled Anthropic | VERIFIED_FACT (static) | audit 2026-07-12 (`.env` not opened; git-ignored) | 0.9 | CF-08/CF-09 (owner verdict) |
