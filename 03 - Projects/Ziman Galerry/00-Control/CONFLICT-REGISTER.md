---
type: control
project: ZIMAN
status: active
updated: 2026-07-12
---

# CONFLICT REGISTER — Ziman

| ID | Conflict | Sources | Fail-closed behaviour (now) | Resolution owner |
|---|---|---|---|---|
| CF-01 | Capacity: 30/week "[Measured]" vs unverified vs observed ≈6.25/week | ziman.yaml ↔ STATUS.md ↔ inference | No campaign > **6/week** proposed until owner revalidates; D4 still caps at 30 in code | Owner (production) |
| CF-02 | Inventory: 20 (yaml) vs 50 ready (OWNER_INPUT) | ziman.yaml ↔ STATUS.md | Neither number used for promises; inventory_snapshot.v1 with measured_at required | Owner count session |
| CF-03 | 3 duplicate ziman-agent copies (Projects / _code / _launchpad) | filesystem | Identical today (verified 2026-07-12) → **drift risk**, not content conflict. Leg authority = Projects copy (resolve order) | Architect: declare Projects = canonical, others = mirrors; never auto-sync |
| CF-04 | `safety.autonomy: "read-only"` (yaml) vs "propose-only" (leg/STATUS) | ziman.yaml ↔ ziman_leg.py | Semantically compatible (drafts-only); terminology unify in next yaml edit — NOT changed now (runtime file) | Next agent w/ test |
| CF-05 | Brand name: "Ziman Gift" (yaml) vs "Ziman Galerry" (folder/telegram) vs "Bloom rose-gold" (candidate) | multiple | No public naming until owner confirms | Owner |
| CF-06 | **D4 fail-open:** `capacity_fail_closed()` (cap 6) exists but is UNWIRED from the live gate — `ziman_leg.py:143 campaign_check` + `worker.py:106` use raw yaml=30 (guard only in `phase2_cli.py:102` reporting) | `ziman_phase2.py` / `product.py` ↔ `ziman_leg.py` / `capacity.py` | Gate approves ≤30/wk despite CF-01; sharpen CF-01 into a code fix (route ceiling through `capacity_fail_closed`) — **gated code change** | Owner/next-agent (verdict) |
| CF-07 | **ATP fail-open:** `compute_atp` only checks `not measured_at` truthiness; stale/future/naive/garbage timestamps yield a real ATP; docstring/error/test claim freshness detection that does not exist | `ziman_phase2.py:28-39` | Add ISO8601 parse + future-reject + staleness window; add real stale/future tests | Next-agent (verdict) |
| CF-08 | **🔴 Outward-execution invariant violated by a 4th tree:** `_launchpad/second-brain-live/` is a divergent SUPERSET with real Telegram+WhatsApp `send()`, approval-queue, live loaded `.env`, and committed owner chat-id (PII value withheld) in `projects.yaml`+`users.yaml` — contradicts "ZERO outward execution" | filesystem (4th tree beyond CF-03's 3) | Owner: declare its status — if it's the real live bot it needs its own governance + PII → `.env`, else archive; agent will not touch it | Owner (verdict) |
| CF-09 | **Provider mislabel (model identity not invariant):** launchpad `anthropic-key`/`ANTHROPIC_API_KEY` actually holds a DeepSeek key (via `ANTHROPIC_BASE_URL`), vs `ziman.yaml:33 model: claude-sonnet-5` | launchpad `app.py` ENV_SECRET_MAP ↔ ziman.yaml | Correct labeling + rotate; RQ-05 invariance depends on it | Owner |
| CF-10 | Dangling qualification pointer: Role Card `suite: "ziman_product_shared"` ≠ actual `ZM-QUAL-PRODINV-v1`; Role Card lists only 3 informal critical tests vs suite's 12 + omits all-critical gate | `product_inventory.yaml:45-50` ↔ `product-inventory-suite.yaml` | Point Role Card to real suite_id + all-critical gate | Next-agent |

## Rules
- A conflict is closed only with evidence + owner confirmation + updated_at.
- Closed conflicts move to `DecisionLog.md`, never deleted here.
