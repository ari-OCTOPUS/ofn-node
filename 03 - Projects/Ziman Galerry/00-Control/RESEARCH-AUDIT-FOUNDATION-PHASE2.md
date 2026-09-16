---
type: report
project: ZIMAN
status: complete
updated: 2026-07-12
phase: FOUNDATION-PHASE2
---

# RESEARCH AUDIT — Foundation Phase 2 (executed 2026-07-12)

## B. Files actually inspected (this session)
- `_ops/legs/ziman_leg.py` (full) · `_ops/wiring.py` (full) · `_ops/tests/test_ziman_leg.py` (full)
- `_ops/budget/budgets.yaml` (full) · `_ops/telegram_center/center.py` (head)
- `ziman-agent/ziman.yaml` × 3 copies (Projects / `_code` / `_launchpad`) — byte-identical content
- `00-Control/STATUS.md` · `03-Offering/CATALOG.md` · directory trees

## F. Research findings (RQ-01..07)
| RQ | Finding | Class |
|---|---|---|
| RQ-01 runtime authority | `ZimanLeg._resolve_agent_root()` prefers **Projects copy** first, then `_code`, then `_launchpad`. All 3 identical today → Projects = de-facto authority; others = mirrors (drift risk, CF-03) | VERIFIED |
| RQ-02 capacity truth | 30/week labelled "[Measured]" in yaml but source is a prose note; STATUS marks CONFLICT. Fail-closed: proposals capped at min(ceiling, 6)/week via `capacity_fail_closed()` until owner revalidates | CONFLICT handled |
| RQ-03 inventory model | Delivered: `product_card.v1`, `inventory_snapshot.v1` (03-Offering/) with ATP invariant + measured_at freshness | DESIGNED |
| RQ-04 photo mapping | Delivered: `photo_product_map.v1` — hash-based, originals never moved, scope locked to WhatsApp-2026, unknown allowed, privacy_flag stops processing | DESIGNED |
| RQ-05 telegram | center.py already has `ziman` leg key + owner allowlist + STOP-TG-CENTER + ok/no/later approvals. Contract for 8 commands written (10-Interfaces/TELEGRAM-CONTRACT.md), dry-run only | VERIFIED + DESIGNED |
| RQ-06 heart/organism | Leg has no writes to pacemaker/setpoint/policy; heart behind separate `OCTOPUS_WIRE_HEART` flag (excluded from PAPER_FULL). STOP/halted() checked before every beat fn in wiring | VERIFIED (static) |
| RQ-07 experiments | EXP cards exist in 05-Growth; thresholds/stop-conditions need owner audience data — blocked on inventory classification decision (A/B/C) | PARTIAL |

## H. Implemented safe changes (all additive, reversible)
| File | Kind | Rollback |
|---|---|---|
| `00-Control/TRUTH-REGISTER.md` | new doc | delete |
| `00-Control/CONFLICT-REGISTER.md` | new doc | delete |
| `03-Offering/PRODUCT-CARD-SCHEMA.yaml` | new schema | delete |
| `03-Offering/INVENTORY-SNAPSHOT-SCHEMA.yaml` | new schema | delete |
| `03-Offering/PHOTO-PRODUCT-MAP-SCHEMA.yaml` | new schema | delete |
| `09-Agents/Qualifications/product-inventory-suite.yaml` | new suite | delete |
| `10-Interfaces/TELEGRAM-CONTRACT.md` | new doc | delete |
| `_ops/legs/ziman_phase2.py` | new pure module (no imports by others) | delete |
| `_ops/tests/test_ziman_phase2.py` | new tests | delete |
| `11-Reports/Handoffs/FOUNDATION-PHASE2-HANDOFF.md` | new doc | delete |
| `00-Control/STATUS.md` | edited (next-gate section) | git / previous text in this report |

**Zero files moved/deleted. Zero external actions. No .env touched. No token read.**

## I. Test evidence
- This session had **no shell access** → tests written but **NOT executed** here.
- Class: `REPORTED_NOT_RERUN`. Owner/next agent must run:
```bat
cd /d F:\backup
python -m pytest _ops/tests/test_ziman_phase2.py _ops/tests/test_ziman_leg.py -q
python _ops/smoke_ziman_wire.py
```

## L. Risks & approval boundaries
- CF-01 capacity + CF-02 inventory remain OPEN — no delivery promises possible.
- 3-way copy drift (CF-03): declare Projects canonical; never auto-sync.
- Telegram live activation = owner decision + token, outside this scope.
