---
type: control
project: "[[03 - Projects/Ziman Galerry/PROJECT]]"
status: active
updated: 2026-07-12
---

# STATUS — Ziman Galerry (OLP-1 limb)

## Phase
`foundation / market validation` — zero outward execution

## Live wiring (OCTOPUS)
| Layer | Status | Evidence |
|---|---|---|
| Organ budget | **active** | `budgets.yaml` → `ZIMAN` floor AU$1 |
| Leg code | **built** | `_ops/legs/ziman_leg.py` |
| Wiring flag | **paper-full** | `OCTOPUS_WIRE_ZIMAN` in `wiring.PAPER_FULL_FLAGS` |
| Telegram center | **named** | leg key `ziman` in `telegram_center` |
| Heart / organism | **wired in code; restart required to load** | `organism.py` → `make_ziman_leg()` → `ziman_beat(doctor=...)` → `ziman_biology` → `ORGANISM-STATE.ziman`; heart read-only, nerves advisory, doctor RFC-only |
| Local agent | **built** | `ziman-agent/worker.py` (drafts only) |
| Control-brain | **built** | `control-brain/` RBAC + start/stop |

## Hard gates (locked)
- propose-only: no publish / send / DM / spend
- D4 capacity-first
- C4 local-only (perishable)
- no auto-post, no auto-spend

## Numbers (truth register)
| Claim | Class | Value |
|---|---|---|
| Ready physical products | OWNER_INPUT | 50 |
| Capacity ceiling | CONFLICT / UNVERIFIED vs Measured in yaml | 30/week in `ziman.yaml` — confirm with production owner |
| Current inventory hint | Measured in yaml | 20 |
| Recorded sales | OWNER/files | 0 |

## Phase 2 artifacts (2026-07-12 · additive)
- `TRUTH-REGISTER.md` + `CONFLICT-REGISTER.md` (this folder)
- `RESEARCH-AUDIT-FOUNDATION-PHASE2.md` (this folder)
- Schemas v1: product_card / inventory_snapshot / photo_product_map (`03-Offering/`)
- Validators: `_ops/legs/ziman_phase2.py` + `_ops/tests/test_ziman_phase2.py` (**executed 2026-07-12 → 40/40 green** — calibration audit; T11→VERIFIED/T16). ⚠ known gap CF-06: validators UNWIRED from live D4 gate
- Local runtime patch: `ziman-agent/phase2_cli.py` + `ziman/product.py` now reject automatic price approval, keep unverified capacity null, load CLI JSON cards, and fail-close stale/naive/future ATP timestamps (**execution still required — REPORTED_NOT_RERUN**)
- `wiring.py`: `make_ziman_leg()` + `ziman_beat()` added (were missing — tests in `test_ziman_wiring.py` now have implementations to match). `ORGANISM-STATE.ziman` written atomically each beat.
- `_ops/tests/test_ziman_wiring.py`: rewritten with offline tests matching the wiring interface.
- `run_all.py`: `test_ziman_leg`, `test_ziman_phase2`, `test_ziman_wiring`, `test_ziman_biology` registered in main suite.
- `RUN-ZIMAN-OCTOPUS-TESTS.bat` added for 4-step offline wiring + biology verification.
- `ziman-agent/START-ZIMAN.bat` added for 4-step local agent test.
- Biology control-plane: `_ops/legs/ziman_biology.py` + `_ops/tests/test_ziman_biology.py` + `10-Interfaces/BIOLOGY-CONTRACT.md`; accepts heart rhythm, SignalHub advisory nerves, and Evolutionary Doctor RFCs under STOP/σ/human-append laws.
- Innervation registry: Ziman added as organ `ziman` → `_ops/state/ORGANISM-STATE.ziman`, SLA 120min; dead-leg detection covered by `test_innervation.py`.
- Runtime seam: `_ops/wiring.ziman_beat()` + `_ops/tests/test_ziman_wiring.py` (added 2026-07-12; restart required; no Telegram routing added)
- Qualification suite QC-01..15 (`09-Agents/Qualifications/`)
- Telegram contract (`10-Interfaces/TELEGRAM-CONTRACT.md`, dry-run design)
- Handoff: `11-Reports/Handoffs/FOUNDATION-PHASE2-HANDOFF.md`

## Next gate
1. Owner chooses inventory classification approach (A/B/C)
2. Run phase-2 + wiring tests (`python -m pytest _ops/tests/test_ziman_phase2.py _ops/tests/test_ziman_leg.py _ops/tests/test_ziman_wiring.py -q`)
3. Normalize 10–50 products into C1–C4 + SKU cards (product_card.v1)
4. Owner counting session → first inventory_snapshot (closes CF-02)
5. Photo→Product ID map (read-only, sha256)
6. First experiment pack (human-executed only)

## Kill switches
- `_ops/STOP-ORGANISM`
- `control-brain` halt
- D4 campaign reject
- Telegram STOP-TG-CENTER
