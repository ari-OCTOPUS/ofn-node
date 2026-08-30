---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [octopus, telegram, webapp, evidence-first, phase0]
created: 2026-08-29
updated: 2026-08-29
created_by: agent
language: fa
sources:
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/P1-RESULT]]"
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/P2-DISCOVERY]]"
---

# OCTOPUS Telegram/WebApp — Phase 0 Synthesis

```text
RUN_ID=tg-web-debug-20260828T233407Z
VERDICT=EDGE6_STILL_BLOCKED
NODES_READ=191,180,138,182
PATCHES_DURING_PHASE0=0
RUNTIME_CHANGES=1_TRANSIENT_CONTAINED
EXTERNAL_EFFECTS=0
MARK_AS_FIXED=NO
```

## Arbiter envelopes

- `node_id=191` · `asserted_ip=192.168.0.191` · `vantage=this_host`
  · `scope=this_host_only` · `claim_type=observation/inference`
  · evidence: process/port tables, loaded source, immutable SQLite aggregates.
- `node_id=180` · `asserted_ip=192.168.0.180` · `vantage=read-only SSH`
  · `scope=this_host_only` · `claim_type=observation/inference`
  · evidence: systemd/procfs, source control flow, proposal/registry artifacts.
- `node_id=138` · `asserted_ip=192.168.0.138` · `vantage=read-only SSH`
  · `scope=this_host_only` · `claim_type=observation/inference`
  · evidence: ofn.service, Git, source, SQLite read-only, loopback GET.
- `node_id=182` · `asserted_ip=192.168.0.182` · `vantage=read-only SSH`
  · `scope=this_host_only` · `claim_type=observation/inference`
  · evidence: witness timer/source, signed receipt, queues, NATS/MQTT metadata.

System-wide conclusions below require corroboration from at least two nodes.

## Findings

### EDGE-6

Same-run closure is absent across 180/138/182:

- 180 last proven step: `live_spine_run` registry persistence.
- no same-run proposal enqueue/claim/effect ACK/ledger hash.
- 182 receipt is signature-valid and includes the run in nested metadata, but
  lacks durable source bytes, canonical proposal/effect IDs and effect ACK.
- transport ACK proves transport acceptance, not effect completion.
- receipt `630c5060…` is a notification-envelope hash, not receipt SHA.

The previous root cause “materializer returns before enqueue” is incomplete.
Current 180 caller already has persist/transmit, while current disk also has a
later inline transmit using a synthetic run ID. Future execution can attempt
two semantic deliveries. The target run predates the inline change and was not
replayed.

### Truth surfaces

- approval aggregates are different stores: 191 observed 4, 29, 0 and 40;
  138 business outbox pending/held is 0.
- beat values are distinct namespaces: organism 54026, cortex 8,
  business-brain snapshot 240, separate heart counters.
- UI must label source, observed_at and freshness instead of forcing equality.

### Confirmed local defects

1. Node 191 lifecycle API removes `rfc_id`; renderer requires it and produces
   `undefined`. Scope: 191 only.
2. Node 191 timeout budget: gateway 55s < provider socket need 61.5s <
   browser 90s. Historical request causality lacks request ID/stage timing.
3. Closed paid activation is labeled provider/model failure instead of
   `POLICY_FALLBACK`. Scope: 191.
4. Node 138 queue scan can exhaust shared `MAX_FILES=2048` on >3871 receipt
   claims before reading inbox/outbox, yielding empty mesh `items`.
5. P1 `owner_items` exists on disk at `a27eb05`, but live PID is pre-P1 and
   current `queue.js` ignores `owner_items`.
6. `flag_drift.is_secret_name()` omitted `BEARER`; a diagnostic snapshot could
   retain a bearer-like value. Value was not copied into evidence.

### Not defects

- reboot-correlated revive cluster after the 08:08 boot.
- different beat numbers when namespaces differ.
- four sandbox approvals hidden by an explicit filter.
- HTTP 401 on auth-required ports.
- open port alone as proof of loop progress.

## Safety incident

The 182 audit ran one malformed process probe that transiently spawned an
extra mosquitto process. Temporary PIDs were terminated; baseline PID 382176
remained. No service/config change persisted. This is
`RUNTIME_CHANGES=1_TRANSIENT_CONTAINED`, not zero.

## Minimal patch queue

1. Secret redaction — `_ops/flag_drift.py` +
   `_ops/tests/test_flag_drift.py`.
2. Undefined fail-closed — MiniApp `app.js` + existing UI test.
3. Queue budget partition — OFN `cockpit_v2_read_model.py` + existing test.
4. Owner-items rendering — OFN `queue.js` + frontend test, after controlled
   P1 runtime load.
5. EDGE-6 — no safe patch until duplicate 180 transmit paths and dirty tree
   are reconciled in an isolated worktree.

## Security patch status

An isolated patch added `BEARER` to the canonical secret-token classifier.

```text
WORKTREE=C:\Users\Armin\.zcode\tmp\octopus-flag-redaction-20260829
BRANCH=fix/bearer-secret-redaction-20260829
COMMIT=00c4fbf
RED=34 total; 2 failures
GREEN=34 total; 0 failures
SHARED_TREE_CHANGED=false
RUNTIME_DEPLOYED=false
```

Published to local `E:\germline\octopus.git`. This repository has no GitHub
remote, so GitHub publication is `BLOCKED_REMOTE_UNLOCATED`; no unrelated
repository was used as a substitute.

## Undefined-card fail-closed patch

The confirmed 191 renderer mismatch was reproduced and fixed in an isolated
branch:

```text
BRANCH=fix/miniapp-undefined-card-20260829
COMMIT=0016cdf
RED=11/12; missing ID rendered "undefined" with 2 approve + 2 reject buttons
GREEN=12/12; missing ID read-only, valid ID keeps 1 approve + 1 reject
RELATED_LIFECYCLE_SUITE=16/16
TARGETED_TOTAL=28/28
SHARED_TREE_CHANGED=false
RUNTIME_DEPLOYED=true
GATEWAY_PID=26892
```

The backend privacy contract remains unchanged: public lifecycle data may omit
`rfc_id`. The frontend now fails closed instead of inventing `"undefined"` as
an action identity. Live loopback returned 200 for `/miniapp` and `/app.js`;
the served asset contains the fail-closed branch. A fresh authenticated
`/api/lifecycle` hit and owner observation confirmed the result; instrumentation
was removed in cleanup commit `1c163ea`.
