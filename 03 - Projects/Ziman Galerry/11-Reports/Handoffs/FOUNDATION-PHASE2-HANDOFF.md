---
type: handoff
project: ZIMAN
status: ready
updated: 2026-07-12
from: Ziman Research & Next-Phase Design Agent
to: next engineering agent
---

# HANDOFF — Foundation Phase 2

## What is now true (verified this session)
- ZimanLeg wired (propose-only, D4, HARD_GATED) — `_ops/legs/ziman_leg.py`
- 3 config copies identical; **Projects copy = authority** (leg resolve order)
- Budgets: ZIMAN floor AU$1, core_member, partners Ari70/Mother30
- Telegram center has `ziman` key; contract designed, **not activated**

## New artifacts (all additive)
- Schemas: product_card.v1 / inventory_snapshot.v1 / photo_product_map.v1 (`03-Offering/`)
- Validators: `_ops/legs/ziman_phase2.py` + `_ops/tests/test_ziman_phase2.py` (14 tests, NOT yet run)
- Registers: TRUTH / CONFLICT (`00-Control/`)
- Qualification suite QC-01..15 (`09-Agents/Qualifications/`)
- Telegram contract (`10-Interfaces/`)

## Your first 5 actions
1. Run test commands (see RESEARCH-AUDIT §I) → update T11 class to VERIFIED or FAIL.
2. Await owner A/B/C decision → generate Product Cards accordingly.
3. Owner counting session → first `inventory_snapshot` (closes CF-02).
4. Owner capacity revalidation → close CF-01; until then use `capacity_fail_closed()` (max 6/wk).
5. Read-only photo index (sha256) of WhatsApp-2026 → photo_product_map entries with product_id=null.

## Hard boundaries (unchanged)
- No publish/send/spend/deploy/price/promise. Human gate for everything external.
- Never move/rename photos or legacy files. Never auto-sync the 3 copies.
- Telegram = gateway only. Canonical memory only via curator + owner.

## Open owner decisions
1. **A/B/C inventory classification scope** (recommended B) ← the single pending decision
2. Capacity revalidation (CF-01) · 3. Real count (CF-02) · 4. Brand name (CF-05)
