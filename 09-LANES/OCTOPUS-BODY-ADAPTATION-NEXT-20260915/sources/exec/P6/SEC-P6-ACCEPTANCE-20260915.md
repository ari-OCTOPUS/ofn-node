# P6 acceptance — SEC gate (PB-1…PB-6)

- **task_id:** SEC-P6-ACCEPTANCE
- **owner:** SECURITY_GOVERNOR
- **stamp_aest:** 2026-09-15 ~13:58
- **mode:** GATE · before fault/restart tests or any **new** consumer
- **parent NEXT:** `7ab84e03df7ca708abeb8cb4178c2d7cf10bc00e9b17a20d2c41588c26508f07`
- **parent EXEC:** `52887e1a088d6d4e87f2a8c14879db392a647d450afe8473ea0a5e620022d268`
- **P5 SEC:** `3e8bd525748531e747761cfaa4345b8a39af8758ea3bf7c565e3da1ea8ba27ec`
- **P5 QA:** `76b6d7daacdba4bca55f3ecf6fff96a53fd0ce38f0cfb3147f40c6a9538c8275` (PASS_WITH_CAVEAT · bus=`jsonl_138` · JetStream `consumers=0` · `NATS_DURABILITY=NOT_CLAIMED`)
- **HOLD customer_send:** true · **may_authorize:** false · **dual-commander:** DENY · **never power off 138**

Owner GO P6 FULL — run PB-1…PB-6 under this gate only.

---

## Verdict

**CONDITIONAL_PASS**

PC may run acceptance tests **PB-1…PB-6** on the **existing jsonl_138** job path. Prefer reversible faults. **No new JetStream/NATS consumer** in P6 unless the one-consumer clause below is met first. This gate does **not** auto-claim 24h independence.

---

## Per-test rules

| ID | test | ALLOW | DENY / honesty |
|----|------|-------|----------------|
| **PB-1** | Continuity without laptop | Pre-registered jobs + local Q/A sample; wall-clock evidence only | **DENY fake 24h** — claim `24h` only with real elapsed window + receipts; else PASS/`PARTIAL`/`NOT_RUN` with measured duration |
| **PB-2** | Worker restart / brief disconnect | Kill/restart **one** lease-eligible worker (100/160/193/114); check lease/deadline, no dup effects, UNKNOWN preserved | Power off **138**; multi-board reboot storm; SD wipe |
| **PB-3** | Restore separate path | Use P3 verified restore path; record RPO/RTO | Overwrite sole live 138 DB as the “test”; dual-commander restore |
| **PB-4** | Answer-with-memory A/B | Held-out prompts; quality+latency with/without retrieval | CPU/NPU fill as success; invent scores |
| **PB-5** | NPU honesty | Model/runtime hash, n, p50/p95, device witness | Invent usable-TOPS / treat 42 TOPS as measured capacity |
| **PB-6** | Expand matrix | 7-row PASS/FAIL/NOT_RUN/UNKNOWN; RAM/temp/error | Hide NOT_RUN; claim fleet complete without denominator |

## Bus / consumer

| path | rule |
|------|------|
| **jsonl_138** (P5 proven) | **Preferred** for all PB tests |
| **New NATS/JetStream consumer** | **DENY** until: exactly **one** named durable on a dedicated fleet stream + proof (`consumers>=1`, deliver, ACK, idempotent redelivery). Else keep `NATS_DURABILITY=NOT_CLAIMED` |
| Revenue / money queues | **DENY** reuse |

## Global DENY

- customer_send / B4 / may_authorize flip  
- Dual-commander / 180 as writer  
- Power off 138  
- Destructive SD wipe / unscoped reboot storm  
- Blind retry of non-idempotent effects  
- Shell-as-job_type  

## P6 exit (SEC)

- Matrix of PB-1…PB-6 with honest PASS/FAIL/NOT_RUN/UNKNOWN + evidence paths  
- No `24h` claim without wall-clock proof  
- If any new consumer created: one-consumer proof packet path+sha  
- QA independent seal before owner “fleet durable / laptop-free” claim  

## Rollback

Stop test jobs; restore worker units from pre-image; leave P0–P5 receipts intact. Never power-cycle 138 for a test.

— SECURITY_GOVERNOR · P6 ACCEPTANCE CONDITIONAL_PASS · no fake 24h · jsonl preferred · JetStream=1 consumer+proof max
