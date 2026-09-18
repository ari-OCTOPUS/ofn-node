# P6 — ACCEPTANCE-MATRIX design + PB-1…PB-6 witness checklists

**stamp_aest:** 2026-09-15 ~13:58  
**mode:** DESIGN · schema + checklists · **PC implements / measures** · QA seals · ARCH design only  
**aligned_to:** NEXT `7ab84e03df7ca708abeb8cb4178c2d7cf10bc00e9b17a20d2c41588c26508f07`  
**proposal:** `e5cacff0…` acceptance table · QA draft PB-1…4 `QA-PERSISTENT-BRAIN-4TESTS-ACCEPTANCE-DRAFT`  
**commander:** 138 · dual-commander **DENY** · **HOLD customer_send**  
**P5 gate:** QA P5 PASS_WITH_CAVEAT `76b6d7da…` — P6 measure may start; **no invent PASS**

---

## 0. Files

| file | role |
|------|------|
| `schemas/acceptance_matrix.v1.schema.json` | matrix schema |
| `P6/ACCEPTANCE-MATRIX.json` | PC fills (validate against schema) |
| `P6/PB-{1..6}-WITNESS.md` or `.json` receipts | per-test evidence packs |
| This design | SoT checklist |

---

## 1. Hard rules (all PB)

- Record **PASS / FAIL / NOT_RUN / UNKNOWN / IN_PROGRESS** honestly — table is aspirational.  
- **CPU/NPU fill is not success.**  
- **42 TOPS** = nominal only — never usable/ready claim.  
- **No early PASS on PB-1:** start wall-clock watch; PASS only after **≥24.0 real hours**; until then `IN_PROGRESS` or `NOT_RUN`. Compressed/simulated clocks → **FAIL** / DENY PASS.  
- No customer_send / revenue queues / dual-commander / power-off 138.  
- Overall matrix **PASS** only if COMMANDER+QA authorize after rows complete — design does not auto-PASS.

---

## 2. Matrix row template

See schema `acceptance_matrix.v1`. Seed recommended:

```json
{
  "schema": "acceptance_matrix.v1",
  "matrix_id": "p6-20260915",
  "created_at": "<utc>",
  "next_sha256": "7ab84e03df7ca708abeb8cb4178c2d7cf10bc00e9b17a20d2c41588c26508f07",
  "proposal_sha256": "e5cacff06435af1d6da95d339d4e4dbb58c09b32384758dfa33bc6f805053ba9",
  "commander_node_id": "138",
  "customer_send": false,
  "dual_commander": false,
  "overall": "OPEN",
  "tests": [
    {"id":"PB-1","name":"Continuity without laptop (≥24h wall-clock)","status":"NOT_RUN","witness_receipt_path":null,"witness_receipt_sha256":null,"started_at":null,"ended_at":null,"wall_clock_hours":null,"caveats":[],"notes":""},
    {"id":"PB-2","name":"Worker restart / brief disconnect","status":"NOT_RUN","witness_receipt_path":null,"witness_receipt_sha256":null,"started_at":null,"ended_at":null,"wall_clock_hours":null,"caveats":[],"notes":""},
    {"id":"PB-3","name":"Restore separate path + RPO/RTO","status":"NOT_RUN","witness_receipt_path":null,"witness_receipt_sha256":null,"started_at":null,"ended_at":null,"wall_clock_hours":null,"caveats":[],"notes":"P3 baseline 83d52513… may seed"},
    {"id":"PB-4","name":"Answer-with-memory A/B","status":"NOT_RUN","witness_receipt_path":null,"witness_receipt_sha256":null,"started_at":null,"ended_at":null,"wall_clock_hours":null,"caveats":[],"notes":""},
    {"id":"PB-5","name":"NPU honesty","status":"NOT_RUN","witness_receipt_path":null,"witness_receipt_sha256":null,"started_at":null,"ended_at":null,"wall_clock_hours":null,"caveats":[],"notes":"cite T2 matrix d13f1928…; nominal TOPS only"},
    {"id":"PB-6","name":"Expand seven-row matrix","status":"NOT_RUN","witness_receipt_path":null,"witness_receipt_sha256":null,"started_at":null,"ended_at":null,"wall_clock_hours":null,"caveats":[],"notes":"fixed denominator 7"}
  ]
}
```

---

## 3. Per-test witness checklists

### PB-1 — Continuity without laptop (≥24h wall-clock)

**Intent (NEXT/proposal):** pre-registered allowed jobs schedule/run/result on fleet; local Q/A sample; no laptop in critical path.

| # | witness item | required |
|---|--------------|----------|
| 1 | `watch_started_utc` recorded **before** claiming IN_PROGRESS | yes |
| 2 | Wall-clock span **≥ 24.0h** before status=PASS | yes — **no early PASS** |
| 3 | `critical_path_inventory` — zero required laptop/HQ hop | yes |
| 4 | `laptop_dependency_probe` during window | yes |
| 5 | Sample job receipt chain on 138 (jsonl fleet_job) | ≥1 CLOSED |
| 6 | Local Q/A sample on-node without laptop | ≥1 |
| 7 | Heartbeat health counts (STALE ≠ healthy capability) | yes |

**PASS:** all above + real ≥24h. **IN_PROGRESS:** watch started, <24h. **FAIL:** simulated clock or laptop required.

### PB-2 — Worker restart / brief disconnect

| # | witness item | required |
|---|--------------|----------|
| 1 | `fault_script` + pre-image | yes |
| 2 | `job_id` / `idempotency_key` / bounded `type` (not shell) | yes |
| 3 | lease_owner / lease_expiry before+after | yes |
| 4 | side_effect count — duplicates = FAIL | yes |
| 5 | UNKNOWN preserved if ambiguous | yes |
| 6 | recovery receipt terminal state | yes |

### PB-3 — Restore separate path

| # | witness item | required |
|---|--------------|----------|
| 1 | verified backup method (not open-DB copy) | yes |
| 2 | manifest sha + readback MATCH | yes |
| 3 | restore on **separate** path (180 `/opt/octopus-restore-copies/…` OK) | yes |
| 4 | `RPO_seconds` / `RTO_seconds` measured | yes |
| 5 | dual-commander still DENY | yes |

May cite P3 `83d52513…` as baseline; re-measure RPO/RTO if not in receipt.

### PB-4 — Answer-with-memory A/B

| # | witness item | required |
|---|--------------|----------|
| 1 | frozen prompt set + sha256 | yes |
| 2 | condition A memory on / B off | yes |
| 3 | per-item quality+latency (named rubric) | yes |
| 4 | aggregate Δ; no CPU/NPU-as-success | yes |

### PB-5 — NPU honesty

| # | witness item | required |
|---|--------------|----------|
| 1 | output correctness witness | yes |
| 2 | model + runtime hash | yes |
| 3 | n, p50/p95, throughput | yes |
| 4 | device witness | yes |
| 5 | **DENY** usable-42-TOPS / unused-ready claims | yes |

May fold T2 matrix `d13f1928…` (6/7 PASS, 138 NOT_RUN) with honest NOT_RUN retained.

### PB-6 — Expand seven-row matrix

| # | witness item | required |
|---|--------------|----------|
| 1 | exactly **7** rows (138/180/182/100/160/193/114) | yes |
| 2 | status ∈ PASS/FAIL/NOT_RUN/UNKNOWN each | yes |
| 3 | fixed denominator 7 (no dropouts) | yes |
| 4 | RAM / temp / error per board where measured | yes |
| 5 | 193 model-server service still not implied by label | yes |

---

## 4. PC apply order

1. Create `P6/ACCEPTANCE-MATRIX.json` seed (overall OPEN).  
2. **Start PB-1 watch** immediately if running continuity — record `started_at`; status IN_PROGRESS — **do not PASS**.  
3. Run PB-2…PB-6 as evidence allows; attach witness receipts.  
4. QA seals matrix; COMMANDER may unlock product claims.  
5. HOLD customer_send throughout.

## 5. ARCH standing

Schema + this checklist only. No fake PASS rows. No live fault injection from ARCH.


---

## Alignment — SEC-P6-ACCEPTANCE `9cd862ef…` (2026-09-15)

**SEC SoT:** `/workspace/octopus-hq/wiring/SEC-P6-ACCEPTANCE-20260915.md`  
sha `9cd862efcad4ee98cb021913c1a92ab5d1fc7766915ce47e2a646bcbb72c9c3c`  
**Verdict:** **CONDITIONAL_PASS**

### Match

| SEC | ARCH design |
|-----|-------------|
| Prefer **jsonl_138** for all PB | Seed + checklists assume P5 bus; JetStream new consumer **DENY** until 1 durable+proof |
| PB-1 no fake 24h | §1 + PB-1 checklist: wall-clock ≥24h · no early PASS · else IN_PROGRESS/NOT_RUN with measured duration |
| PB-5 NPU honesty | checklist DENY usable-42-TOPS |
| PB-2 one worker fault; never power 138 | checklist + Hard rules |
| PB-3 separate path; no dual-commander | checklist cites P3 RO path |
| Matrix honest statuses | schema enums NOT_RUN/IN_PROGRESS/PASS/… |

PC measures under this gate. ARCH design only. HOLD customer_send.
