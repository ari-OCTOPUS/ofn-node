# PERSISTENT FLEET BRAIN — architecture discovery (docs/map)
**stamp_aest:** 2026-09-15 ~13:17  
**mode:** PROPOSAL_MAP · **no live queue jobs** until owner **GO EXECUTE**  
**HOLD customer_send:** true · no B4  
**ARCH role:** discover existing queue+consumers · memory contract · restore-test design · role reconcile vs T0  
**SEC owes:** failover / authenticated `node_id` gate (not this packet)

## Owner SoT (inputs)

| artifact | path | sha256 |
|----------|------|--------|
| Persistent fleet proposal | `F:\hardware-handoff-review-20260915\09-LANES\HARDWARE-HANDOFF-REVIEW-20260915\PERSISTENT-FLEET-PROPOSAL.md` | `e5cacff06435af1d6da95d339d4e4dbb58c09b32384758dfa33bc6f805053ba9` |
| T0 census LANE-REPORT (live SoT) | `F:\backup\09-LANES\OCTOPUS-HARDWARE-EXEC-20260915\LANE-REPORT.md` | `e62c785117cbf528dce701267f4ad3692d96677621839a3ee778f26cd5ae4a7c` |
| T0 inventory JSON | `…\T0-RECEIPTS\fleet-inventory-t0.json` | `ca17b6cdb4b31e7c1d3761623b589d83ec41017037994884f273c6492eb24a75` |
| Hardware review (Addendum O) | LANE-REPORT owner review | `8922bc4e…` |

**Success metric (OWNER):** better answers + remember experience + continue without laptop — **NOT** CPU/NPU fill.  
**NPU SoT unchanged:** 42 TOPS = nominal 7×6 only; inference/utilization **NOT_MEASURED**.

---

## 1. Role table — proposed vs T0 live (`e62c7851…` / `ca17b6cd…`)

| node | proposed (owner) | T0 `role` field | OCTOPUS services (T0) | `librknnrt` | reconcile |
|------|------------------|-----------------|------------------------|-------------|-----------|
| **138** | coord / ledger | `commander-router-ledger-owner` | bridge, control-router, cycle-settler, router, supervisor, verify-dispatcher, ofn, heartbeat | **3** | **ALIGN** — primary writer / commander |
| **180** | quality + recoverable memory | `quality-brain` | afferent-lab, gateway, llama-lab, organism-lab, soak-lab (+ docker) | 0 | **ALIGN** quality; memory-restore copies = design target (backup_job already knows `memory.sqlite`) |
| **182** | witness / health (**important work only**, not every heartbeat) | `lab-witness` | fusiond, metacontrol, reflex, salience-shadow, sensorium, skill-tracker, stability, world-model + **`nats-server`** + mosquitto | 0 | **ALIGN** witness; **NATS lives here** (census). Heartbeat policy must stay sparse per proposal |
| **193** | model + NPU pilot | `model-server` | **NONE** | 0 | **LABEL ONLY** — T3 unbuilt; NPU pilot needs T2 measured inference first |
| **160** | knowledge prep | `compute-node` | NONE | 0 | **ASPIRATIONAL** until T1 provision |
| **100** | knowledge retrieve | `compute-node` | NONE | 0 | **ASPIRATIONAL** until T1 (`python3` present per pre-T0 mesh note) |
| **114** | eval / batch | `compute-node` | NONE | 0 | **ASPIRATIONAL** until T1 |

**Do not** treat T0 role strings as deployed capability. Publish a 7-row matrix with NOT_RUN retained (T0 LANE-REPORT DoD).

---

## 2. Existing queue / bus discovery (evidence — prefer reuse)

**Rule:** discover before new queue. No enqueue of fleet-brain jobs until GO EXECUTE.

| surface | where | evidence | durable? | notes for fleet brain |
|---------|-------|----------|----------|------------------------|
| **WorkQueue (brain)** | `ofn/worker.py` | `docs/architecture/DECISION-brain-queue-ram.md` (2026-08-10) | **RAM-only** intentional | Shadow ledger; **no auto-replay** (double-charge risk). Thinking jobs ≠ send |
| **Autonomy task transitions** | `/home/ari/ofn/state/autonomy/queue.jsonl` | schema `octopus.autonomy-task-transition.v1` | append jsonl | Supervisor witness transitions — not general job bus |
| **Owner / reply queue** | `OWNER-QUEUE.md` + `tools/reply_queue_bridge.py` | idempotency_key dedup; `grants_send=false` | file | Owner-facing proposals only |
| **Revenue send-queue** | `state/revenue-drive/send_queue.py` | present | path-local | **HOLD customer_send** — do not reuse for fleet brain |
| **NATS** | **182** `nats-server.service` (T0 SVC list) | census `ca17b6cd…` | **UNKNOWN** JetStream/persistence | **138 `nats-server` inactive**. Prefer 182 as candidate bus; prove JetStream + consumers before adopting |
| **Mosquitto** | 182 | T0 | MQTT | Sensorium path — not default job bus |
| **octopus-verify-dispatcher / router / supervisor** | 138 systemd | T0 | process | Existing control plane — map job_id through these before new dispatcher |

**Gap (map):** `W-FLEET-QUEUE-SOT` — no single canonical producer→queue→consumer→receipt for fleet jobs yet; shadow vs RAM WorkQueue vs NATS-182 unresolved until discovery PASS + SEC.

### Proposed job contract (from owner; not implemented)

`job_id, idempotency_key, job_type, input_ref/hash, required_capability, target_node_id, deadline, attempt, lease_owner, lease_expiry, resource_budget, result_ref/hash, receipt_id`

Path: request → retrieve → model → needed review → persist.  
ACK before work; lease + deadline; crash → reconcile; unclear → **UNKNOWN** (not invent); no infinite wait; no shell as job_type.

---

## 3. Memory contract (triple)

| tier | content | writer | durable store (existing clues) |
|------|---------|--------|--------------------------------|
| **A facts / experience** | observed facts, receipts, lane outcomes | 138 primary | sqlite / jsonl under ofn state; `memory.sqlite` in backup scope |
| **B valid decisions + expiry** | owner/organism decisions with `expires_at` | 138 (+ owner_dialogue) | `decision_request`/`owner_decision` + `hold_external_sot.v1` |
| **C model summary / hypothesis + source** | summaries with provenance hashes | 180 quality gate before promote | 180 verified copy; never sole writer |

**Path:** request → retrieve (100 aspirational / 138 today) → model (193 aspirational / 180 lab today) → review (180) → persist (138) → optional 180 historical restore copy.

**Durability rules (owner):**
- 138 = **primary writer**
- 180 = **verified historical restore copies** (not failover commander)
- Laptop = observe/dev only
- Mirror ≠ failover
- SQLite backup must use proven restore (existing `backup_job` / `restore_job` verify-then-restore)

---

## 4. Identity correction (SEC gate)

| wrong | right |
|-------|-------|
| hostname + machine-id + role alone | **`node_id` registered + authenticated** |
| DHCP sticky to MAC only | media-change strategy (SD↔eMMC) — **W-HW-MAC-DHCP** |
| Clone machine-id | detect clone; re-enrollment |

SEC designs failover + auth before any auto-promote of 180/mirror to commander.

---

## 5. Restore / acceptance test design (docs only)

| # | test | pass criteria | fail / UNKNOWN |
|---|------|---------------|----------------|
| **1** | 24h laptop-independent | Jobs complete with receipt chain; no laptop in critical path | Any step needs HQ/laptop → FAIL |
| **2** | Worker-crash recovery | Kill worker mid-lease → no duplicate side effect; idempotent retry OR UNKNOWN | Dup send/result without receipt → FAIL |
| **3** | Real memory restore | Restore verified backup on spare/180 copy → readback match manifest; RPO/RTO recorded | Unverified backup accepted → FAIL |
| **4** | Quality A/B | Same prompts with vs without memory tier A/B; quality score + latency | CPU/NPU fill as success metric → DENY |

NPU pilot remains under T2 measured acceptance (Addendum O / T0 DoD) — separate from brain success metric.

---

## 6. Order (unchanged)

1. **PC:** continue T0/T1/NPU pilot under SEC scope  
2. **ARCH:** this packet — queue discovery + memory contract + restore tests (**done as map**)  
3. **SEC:** gate failover / auth `node_id`  
4. **Owner GO EXECUTE** before any live fleet-brain queue traffic  

---

## 7. Explicit DENY until GO EXECUTE

- New production queue that bypasses discovery  
- Claiming 193/100/160/114 roles as live  
- Treating NATS-182 as JetStream SoT without proof  
- Auto-replay of RAM WorkQueue  
- Failover commander without SEC  
- customer_send / B4 / APPROVE_PAT widen  
- 42 TOPS unused/ready claims  

— ARCHITECT · PERSISTENT-FLEET-BRAIN map · HOLD customer_send
