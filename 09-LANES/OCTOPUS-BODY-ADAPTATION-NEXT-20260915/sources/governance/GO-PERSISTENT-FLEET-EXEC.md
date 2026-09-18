# PERSISTENT-FLEET EXECUTE-READY — SEC PASS (phased)

- **task_id:** GO-PERSISTENT-FLEET-EXEC
- **owner:** SECURITY_GOVERNOR
- **stamp_aest:** 2026-09-15 ~13:21
- **mode:** EXECUTE-READY · **SEC PASS**
- **executor:** PC bridge → organism apply **phase-by-phase**
- **customer_send / HOLD_EXTERNAL:** **HOLD** (`13a1e79f…`)
- **GO-B4 / may_authorize / wire flips:** **DENY**
- **dual-commander failover:** **DENY** until separate design + SEC PASS
- **power off 138:** **DENY**
- **invent usable-TOPS:** **DENY** (nominal 42 ≠ measured)

---

## 0. Binding SoT

| artifact | path | sha256 |
|----------|------|--------|
| Owner proposal | `F:\hardware-handoff-review-20260915\09-LANES\HARDWARE-HANDOFF-REVIEW-20260915\PERSISTENT-FLEET-PROPOSAL.md` | `e5cacff06435af1d6da95d339d4e4dbb58c09b32384758dfa33bc6f805053ba9` |
| ARCH map | `/workspace/octopus-hq/wiring/PERSISTENT-FLEET-BRAIN-ARCH-20260915.md` | `17eb76e17869e73d3a665edae546e25ad67f89e35c6e2c3296ce97ef886f7768` |
| Prior SEC docs review | `SEC-PERSISTENT-FLEET-PROPOSAL-20260915.md` | `b01918c468a4a85c4ecc8449d37ce85d72d830f80bfcac5291e9b88ede3aaa2d` |
| HW megaprompt gate | `SEC-HW-MEGAPROMPT-GATE-20260915.md` | `69012a24a31d5d907cd9f1dd0956f10cb4f094daef6688cf4bd4554ef4705cc5` |
| T0 LANE-REPORT (ARCH cite) | `F:\backup\09-LANES\OCTOPUS-HARDWARE-EXEC-20260915\LANE-REPORT.md` | `e62c785117cbf528dce701267f4ad3692d96677621839a3ee778f26cd5ae4a7c` |
| T0 inventory | `…\T0-RECEIPTS\fleet-inventory-t0.json` | `ca17b6cdb4b31e7c1d3761623b589d83ec41017037994884f273c6492eb24a75` |

Owner GO FULL + this sha = execute license for **ordered phases** only. Each phase needs its own receipt before the next starts.

---

## 1. Verdict

**PASS (EXECUTE-READY, phased)**

PC/organism may proceed **P0 → P6** under the DENY list. No phase may skip ahead. No customer send. No dual writer. No powering off 138.

---

## 2. Phases (ordered)

### P0 — Discover queue / NATS / consumers (READ)

- **ALLOW:** read-only on 138/182: WorkQueue docs, autonomy `queue.jsonl`, owner reply queue, revenue send-queue (**observe only**), systemd NATS/Mosquitto status.  
- **EXPECT (ARCH):** NATS on **182**; 138 nats inactive; JetStream = **UNKNOWN** until consumer proof.  
- **DENY:** enqueue fleet-brain jobs; reuse revenue `send_queue` for brain.  
- **EXIT:** discovery receipt path+sha (existing surfaces table).

### P1 — Memory contract triple + path

- **ALLOW (design→implement on non-TCB / append-only):** tiers A facts · B decisions+expiry · C hypothesis+source. Path: request → retrieve → model → review → persist.  
- **Writer:** 138 primary; 180 = verified historical **copy** only. Laptop observe/dev.  
- **DENY:** 180 as sole writer; promote C without review; secrets in memory rows.  
- **EXIT:** schema/docs + one dry persist receipt (`external_effects=0`).

### P2 — Durable job contract

- **ALLOW:** implement contract fields from proposal (`job_id`, `idempotency_key`, … `receipt_id`); ACK ≠ success; crash reconcile; unclear → **UNKNOWN**; deadline+lease; no shell-as-job_type.  
- **Bus:** prefer **discovered** surface; if NATS-182, require JetStream stream+consumer config receipt first. RAM WorkQueue = shadow only (no auto-replay double-charge).  
- **DENY:** claiming durable without JetStream consumer proof (`NATS_DURABILITY=UNKNOWN` until then).  
- **EXIT:** unit tests for idempotency + UNKNOWN; no production enqueue yet unless P0 chose an existing safe bus.

### P3 — 138 writer + 180 verified restore copies

- **ALLOW:** 138 continues primary state writer; 180 Online Backup / proven restore_job path; restore drills on **separate/non-prod path**; RPO/RTO recorded.  
- **DENY:** dual-commander; auto failover 138→180; power off 138; open-file sqlite copy as “backup”; laptop in critical path.  
- **EXIT:** restore readback MATCH manifest receipt.

### P4 — Role binding vs T0 census

- **ALLOW:** publish 7-row matrix (proposed vs T0 `e62c7851…`/`ca17b6cd…`) with NOT_RUN retained for 193/160/100/114. Bind jobs to **registered authenticated `node_id`** (credential), not hostname+machine-id alone.  
- **DENY:** treat T0 role string as deployed capability; invent NPU usable-TOPS; claim 193/100/160/114 live.  
- **EXIT:** matrix receipt + node_id registry design (no secret paste).

### P5 — 182 witness scope

- **ALLOW:** 182 witnesses **important Class-B-class** artifacts only (FREEDOM-V2 Class B / TCB-adjacent / restore / deploy).  
- **DENY:** witness every heartbeat; block green Class A on witness lag.  
- **EXIT:** witness policy stub + one sample Class-B receipt path.

### P6 — Acceptance

Run only after P0–P5 receipts exist:

| test | pass |
|------|------|
| 24h laptop-independent | critical path receipts without HQ/laptop |
| crash idempotency | kill mid-lease → no dup side effect; UNKNOWN preserved |
| real restore | verified backup restore MATCH |
| quality A/B | with vs without memory; **not** CPU/NPU fill |

Fail closed on customer_send or dup external effect.

---

## 3. Hard DENY (all phases)

- `customer_send` / GO-B4 / `may_authorize` / `OCTOPUS_WIRE_*` flip  
- Dual-commander failover / second state writer  
- Power off / wipe 138 (or unscoped reboot storm — HW gate)  
- Invent usable-TOPS / treat 42 TOPS as measured  
- Revenue send-queue / money `APPROVE_PAT` widen  
- Secrets paste / TFN / deploy keys  
- Dirty `reset --hard` / `clean -fd` on `F:\ofn-node` or `F:\backup`

---

## 4. Apply order (PC)

1. Re-hash this file + proposal `e5cacff0…` + ARCH `17eb76e1…`.  
2. Create lane bag: `F:\backup\09-LANES\OCTOPUS-HARDWARE-EXEC-20260915\PERSISTENT-FLEET-EXEC\` (or sibling).  
3. Run **P0 only**; seal discovery receipt; COMMANDER/QA may spot-check.  
4. Then P1…P6 sequentially with receipts.  
5. Do **not** start live fleet-brain production traffic until P0+P2 durability status is either proven or explicitly `UNKNOWN` with RAM/shadow-only bus.

## 5. Rollback

- Per-phase: revert non-TCB files from pre-image; delete new queue if wrongly production-enqueued.  
- Restore drills: use separate path only — never overwrite sole 138 live DB without scoped GO.  
- Dual-writer incident → stop writers; restore 138 from last known good; SEC incident note.

— SECURITY_GOVERNOR · GO-PERSISTENT-FLEET-EXEC PASS · phased · HOLD customer_send · DENY dual-commander
