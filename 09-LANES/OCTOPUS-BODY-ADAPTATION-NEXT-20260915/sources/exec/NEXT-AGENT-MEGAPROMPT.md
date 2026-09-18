# NEXT-AGENT-MEGAPROMPT — OCTOPUS PERSISTENT FLEET P5→P6 (+ HW T3 follow-on)
**Lane successor of:** `09-LANES/OCTOPUS-PERSISTENT-FLEET-EXEC-20260915`
**Also continues:** `09-LANES/OCTOPUS-HARDWARE-EXEC-20260915` (T3 model-server; Gate A still open)
**Written:** 2026-09-15T03:47:52Z · **Author:** OCTOPUS_COMMANDER (verified on-disk before write)
**Repository:** `F:\backup` · **Primary contract:** `F:\backup\AGENTS.md`
**Owner GO in force:** full persistent-fleet proposal after SEC (GO-PERSISTENT-FLEET-EXEC)
**SEC SoT:** sha256 `52887e1a088d6d4e87f2a8c14879db392a647d450afe8473ea0a5e620022d268` · P4 addendum `db62b3357c24f464b047926a51132829f08f7dc9222f58bcf4df033d59f2a0a9`
**Proposal SoT:** `HARDWARE-HANDOFF-REVIEW-20260915/PERSISTENT-FLEET-PROPOSAL.md` sha `e5cacff06435af1d6da95d339d4e4dbb58c09b32384758dfa33bc6f805053ba9`

> **Persian owner intent:** مغز ناوگان باید بدون لپ‌تاپ ادامه دهد؛ کیفیت پاسخ + حافظه پایدار هدف است، نه پر کردن CPU/NPU.
> **HOLD:** `customer_send=false` · `may_authorize=false` · never power off 138 · **no dual-commander** · no B4 · no invent usable 42 TOPS.

---

## 0. READ FIRST (this order)

1. This file (claims below are **re-hashed on disk** at write time — do not trust chat memory).
2. `09-LANES/OCTOPUS-PERSISTENT-FLEET-EXEC-20260915/LANE-REPORT.md` (must say P0–P4 COMPLETE).
3. Receipts: `P0/P0-DISCOVERY.json` · `P1/receipts/P1-DRY-PERSIST-RECEIPT.json` · `P2/P2-DRY-BOOTSTRAP-RECEIPT.json` · `P3/P3-VERIFIED-RESTORE-RECEIPT.json` · `P4/P4-NODE-AUTH-RECEIPT.json`.
4. `P4/P4-7ROW-MATRIX.json` + `P4/registry.jsonl` + `P4/proofs/auth_proof.v1.{100,160,193,114}.json`.
5. HW: `09-LANES/OCTOPUS-HARDWARE-EXEC-20260915/T2-PILOT/T2-NPU-INFERENCE-MATRIX.json` · `WORKER-CONNECT/`.
6. Proposal acceptance table in `PERSISTENT-FLEET-PROPOSAL.md` (future targets — not already-passed tests).

**Truth hierarchy:** runtime output > repository file > fresh handoff > old notes.
Chat / agent memory / this megaprompt narrative are **not** evidence. Re-hash before claiming.

---

## 1. VERIFIED STATE (2026-09-15 re-check) — do not regress

| Phase | Verdict | Receipt sha256 (prefix) | Key fact |
|---|---|---|---|
| P0 | PASS_WITH_CAVEAT | `a2bd6c1233e7…` | NATS+JetStream **YES on 182**; **consumers=0**; NATS absent on 138; `:8222` localhost |
| P1 | DRY PASS_WITH_CAVEAT | `a3d586b5ef2f…` | `fleet_facts.jsonl` on 138; `external_effects=0` |
| P2 | DRY PASS_WITH_CAVEAT | `8cb8c2960392…` | shadow jobs + idempotency tests; **NATS durability NOT_CLAIMED** |
| P3 | VERIFIED RESTORE PASS_WITH_CAVEAT | `83d525134317…` | 9/9 MATCH on 180 `/opt/octopus-restore-copies/p3-…/`; RPO/RTO addendum `5262d4eae453…` |
| P4 | **PASS** | `d8844e96dcd9…` | mesh_ssh FP `SHA256:vuyFXOS/CAXrxWbXlQSgq9eDB+MklKq1KkGJW4435as`; auth_status=OK ×7; LEASE_ELIGIBLE only 100/160/193/114; lease deny unregistered PASS |
| T2 NPU matrix | 6/7 PASS | `d13f19285482…` | 138 **NOT_RUN** (organism_optional_last); **deny** “42 TOPS usable/ready” |
| Worker HB | connected | WORKER-CONNECT | 100 retrieve / 160 prep / 193 model_infer / 114 eval_batch — **HB ≠ T3 model service** |

### P4 caveats (carry forward)
- Method = **mesh_ssh BatchMode + StrictHostKeyChecking** (SEC method A).
- `challenge_verify` / `hb_sig_verify` = `n/a_primary_mesh_ssh_batchmode` — do **not** claim HMAC path proven.
- Same mesh key fingerprint on all nodes is expected for this method; still DENY LEASE without registry `auth_status=OK`.
- P4 receipt `controls.stop_before_p5=true` was correct for that run — **this megaprompt opens P5**.

### Still false / forbidden claims
- JetStream brain is consuming while consumers=0
- NATS queue durable without consumer+ack proof
- 193 is a live model-server from heartbeat role string alone
- 42 TOPS unused capacity ready / measured usable TOPS
- Dual commander / customer_send / may_authorize=true

---

## 2. YOUR MISSION (next agent)

Finish the owner success definition: **better answers + durable memory + laptop-independent continuity**.

Execute under existing SEC `52887e1a088d…` unless SECURITY_GOVERNOR issues a tighter P5 addendum — then that addendum wins.

### Phase P5 — Bind workers into the real job path
**Owner:** PC_worker (implement) · ARCHITECT (contract) · SECURITY_GOVERNOR (gate) · QA_VERIFIER (seal)

1. **Canonical producer → queue → consumer → receipt** on one job_type first (shadow→live). Prefer **file/jsonl path on 138** that already exists from P2 unless SEC approves a **new** JetStream consumer on 182.
2. If JetStream: create **exactly one** consumer with known durable name; prove `consumers>=1`, deliver, ACK, idempotent redelivery; **do not** dual-poll / dual-commander.
3. **DENY** reuse of revenue-drive / money APPROVE_PAT queues for brain jobs.
4. Workers **100 / 160 / 193 / 114** may take leases **only** when registry says `auth_status=OK` and `lease_eligible=true` (already true for those four).
5. 180 remains **quality / restore_copy_RO** — never commander.
6. 182 remains **lab_witness / NATS host** — independent check of artifacts, not a second writer of fleet memory.
7. Job contract (from proposal):
   `job_id, idempotency_key, job_type, input_ref/hash, required_capability, target_node_id, deadline, attempt, lease_owner, lease_expiry, resource_budget, result_ref/hash, receipt_id`
8. UNKNOWN on ambiguous post-crash; no blind retry of non-idempotent effects; no free-form shell as job_type.

**P5 exit:** at least one end-to-end leased job 138→worker→receipt with QA seal; consumers count proven if NATS path chosen; LANE-REPORT updated; STOP gate before claiming P6 acceptance.

### Phase P6 — Owner acceptance tests (measure, don’t invent)
Run proposal acceptance table as **PB-1…PB-6** with receipts (table is aspirational — record PASS/FAIL/NOT_RUN/UNKNOWN honestly):

| ID | Test | Minimum witness |
|---|---|---|
| PB-1 | Continuity without laptop execution dependency | Pre-registered allowed jobs schedule/run/result on fleet; local Q/A sample |
| PB-2 | Worker restart / brief disconnect | Lease+deadline correct; no lost job; duplicate effects=0; UNKNOWN preserved |
| PB-3 | Restore to separate path | Manifest match + replay/readback; measured RPO/RTO (P3 baseline exists) |
| PB-4 | Answer-with-memory A/B | Quality+latency on held-out questions with/without retrieval |
| PB-5 | NPU honesty | Output correctness, model/runtime hash, n, p50/p95, throughput, device witness — **nominal TOPS only** |
| PB-6 | Expand matrix | Seven-row PASS/FAIL/NOT_RUN/UNKNOWN with fixed denominator; RAM/temp/error per board |

**P6 exit:** acceptance matrix filed; no claim of 24h independence without wall-clock evidence; CPU/NPU “full” is **not** success.

### Parallel hardware follow-ons (same HOLD rules)
| ID | Work | Note |
|---|---|---|
| T3 | Real **model-server service** on 193 | systemd unit + health endpoint + version hash; HB role string insufficient |
| T4 | Static IP / MAC SD↔eMMC plan | Plan+receipt; **not** one-reboot flip without preimage |
| Gate A | Fleet NPU | Still open while 138 NOT_RUN; optional_last only with organism care |
| W24 | Telegram glass getUpdates | **Parallel organism queue**; sole poller; DENY dual getUpdates; binder ARMED but LIVE-INGEST not proven |

---

## 3. ACCESS / SAFETY

- Mesh key only from 138: `ssh -i ~/.ssh/octopus_mesh_ed25519 root@192.168.0.<octet>`
- Registry live: `/home/ari/ofn/state/fleet-nodes/registry.jsonl` (P4 path) + mesh `nodes.json` (backup taken at P4)
- Never power off 138 · never dual-commander · never customer_send · never paste secrets into chat/repo
- Destructive / Class B / external: OWNER GO + SEC PASS required (this megaprompt does **not** widen that)

---

## 4. DELIVERABLES (write under new or same lane bag)

Suggested bag: `F:\backup\09-LANES\OCTOPUS-PERSISTENT-FLEET-P5P6-20260915\`

Must include:
- `LANE-REPORT.md` · `ACTIONS-LOG.md` · `EVIDENCE.md`
- `P5/*` receipts (job path + consumer proof if any)
- `P6/ACCEPTANCE-MATRIX.json` + per-test receipts
- Optional `T3/*` if hardware stream runs in parallel
- Final `NEXT-AGENT-MEGAPROMPT.md` only after re-hash (do not copy stale claims)

---

## 5. COORDINATION

- Organism owns green execute; HQ (COMMANDER) gates/witnesses.
- One owner per work item; QA seals PC/ARCH; SEC reviews credentials/publish/delete/remote-write.
- Update stale docs: any LANE-REPORT saying “STOP before P4” after P4 PASS is **obsolete**.

---

## 6. HASH PIN (re-verified at megaprompt write)

```
P0-DISCOVERY.json                         a2bd6c1233e7eb6d348cb9bdb36d2267c7b9e12d629dd1fedfce9db31964e4d9
P1-DRY-PERSIST-RECEIPT.json               a3d586b5ef2f5ca6aa4ee358f7a710a7e3dfa1a169190b48db97a89d1fcf9c3d
P2-DRY-BOOTSTRAP-RECEIPT.json             8cb8c296039209c25730106c571d4a489ff87d1982939b6942a364c7075166fc
P3-VERIFIED-RESTORE-RECEIPT.json          83d525134317e7b2de93986684309ba2bb4bd96b9ee79566e5494035bf801d11
P3-RPO-RTO-ADDENDUM.json                  5262d4eae4531b9b76cfcbc3068a3abbdc86cb2993c6a6b61f29a1604d656335
P4-NODE-AUTH-RECEIPT.json                 d8844e96dcd9b6f81bba3825af9a9128347a123fc298cefacab9c565e5da2036
P4-7ROW-MATRIX.json                       bbf340969a0eb6c921f019c56934e120d25babd92c49a86d7250920c74136498
P4 registry.jsonl                         01dc6eeb635b79d7469ec3d570a0306610cc1484ad64f14bc21bc6c4170dee98
T2-NPU-INFERENCE-MATRIX.json              d13f19285482a2a346b8b26979f2341c8f7a4ccef50c281967e47cabfc469df5
GO-PERSISTENT-FLEET-EXEC SEC              52887e1a088d6d4e87f2a8c14879db392a647d450afe8473ea0a5e620022d268
SEC-NODE-ID-AUTH-ADDENDUM                 db62b3357c24f464b047926a51132829f08f7dc9222f58bcf4df033d59f2a0a9
ARCH P4 design                            8b0a5e03c4df626cb735a54ba16e0a02c948f23c9a9066d7fe0354e107316cd2
PERSISTENT-FLEET-PROPOSAL.md              e5cacff06435af1d6da95d339d4e4dbb58c09b32384758dfa33bc6f805053ba9
```

---

## 7. FIRST COMMANDS (suggested)

```bash
# From 138 as ari — re-prove consumers still 0 before inventing durability
ssh -i ~/.ssh/octopus_mesh_ed25519 root@192.168.0.182 'curl -s http://127.0.0.1:8222/jsz | head'
# Re-hash P4 receipt on laptop bag
sha256sum /path/to/P4-NODE-AUTH-RECEIPT.json
```

Then design P5 with ARCH+SEC **before** live consumer create.

END OF MEGAPROMPT
