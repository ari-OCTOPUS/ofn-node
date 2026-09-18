# P5 job-path bind — SEC gate (tighten)

- **task_id:** SEC-P5-JOB-PATH-GATE
- **owner:** SECURITY_GOVERNOR
- **stamp_aest:** 2026-09-15 ~13:50
- **parent EXEC:** `52887e1a088d6d4e87f2a8c14879db392a647d450afe8473ea0a5e620022d268`
- **NEXT SoT:** `F:\backup\09-LANES\OCTOPUS-PERSISTENT-FLEET-EXEC-20260915\NEXT-AGENT-MEGAPROMPT.md`  
  sha256 `7ab84e03df7ca708abeb8cb4178c2d7cf10bc00e9b17a20d2c41588c26508f07` (re-hash MATCH)
- **P4 auth:** addendum `db62b335…` · receipt cite `d8844e96…` (mesh_ssh)
- **HOLD customer_send:** true · **may_authorize:** false · **dual-commander:** DENY · **never power off 138**

Owner GO P5 EXECUTE — job-path bind before PC creates any live consumer.

---

## Verdict

**CONDITIONAL_PASS**

PC may bind **one** job_type on the **138 jsonl/shadow path first**. JetStream live consumer create is allowed **only** under the JetStream clause below. This addendum **wins** over looser wording in NEXT/`52887e1a…` P5 witness-only text for the job-path slice.

---

## Allowed

1. **Primary bus:** existing P2 **file/jsonl on 138** (producer → queue → consumer → receipt). One job_type, shadow→live.  
2. **Leases:** only `node_id` with `auth_status=OK` and `lease_eligible=true` (100/160/193/114).  
3. **Roles:** 138 sole commander/writer · 180 quality/RO restore · 182 witness/NATS host (not second memory writer).  
4. **P5 witness fold:** 182 checks important artifacts only — not every heartbeat.  
5. **JetStream (optional, 182 only):** create **exactly one** durable consumer with a **named** durable; prove `consumers>=1`, deliver, ACK, idempotent redelivery receipt. No second consumer. No dual-poll with jsonl for the same job_id. Until that proof: keep `NATS_DURABILITY=NOT_CLAIMED` / UNKNOWN.  
6. Pre-image + rollback before unit/consumer enable.

## DENY

| item | rule |
|------|------|
| Revenue / money queues | **DENY** reuse (`send_queue`, APPROVE_PAT path) |
| Dual-commander / 180 auto-failover | **DENY** |
| Power off 138 / SD wipe / reboot storm | **DENY** |
| customer_send / B4 / may_authorize flip | **DENY** / HOLD |
| JetStream without proof | **DENY** durability claim; **DENY** >1 consumer |
| Free-form shell as job_type | **DENY** |
| Lease to unregistered / PENDING_AUTH | **DENY** |
| Invent usable-TOPS | **DENY** |

## P5 exit (SEC)

- ≥1 E2E leased job 138→worker→receipt (`external_effects=0` unless separately scoped)  
- If NATS path chosen: consumer proof packet (name, stream, ack policy, `consumers>=1`)  
- Else: explicit `bus=jsonl_138` + `NATS_DURABILITY=NOT_CLAIMED`  
- QA seal before P6 acceptance claims  

## Rollback

Stop consumer; leave jsonl append-only; do not delete P0–P4 receipts. Never touch 138 commander power.

— SECURITY_GOVERNOR · P5 JOB-PATH CONDITIONAL_PASS · prefer jsonl · JetStream=1 consumer+proof max
