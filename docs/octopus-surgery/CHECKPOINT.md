---
type: reference
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [octopus, surgery, checkpoint, evidence]
created: 2026-08-30
updated: 2026-08-30
created_by: agent
sources:
  - "[[INDEX]]"
  - "[[06-REALITY-MANIFEST.yaml]]"
---

# Surgery 1 closure checkpoint

Default arbiter envelope:

```yaml
node_id: octopus-continuity-180
asserted_ip: 192.168.0.180
vantage: canonical-vault-this-host
scope: this_host_only
claim_type: verified_provenance
```

## Accepted result

- Outcome: `TEST_ONLY_GUARD`
- Production behavior changes: `0`
- Narrow cognition separation: `VERIFIED` only for sources enumerated by the policy.
- Cortex → provider: `SAFE_INFERENCE_BOUNDARY`.
- Provider adapters retain model-network and provider-credential capability.
- `code_brain → code_autonomy`: `APPROVED_EXECUTOR_BOUNDARY`.
- `27/27`: 27 checks executed by one verifier; 27 independent verifiers is `CONTRADICTED`.
- OFN `secret_rotation` is separate from rotation-vault mechanisms.

## Provenance values

```text
parent_manifest_sha256=e09ee5dc550d0191a73571b8881d90192a892a6895c7133beea9f684f2cbe34c
surgery_receipt_sha256=59785c8f5f3d856d07f637386156fe0bc5753df3cc78370e269861d8c22af8a2
resulting_manifest_sha256=b7f6a38aeb33cf503b059a6c24b7d1de9b48914089ca5749e86f8a0b1e9fb017
surgery_commit=57e1a2fecb770b62c459b67c10ff450fdcbe8632
```

These are separate provenance values. The valid manifest and receipt were not
rewritten to contain their own hashes.

## Safety totals

```text
pushes=0
merges=0
deployments=0
runtime_restarts=0
provider_calls=0
external_effects=0
owner_gates_modified=0
```

## Completion estimates

```text
CODE_COMPLETION=63% ± 7%
EVIDENCE_COMPLETION=57% ± 8%
OPERATIONAL_COMPLETION=31% ± 9%
OVERALL=45% ± 7%
```

The documentation-sync commit is reported out-of-band because embedding its own
commit SHA would be self-referential.

## Surgery 2 delta

- Caller inventory: `8/8` after registering four routed callers and one lab-gated caller.
- Gateway classification: `ISOLATED_LAB_ONLY`.
- Production importers of the lab gateway: `0`.
- Explicit gate requires lab/test zone, approved entrypoint, and non-executable/no-external-action request.
- Receipt SHA-256:
  `fb3bbcd423e6cfc56132756699bcade58abb950e1d988813da7586a72bf412d8`.
- GitHub publication is blocked because `github/main` and this vault lineage have no merge base.

## Surgery 3 delta

- Hermetic boundary contract: `7/7`.
- Registered invocation: `1/1`; inner checks `7/7`.
- Runner scoring regressions: `14` passed.
- Cortex harness: `6/16 → 16/16` through explicit module import.
- Live provider test default admission: expected exit `2`, no provider call.
- Hermetic default inventory: `826` candidates; one live suite explicitly excluded.
- Receipt SHA-256:
  `2e3c8eab3bc102dd7afff4e3b9822099f1b02dc952da3e4e58c41ed7f7b3e6b5`.

## Surgery 4 delta

- `run_observatory.py`, Bayesian strategy, live verifier and backtest executable:
  `NOT_FOUND_IN_CURRENT_LINEAGE`.
- Referenced commits `43fd377`, `18fd88a`, `e3e9d36`: absent from the object database.
- Historical Desktop working path and runtime databases: absent on this host.
- Current Brier values, sample counts, CI and leakage checks: not reproducible.
- Provenance gap receipt SHA-256:
  `a23a780af5bb861591a7daf0f0596b1c6c135c80934ccb29960ab2a6494f5713`.

## Surgery 5 delta

- New modules: `_ops/observatory/observation_record.py`, `replay_adapters.py`.
- Existing USGS/HN parser was not replaced.
- Foundation tests: `15/15`.
- Real sensor connected: `false`.
- Receipt SHA-256:
  `c7cd3103d09f84ac24e7f05dfc07ad6d338235ce0b2f772d147058013deeb0d1`.

## Campaign closeout

- Files 09–14 added.
- GitHub push/PR: `BLOCKED_PUBLIC_UNRELATED_HISTORY`.
- Implementation HEAD: `1a18c3e6559f5e7a548751d19dc80f1dadec96a6`.
- Closeout commit SHA is reported out-of-band.
