# P4 node_id credential — SEC addendum (idle workers)

- **task_id:** SEC-NODE-ID-AUTH-ADDENDUM
- **owner:** SECURITY_GOVERNOR
- **stamp_aest:** 2026-09-15 ~13:38
- **binds:** EXEC `52887e1a…` · IDLE-WORKER `0a634c9d…` · QA-WORKER-CONNECT PASS_WITH_CAVEAT (credential **NOT PROVEN**)
- **HOLD customer_send:** true · **may_authorize:** false · **commander:** 138 only

QA is correct: heartbeat `node_id` + `boot_id` + hostname **≠** authenticated credential bind.

---

## Verdict

**CONDITIONAL_PASS — mechanism named; proof still owed**

Install/HB on 100/160/193/114 may stay as **ENROLLED_PENDING_AUTH**.  
**LEASE_ELIGIBLE / QUEUED→LEASED** to those nodes remains **DENY** until a proof receipt lands.

---

## Allowed mechanism (pick one primary; do not invent a third)

### A — Preferred: mesh SSH identity (existing organism path)

1. Worker authenticates to 138 mesh using its **existing board SSH key** (or mesh join key already on node).  
2. 138 registry row (`fleet_worker_bind.v1`) stores:  
   - `node_id` (stable program id, not raw machine-id)  
   - `cred_kind: mesh_ssh`  
   - `cred_fingerprint` = SHA-256 of **public** key only  
   - `auth_status: OK` only after 138 verifies a signed/authenticated enrollment push from that key  
3. Heartbeats accepted only over that authenticated channel (or include `ssh_session_proof` / pull by 138 via BatchMode from registered host).  
4. **Never** paste private keys / tokens into chat, logs, or HQ bags.

### B — Alternate: node HMAC token (if mesh already uses secrets.env pattern)

1. On worker only: random token in existing secrets path (`~/.config/ofn/` or mesh-equivalent) — generate on-box.  
2. Registry stores `cred_kind: hmac_v1` + `token_id` + `token_sha256` (hash only).  
3. Each HB: `sig = HMAC-SHA256(token, node_id|boot_id|seq|at)` (exact field order fixed in receipt).  
4. 138 verifies sig; mismatch → `auth_status=REVOKED` / drop.

**DENY as auth:** hostname alone · IP alone · raw `machine-id` · unsigned JSON drop on 138 · cloning another board’s `node_id`.

---

## Proof receipt (closes QA caveat)

PC files under WORKER-CONNECT / PERSISTENT-FLEET-EXEC:

```
auth_proof.v1 {
  node_id, lan_octet, cred_kind,
  cred_fingerprint_or_token_sha256,  // never raw secret
  auth_status: "OK",
  verified_at, verifier: "138",
  method: "mesh_ssh"|"hmac_v1",
  commander_node_id: "138",
  may_authorize: false,
  customer_send: false
}
```

Four boards → four proofs (or one INDEX listing four OK rows). QA re-hash → then `LEASE_ELIGIBLE`.

---

## Until proof

| state | allowed |
|-------|---------|
| ENROLLED_PENDING_AUTH | HB timers may run; observed on 138 |
| LEASE_ELIGIBLE | **DENY** |
| dual-commander / may_authorize flip | **DENY** |
| customer_send | **HOLD** |

— SECURITY_GOVERNOR · NODE-ID AUTH ADDENDUM · QA caveat stands until proof
