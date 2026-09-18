# OWNER clear-blockers — ARCH support map

**mode:** MAP / support · **no implement** this packet · **HOLD customer_send**  
**stamp_aest:** 2026-09-16  
**from:** OCTOPUS_COMMANDER OWNER GO clear-blockers → ARCHITECT  
**DENY:** invent NATS durable · commerce smuggle · dual-commander · usable-42

---

## 0 · Verdicts (one screen)

| ask | answer |
|-----|--------|
| Promote-bridge LIVE after Step B? | **YES (pilot)** — apply receipt `10f78945…` · EXECUTE `f506b159…` · outcome **ok** · retrieve→100 CLOSED · bus `SHADOW_LOCAL_JSONL` · **no** JetStream consumer |
| W23 additive land interfaces? | **EXECUTE-READY Class C** (`125a81c8…`) · land = additive WT only · primary `F:\ofn-node\ofn\ziman_cycle` still **ABSENT** until apply receipt |
| P6 overall / PB-4? | Matrix `ac4dbb18…` · **overall OPEN** · **PB-4 NOT_RUN** · blockers include PB-4 harness + QA seal · NATS **NOT_CLAIMED** (honest, not invented durable) |
| What unblocks PB-4? | Frozen prompt set + A/B harness on retrieve/memory · measure quality+latency · **not** NATS · promote-bridge helps feed `retrieve` jobs but **≠** PB-4 harness |

---

## 1 · Promote-bridge LIVE state (confirm)

| artifact | sha256 | role |
|----------|--------|------|
| ARCH design | `87fc6f3d7beff1bf137763654579ccd7ee92e2655aa4069e58e2cee7c403d219` | MATCH |
| SEC EXECUTE | `f506b159ee67bccbe138a1791d4a0a40d1ccfb6644fa5c0e02873256aeb2ffd9` | MATCH |
| APPLY receipt (.md) | `10f78945a4997df19d1a04875ab66c747c7bf1f505db7d96ad6b772ff6b7198d` | **LIVE apply ok** |
| APPLY receipt (.json) | `4b8c8fd508da54d445c087db0281c309bc250324a15a37265141cb3470a7ce22` | machine twin |
| SSH Step A | `4c2215b9…` | mesh trust GREEN (precondition) |

### Schemas / deps on 138 (from apply receipt)

| item | path / sha | dep note |
|------|------------|----------|
| `fleet_promote_request.v1` | HQ+138 schemas · `ffa63bda…` | Step B input |
| `fleet_promote_receipt.v1` | HQ+138 schemas · `7bbf716a…` | Step B outcome |
| bridge | `/home/ari/ofn/state/fleet-memory/fleet_promote_bridge.py` · `cd00c2fc…` | 138-only writer |
| facts | `…/fleet_facts.jsonl` | source tier A |
| decisions | `…/fleet_decisions.jsonl` | **required** gate |
| promotes | `…/fleet_promotes.jsonl` + `promote_decision_spent.json` | one-use |
| jobs | `…/fleet-jobs/fleet_jobs.jsonl` + idempotency index | QUEUED emit only via bridge |
| P5 SM | existing lease path | retrieve→100 CLOSED proven (`job-d7af47b150bc4135`) |
| JetStream | consumers=**0** | **DENY** invent durable; promote path **jsonl only** |

**Negatives proven LIVE:** commerce types DENY · expired decision DENY · non-138 DENY · prep→160 deferred DENY · idempotency ACK_SEEN.

**Not LIVE:** prep→160 · model_infer→193 · eval_batch→114 · auto-promote flood · NATS promote.

---

## 2 · W23 additive land interfaces

| layer | interface | status |
|-------|-----------|--------|
| Plan | `W23-ZIMAN-CYCLE-ADDITIVE-CHECKOUT-PLAN-20260913.md` | sha `479606a3…` · additive WT only |
| SEC | `SEC-W23-ZIMAN-CYCLE-CLASS-C-20260916.md` | sha `125a81c8…` · **EXECUTE-READY PASS** Class C |
| Package SoT (repair) | `F:\wt-ziman-cycle-repair-20260910` · branch `repair/ziman-cycle-4-readiness` | PRESENT (plan/addendum) |
| Primary tree | `F:\ofn-node\ofn\ziman_cycle` | **ABSENT** (do not dirty-main land) |
| 138 ofn tree | ziman_cycle | **ABSENT** until documented land |
| Import prove | `python -c "import ofn.ziman_cycle"` from WT | owed on apply |
| Tests | pytest `tests/ziman_cycle` | owed on apply |
| PYTHONPATH/cwd | document for organism jobs | owed on apply |
| Legacy | `_ops/legs/ziman_leg.py` | **non-use** · no delete |
| Receipt | `SEC-W23-APPLY-RECEIPT-*.md` | **feeds I7 R1** — not yet this ARCH packet |
| DENY | merge onto dirty ofn-node · reset/clean · force-push · customer_send · invent NATS durable · dual-commander | intact |

**Clear-blocker meaning:** W23 is **gated ready** for PC additive land; it is **not** the PB-4 harness and **not** a commerce bind_role. Landing package ≠ enabling ziman_* fleet job types (still DENY / separate GO).

---

## 3 · PB-4 acceptance criteria (P6 · still NOT_RUN)

**Matrix:** `ACCEPTANCE-MATRIX-P6-20260916.json` sha `ac4dbb18…`  
**Design SoT:** P6 `4dea6030…` · SEC P6 `9cd862ef…`  
**Witness stub:** `P6/PB-4/PB-4-ANSWER-MEMORY-AB.json` · status **NOT_RUN** · honest_reason: no frozen prompts / no retrieve A/B harness (fleet_facts was dry-only at stamp; Step B later added facts but **harness still missing**).

### Required witnesses (from design checklist)

| # | criterion | need to run |
|---|-----------|-------------|
| 1 | Frozen prompt set + **sha256** | Author + seal prompt file; cite sha in receipt |
| 2 | Condition **A = memory on** / **B = memory off** | Same prompts; A may use fleet_facts / retrieve-with-memory; B without |
| 3 | Per-item **quality + latency** (named rubric) | Rubric doc + measured rows — **DENY invent scores** |
| 4 | Aggregate Δ; **no** CPU/NPU-as-success | Compare A vs B; NPU fill ≠ PASS |

### Schema / deps for a real PB-4 run

| dep | role | blocker if missing |
|-----|------|--------------------|
| Worker **100** retrieve + mesh (Step A) | execute retrieve | GREEN |
| Promote-bridge (Step B) **optional** | can QUEUED retrieve from fact+decision | LIVE pilot — helpful feeder, **not sufficient** |
| `fleet_facts` with answerable content | memory-on condition | more than dry row; promote_candidate ≠ QA corpus |
| **Frozen prompt set** artifact | criterion 1 | **MISSING** — primary blocker |
| **retrieve_ab / answer-with-memory harness** | run A/B + record latency | **MISSING** — primary blocker |
| Rubric (named) | quality scores | **MISSING** |
| PB-4 witness JSON update | matrix row | stays NOT_RUN until filled honestly |
| JetStream durable | — | **NOT required**; remain `NATS_DURABILITY=NOT_CLAIMED` |

### Explicit non-claims

- Do **not** invent NATS durable to “pass” PB-4.  
- Do **not** treat Step B CLOSED retrieve pilot as PB-4 PASS.  
- Do **not** use W23 ziman_cycle land as PB-4 memory path unless harness explicitly binds it (default: PB-4 = retrieve/memory A/B, not commerce).  
- overall stays **OPEN** until QA seal even after PB-4.

---

## 4 · Clear-blockers order (ARCH recommendation · not assign)

1. **PB-4 harness design+apply** (PC/QA) — frozen prompts + A/B runner + rubric → only path to leave NOT_RUN.  
2. **W23 additive apply receipt** (PC under SEC `125a81c8…`) — clears ziman_cycle land HOLD for I7 R1; orthogonal to PB-4.  
3. Keep promote-bridge on **retrieve→100** only until separate SEC widen.  
4. Leave NATS consumers=0 / NOT_CLAIMED until one-durable+proof GO.  
5. HOLD customer_send throughout.

---

## 5 · ARCH standing

Support map only. No land, no harness implement, no NATS invent, no matrix PASS invent. Await COMMANDER assign for any follow-on design (e.g. PB-4 harness contract).
