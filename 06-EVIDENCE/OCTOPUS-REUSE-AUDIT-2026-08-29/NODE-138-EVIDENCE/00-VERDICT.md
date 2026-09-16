---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [octopus, node-138, ofn-body, forensic]
created: 2026-08-29
updated: 2026-08-29
created_by: agent
language: en
sources:
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/P1-RESULT]]"
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/P2-DISCOVERY/00-VERDICT]]"
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/runtime-provenance-20260828T230743Z/CHECKPOINT]]"
  - "[[06-EVIDENCE/OCTOPUS-L191-FINDINGS-2026-08-28]]"
  - "[[06-EVIDENCE/OCTOPUS-TELEGRAM-WEBAPP-PHASE0-2026-08-29]]"
  - "[[02-DECISIONS/A2-001-MIRROR-MANIFEST-VERIFIER]]"
---

# NODE-138-EVIDENCE — Verdict

```text
node_id=191
asserted_ip=192.168.0.191
hostname=DESKTOP-KA9RFN5
claimed_session_role=octopus-continuity-180_quality_brain
live_host_role=vault_191
vantage=ssh_readonly_191_to_138
target_node_id=138
target_asserted_ip=192.168.0.138
target_hostname=DietPi
scope=this_host_only
claim_type=observation
observed_at=2026-08-29T05:32:32Z
OFN_138_RUNTIME=LIVE_VERIFIED
SECRETS_READ=NO
RUNTIME_CHANGES=0
EXTERNAL_EFFECTS=0
MARK_AS_FIXED=NO
```

This pack is read-only forensic evidence of the OFN body on 138. It does not implement, patch, restart, or mark fixed. SSH used BatchMode + existing `ari@192.168.0.138` identity; no secret file was read; no queue was consumed; no Telegram call was made.

```text
NODE=138
DISCOVERY_STATUS=COMPLETE
ROLE_STATUS=DISPUTED
CANONICAL_USER=ari
CANONICAL_HOME=/home/ari
OFN_REPO=/home/ari/ofn
OFN_HEAD=a27eb0536793c7fc040917bb645e9057707298f4
RUNTIME_COMMIT=UNPROVEN_PRE_P1
SAFE_TESTS=NOT_RUN
P1_REPO_IMPLEMENTED=YES
P1_RUNTIME_LOADED=NO
P1_FRONTEND_VISIBLE=NO
P2_CANONICAL_FIELDS=0
P2_MISSING_FIELDS=9
TRANSMIT_PATHS=PATH_A,PATH_B
DUPLICATE_EFFECT_POSSIBLE=YES
EDGE6_FIRST_MISSING_STAGE=proposal_enqueue
TELEGRAM_EXISTING_COMPONENTS=5x_OFN_BOT_TOKEN_NAMES,publish_to_telegram,ConsentStore,alert.py,telegram_channel.py,telegram_readonly.py,MiniApp_HMAC_tests,legacy_panel,/api/v1/decide,Cockpit_V2_GET
T1_STATUS=PARTIAL
T2_STATUS=PARTIAL
T3_STATUS=PARTIAL
T4_STATUS=PARTIAL
T5_STATUS=PARTIAL
NEW_SUBSYSTEMS_REQUIRED=0
RUNTIME_CHANGES=0
EXTERNAL_EFFECTS=0
SECRETS_READ=NO
EVIDENCE_PATH=06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/NODE-138-EVIDENCE
EVIDENCE_SHA256=46bf0c32efce8c2c17b1bd8671202ff67eac395fec4452515bacc4e9ca41509f
READY_FOR_FINAL_PROMPT=YES
```

`EVIDENCE_SHA256` is filled after `hashes.sha256` is written (hash of that file).

## Binding (do not execute)

| Gate | Value | Truth |
|---|---|---|
| P1 source on `/home/ari/ofn` | `a27eb05` four files; parent `6881337` | `LIVE_VERIFIED` |
| P1 in PID `1351408` | No — process started 2026-08-27 11:33:39 AEST | `LIVE_VERIFIED` |
| P2 bind / local mint | Blocked; 12-field card unwired | `REPO_VERIFIED` |
| EDGE-6 patch | Not authorized; first missing stage is enqueue | `DOCUMENTED` |
| Signed mesh role registry | Not found | `NOT_FOUND` |
| New subsystem | Forbidden; reuse existing | `REPO_VERIFIED` |
