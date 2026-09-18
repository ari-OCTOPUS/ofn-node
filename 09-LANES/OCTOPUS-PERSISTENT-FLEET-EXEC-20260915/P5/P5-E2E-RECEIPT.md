# P5-E2E-RECEIPT

**verdict:** PASS
**stamp_utc:** 2026-09-15T03:53:05Z
**job_id:** `job-8f635a12d2cd4228`
**worker_node_id:** `100` (knowledge_retrieve)
**receipt_sha256:** `4ea146a86481707f15a726ba26d85b3c029d87079b68deb73f9fd84c462838b2`
**result_hash:** `14a99a95216456fc7c29fd719f85b02d66794a12e651c22202dd1a9ad9efb497`
**bus:** SHADOW_LOCAL_JSONL (`jsonl_138`)
**NATS_DURABILITY:** NOT_CLAIMED ? JetStream consumers=0 (unchanged)
**external_effects:** 0 ? customer_send: HOLD false

## Citations
- EXIT receipt contract sha256: `5d12e068568cdcc694ac1c8de6c5e36c623832727244814a36303ed7862c82d7`
- SEC-P5-JOB-PATH-GATE sha256: `3e8bd525748531e747761cfaa4345b8a39af8758ea3bf7c565e3da1ea8ba27ec`
- P4-NODE-AUTH-RECEIPT sha256: `d8844e96dcd9b6f81bba3825af9a9128347a123fc298cefacab9c565e5da2036`
- fleet_job.v1.schema sha256: `49eb6c0be2f4a9afbd0520feba4cff00500bab73f4b5eae7a89695138ab70d59`

## Path
138 producer ? fleet_jobs.jsonl ? LEASE worker 100 ? RUNNING (mesh SSH work) ? ACK_RESULT ? PERSISTED ? CLOSED

## Proofs
- lease DENY unregistered 999: REJECTED: LEASE DENY auth_status=UNREGISTERED for node_id=999 (need OK)
- shell job_type DENY: REJECTED
- idempotency re-submit key `p5-e2e-100-1789444384` ? hit, no dup side effects
- worker result: `/var/lib/octopus-worker/jobs/job-8f635a12d2cd4228.json` hostname=octopus-compute-100 boot_id=1d9d56a9-9591-451e-bdbe-a04f2c898a3a

## STOP
STOP before P6. QA seal next.
