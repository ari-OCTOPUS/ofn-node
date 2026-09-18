# OWNER-RO-STALL-ARCH-20260916 — why Octopus does not self-advance

**mode:** MAP ONLY · **no implement** · **HOLD_EXTERNAL** · HOLD customer_send  
**stamp_aest:** 2026-09-16  
**from:** OCTOPUS_COMMANDER OWNER stall root-cause RO → ARCHITECT  
**commander:** **138 sole** · dual-commander **DENY**

## Binding evidence (do not invent)

| packet | sha256 |
|--------|--------|
| OWNER-RO-7BOARD-P0P6-MAP | `a15a86bc4fe4e1875d197b9d7366b433b90105395f079948d80122796c5df1df` |
| OWNER-RO-DEEP-ARCH-WIRING | `8149d40f876730cbf5c2759f9467453682ba24394f3f45b9fe604e57f390b0f5` |
| OWNER-RO-OFN-INJECT-SURFACES | `a4e4ef964802c927d4f56b91a6f3ab705f02fd337b035186e403a43285e5ec0e` |
| P0 discovery | `a2bd6c1233e7eb6d348cb9bdb36d2267c7b9e12d629dd1fedfce9db31964e4d9` |
| P5 contract (aligned) | `5d12e068568cdcc694ac1c8de6c5e36c623832727244814a36303ed7862c82d7` |
| P4 design (aligned) | `8b0a5e03c4df626cb735a54ba16e0a02c948f23c9a9066d7fe0354e107316cd2` |
| live `fleet_job.v1` | `49eb6c0be2f4a9afbd0520feba4cff00500bab73f4b5eae7a89695138ab70d59` |
| P6 design (aligned) | `4dea603014747a966bfaf9da3dd40b2378f283b462b4ed83923095920140851b` |
| P6 measure fold | `c0ba7ac90109d2bb92deff48980864aa6c66a85df5c0f6d83aab616ff461ef7c` |

---

## 0 · One-screen verdict

Octopus **does not self-advance into business cash** because architecture intentionally (and currently) keeps **three planes disconnected**:

1. **Business / HITL plane** — Telegram + legs on laptop `_ops` (LIVE-ish, publish often hard-blocked).  
2. **Persistent fleet plane** — 138 jsonl jobs + 100/160/193/114 compute roles (pilot retrieve only; no commerce `bind_role`).  
3. **Memory / RO-intel plane** — `fleet_facts` / glass / owner_dialogue (ingest gated; SEC EXECUTE often not relayed).

Self-advance would require a **designed bridge** (new job types + auth + bus proof + owner GO). Today every automatic bridge is **DENY** or **ABSENT** — so the organism **stalls by design**, not only by missing code.

---

## 1 · Missing business `bind_roles` (stall root A)

**What exists (fleet):** P4/P5 roles only — `commander` (138), `quality+restore_RO` (180), `lab_witness` (182), `knowledge_retrieve` (100), `knowledge_prep` (160), `model_infer` (193 ≠ T3), `eval_batch` (114).  
**What Architecture Maps name:** Ziman domain/legs, `studio_pf`, Saba DORMANT, Lead-نقاشی, etc.  
**Gap:** no registry `bind_role` / `fleet_job.type` for `ziman_*`, `studio_*`, `shopify_*`, `saba_*`, publish, or customer_send (`8149d40f…`, `5d12e068…`).

**Effect:** even a healthy fleet can only lease **compute** work. It cannot legally route “make a Ziman listing” or “Studio post” as a fleet job. Business value stays on the _ops/legs plane (often drafts-only / hard-blocked).

**Self-advance blocked until:** SEC+ARCH design new bind_roles + schema enums + owner GO — not by workers “trying harder.”

---

## 2 · Telegram on `_ops`, not fleet (stall root B)

**Evidence:** dual-bot centre, MiniApp, TG-SPLIT, doctor_link LIVE in Architecture Maps; **ABSENT** as P5 producer/consumer (`8149d40f…`).  
**Fleet producer:** 138 `fleet_job_sm` → `fleet_jobs.jsonl` only.  
**Telegram producer:** laptop `_ops/telegram_center` / approval_channel.

**Effect:** owner HITL and organism “pulse” advance on Telegram **do not enqueue** fleet leases. Fleet PB soak (P6 PB-1) and Telegram activity are **orthogonal clocks**. The system looks busy on TG while fleet stays idle or pilot-only.

**Self-advance blocked until:** explicit design for TG→fleet_job bridge (single writer 138, no dual poll, no laptop shadow commander) — currently DENY by dual-commander / dual-path rules.

---

## 3 · NATS consumers=0 (stall root C)

**Evidence:** P0 JetStream **YES** on 182 · **8 streams · 0 consumers** · 138 nats ABSENT · `:8222` localhost-only (`a2bd6c12…`).  
**P5 rule:** prefer `jsonl_138`; JetStream optional only with **exactly one** durable + proof else `NATS_DURABILITY=NOT_CLAIMED` (`5d12e068…`).

**Effect:** no durable puller means **no NATS-driven self-scheduling** of brain/fleet work. Claiming “mesh will advance us” is false. Any improvised consumer risks dual-poll with jsonl and falsifies P6 bus honesty.

**Self-advance blocked until:** SEC-approved `FLEET_JOB` stream + one named durable **or** stay on jsonl_138 scheduler owned solely by 138.

---

## 4 · Glass vs `fleet_facts` path (stall root D)

| path | role | stall implication |
|------|------|-------------------|
| `/home/ari/ofn/state/fleet-memory/fleet_facts.jsonl` | P1 tier-A SoT (138 append) | RO packs / experience can land **here** after EXECUTE — still **facts**, not jobs |
| glass ingest / `owner_dialogue` `intel_ingest.v1` | receipt / pointer plane | indexes packs; **does not** run workers |
| `fleet_jobs.jsonl` | P2/P5 lease SM | **DENY** packing docs here (`a4e4ef96…`) |

**Effect:** deep RO packs (INTEGRATE / SEASON-BIZ / STUDIO / ZIMAN / SEC / ARCH) can enrich **memory** without moving the **job** clock. Without a separate “promote fact → scheduled fleet_job” law (owner-gated), intel accumulates and **execution stalls**. Glass≠fleet_facts≠fleet_jobs — three sinks, one missing promote edge.

**Self-advance blocked until:** promoted, expired, hash-bound decisions (tier B) that **138** turns into bounded `type` jobs — not automatic glass→lease.

---

## 5 · Dual-commander DENY effects (stall root E)

**Rule:** only **138** may set `commander=true`, enqueue, and issue LEASE; **180** never auto-failover; laptop must not shadow-enqueue (`8b0a5e03…`, standing HOLD).

**Intended safety:** prevents split-brain and customer_send races.  
**Stall side-effect:** when 138 is idle / waiting SEC EXECUTE / waiting PB-1 wall-clock / waiting owner Telegram GO, **no other node may advance the business or fleet SM**. Quality (180), witness (182), and workers cannot “help” by becoming commanders. Parallel RO on HQ/Desktop **cannot** close the live loop.

**Self-advance blocked until:** 138 runs an authorized scheduler (still single commander) — DENY is correct; the missing piece is **authorized work on 138**, not a second commander.

---

## 6 · Jobs schema poison risks (stall root F)

Writing RO markdown or intel rows into `fleet_jobs.jsonl` / JetStream would:

1. Fail or distort `fleet_job.v1` lease SM (`49eb6c0b…`).  
2. Create false QUEUED→LEASED work for 100/160/193/114.  
3. Poison `idempotency_index.json`.  
4. Create laptop/ARCH **shadow commander**.  
5. Dual-poll if JS added beside jsonl.  
6. Falsify P6 `bus=jsonl_138` measurements (`4dea6030…`, measure OPEN).

**Effect:** the **correct** refuse-to-mix policy also means “dumping progress docs into the queue” cannot be the self-advance mechanism. Stall continues unless a **typed** job path exists.

---

## 7 · Causal chain (architecture, not blame)

```
Business maps (Ziman/Studio/TG)
        ✗ no bind_role / job_type
Telegram LIVE on _ops
        ✗ not fleet producer
NATS consumers=0
        ✗ no durable self-pull
RO intel → fleet_facts / glass
        ✗ no promote→job edge
dual-commander DENY
        ✗ only 138 may enqueue (and often waits)
DENY jobs-schema poison
        ✗ cannot cheat via jsonl dump
                    ↓
            SELF-ADVANCE STALL
     (safe stall · HOLD_EXTERNAL intact)
```

---

## 8 · What would unstall (design pointers only — NOT assigned)

Ordered, fail-closed (any skip = remain stalled):

1. Keep dual-commander DENY + HOLD customer_send.  
2. Owner/COMMANDER EXECUTE for intel inject into **fleet_facts** only (SEC `4b9158bf…` class gate) — advances **memory**, not cash.  
3. New ARCH+SEC contract: business `bind_role` + `fleet_job.type` enums with `external_effects` caps.  
4. Single scheduler on **138** (jsonl) turning tier-B decisions into QUEUED jobs — never TG dual-poll.  
5. Optional later: one JetStream durable with proof — else stay NOT_CLAIMED.  
6. P6 PB-1 wall-clock + QA before “laptop-free” claims.

**ARCH standing this turn:** map sealed · **no implement** · no enqueue · no dual-commander · no customer_send.

---

## 9 · Related artifacts

| file | use |
|------|-----|
| This packet | stall root-cause SoT for OWNER/COMMANDER |
| OWNER-RO-DEEP-ARCH-WIRING | business × fleet ABSENT wires |
| OWNER-RO-OFN-INJECT-SURFACES | safe memory vs DENY job bus |
| OWNER-RO-7BOARD-P0P6-MAP | role/topology baseline |
