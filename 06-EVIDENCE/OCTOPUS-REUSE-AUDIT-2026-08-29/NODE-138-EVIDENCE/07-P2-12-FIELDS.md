---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [octopus, node-138, p2, owner-decide]
created: 2026-08-29
updated: 2026-08-29
created_by: agent
language: en
sources:
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/P2-DISCOVERY/03-OWNER-DECIDE-12-FIELDS]]"
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/runtime-provenance-20260828T230743Z/owner_decision.p2]]"
  - "[[03 - Projects/OFN-Board/ofn/node.py]]"
---

# 07 — P2 twelve fields

```text
observed_at=2026-08-29T05:32:32Z
method=138_grep_owner_decide_plus_vault_node_plus_owner_decision.p2
scope=this_host_only
P2_CANONICAL_FIELDS=0
P2_MISSING_FIELDS=9
LOCAL_MINTING=FORBIDDEN
```

## Live command (138 + vault same shape)

138 `node.py:3112` `owner_decide(item_id, approve, confirmed_twice)` → `outbox.approve_manual` (`:3157`). Grep found **no** `OwnerDecision` / `witness_mint` on that path.

Vault `node.py:3081-3137` / `http_api.py:1284-1295`: `POST /api/v1/decide` `{id, approve, confirmed_twice}`.

Truth: `LIVE_VERIFIED` (138 line numbers) + `REPO_VERIFIED` (vault).

Card schema: `owner_decision.py` on 138 disk (sha `6cc5d878…`); `DECISION_FIELDS` twelve names. `validate()` checks presence/hex/expiry shape, **not** `sha256(exact_payload)==payload_sha`. `run.py` does not import it for HTTP.

Telegram contract (`docs/audit-138/138-TELEGRAM-CONTRACT.md`) uses `payload_sha256` / `artifact_sha256` / `verdict_sha256` / extra `policy_sha256` — **name CONTRADICTED** vs `OwnerDecision`.

## Field table

| Field | Type | Required | Producer | Store | Provenance | May default | Status |
|---|---|---|---|---|---|---|---|
| decision_id | str | yes | UNKNOWN | none | none | no | MISSING |
| run_id | str | yes | UNKNOWN | none at decide | none | no | MISSING |
| lane | str | yes | UNKNOWN (tenant neighbor) | tenant only | CLAIM if mapped | no | MISSING |
| action | str | yes | enqueue `kind` | `OutboxItem.kind` | CLAIM kind≡action | no | AVAILABLE_UNVERIFIED |
| recipient_masked | str | yes | UNKNOWN | none; packet returns raw `target` | CLAIM | no | MISSING / CONTRADICTED vs packet |
| exact_payload | str | yes | first of text\|caption\|message later | payload dict | CLAIM first-wins | no | DERIVABLE_LOSSY |
| payload_sha | str 64hex | yes | intended sha256(exact_payload) | none at decide | three hash objects | no | MISSING |
| artifact_sha | str 64hex | yes | UNKNOWN | none | witness uses `artifact_sha256` | no | MISSING |
| verdict_sha | str 64hex | yes | UNKNOWN | ledger VERDICT ≠ this | CLAIM | no | MISSING |
| idempotency_key | str | yes | enqueue caller | `outbox.idem_key` scoped | CLAIM scoped vs card | no | AVAILABLE_UNVERIFIED |
| expires_at | str Z | yes | UNKNOWN | none on item | CLAIM | no | MISSING |
| rollback | str | yes | UNKNOWN | none | CLAIM | no | MISSING |

```text
TWELVE_FIELDS_TOTAL=12
TWELVE_FIELDS_CANONICAL=0
TWELVE_FIELDS_AVAILABLE_UNVERIFIED=2
TWELVE_FIELDS_DERIVABLE_LOSSY=1
TWELVE_FIELDS_MISSING=9
OWNER_DECISION_DATA_AVAILABLE_AT_APPROVAL=false
```

Forbidden still: local UUID, wall-clock stamp, empty/zero fill, witness mint inside `owner_decide`, enqueue before binding.

source: P2-DISCOVERY/03 + 138 `owner_decision.py` + vault `node.py` · observed_at: 2026-08-29T05:32:32Z · truth: `REPO_VERIFIED` / `LIVE_VERIFIED` file presence
