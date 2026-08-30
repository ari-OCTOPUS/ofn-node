# Public PR statements

1. Changes were selectively reapplied from a separate local germline lineage.
2. Local vault history was not published.
3. All included code was retested against GitHub main.
4. Omitted local surgeries: cognition deny-list, LLM inventory, lab gateway, hermetic runner, cortex import fix, observatory recovery.
5. This PR does not authorize deployment.
6. This PR does not open D1, D7, OWNER_KEY or secret rotation.
7. No live provider call was performed.
8. No physical sensor was activated.
9. Opening the PR does not change production behavior.

# Final campaign report

Envelope: `node_id=octopus-continuity-180`, `asserted_ip=192.168.0.180`,
`vantage=isolated-worktree`, `scope=this_host_only`.

## Campaign result

- Repository: `<vault-root>` via isolated worktree
  `<isolated-surgery-worktree>`
- Germline remote: `<germline-remote>`
- GitHub remote: `https://github.com/ari-OCTOPUS/ofn-node.git` (PUBLIC)
- Original commit: `2a718aaa96235fcf5aa5219d25eba4a9b314eed5`
- Final branch: `surgery/cognition-authority-denylist-20260830-170620`
- Implementation HEAD: `1a18c3e6559f5e7a548751d19dc80f1dadec96a6`
- Closeout HEAD before OWNER-09: `b394b999b43ab12573ad574f33a5621a57c66686`
- OWNER-09 first record: `470bb6031f1e51c9a8e6e1f1536c349e22a5200e`
- Scoring repair: `d6eeadd40d867bdc082dbc287c48e24be280a335`
- Campaign status: recorded after local finalize; see OWNER-09
- OWNER-09 status: `HERMETIC_BOUNDARY_VIOLATION`
- OWNER-09 rerun: `2026-08-30T09:29:42Z`–`09:54:01Z`, 1459s, 770/827 passed, 57 failed, 1 live skipped
- Scoring after repair: 14/14 via `run_all --only`; full 827 not rerun
- GitHub PR at this local finalize: pending Phase K/L
- CI status: inspect after public export SHA

## Surgeries completed

| Surgery | Outcome | Commit | Tests | Receipt |
|---|---|---|---|---|
| 1 cognition deny-list | TEST_ONLY_GUARD | `57e1a2fecb770b62c459b67c10ff450fdcbe8632` | 11/11 | `59785c8f5f3d856d07f637386156fe0bc5753df3cc78370e269861d8c22af8a2` |
| 2 LLM inventory + lab gate | ISOLATED_LAB_ONLY | `ba717a277a355cf81a52ca8c848f4cc7b0b22522` | 8/8 inventory; 11 gateway | `fb3bbcd423e6cfc56132756699bcade58abb950e1d988813da7586a72bf412d8` |
| 3 hermetic runner | HERMETIC_DEFAULT_BOUNDARY_ENFORCED | `09dc566254b645e5a7e0ae288f94c4bf2d3ec690` | 7/7; cortex 16/16 | `2e3c8eab3bc102dd7afff4e3b9822099f1b02dc952da3e4e58c41ed7f7b3e6b5` |
| 4 observatory provenance | NOT_FOUND_IN_CURRENT_LINEAGE | `aa2b816946a4f4caee662ebcc8a307743061e567` | search only | `a23a780af5bb861591a7daf0f0596b1c6c135c80934ccb29960ab2a6494f5713` |
| 5 observation.v1 foundation | REPLAY_SAFE_FOUNDATION | `1a18c3e6559f5e7a548751d19dc80f1dadec96a6` | 15/15 | `c7cd3103d09f84ac24e7f05dfc07ad6d338235ce0b2f772d147058013deeb0d1` |

## Claims corrected

| Claim | Previous state | Final state | Evidence |
|---|---|---|---|
| 27 independent verifiers passed | contradicted historical claim | 27 checks by one verifier | Surgery 1 receipt and canonical notes |
| 320 tests green | stale | contradicted by OWNER-09 | 770/827 hermetic passed; 57 failed |
| observation.v1 absent | contradicted | parser existed; record contract now added | `observation_record.py` 15/15 |
| run_observatory.py present | assumed | NOT_FOUND_IN_CURRENT_LINEAGE | Surgery 4 gap receipt |
| OCTOPUS score = 0.80 | stale narrative | NOT_REPRODUCED | no claim store on this host |
| cognition has no executor handle | over-broad | narrow set verified; code_brain is approved executor | AST policy |
| lab gateway safe for production | unfenced callable | ISOLATED_LAB_ONLY | Surgery 2 |

## Test state

| Suite | Before | After | Notes |
|---|---|---|---|
| cognition authority | absent | 11/11 | new |
| LLM inventory | 5/6 | 8/8 | fixed stale inventory |
| lab gateway | unfenced | 11 pytest + gate tests | fail-closed |
| cortex harness | 6/16 | 16/16 | explicit module import |
| hermetic runner | non-hermetic default | 7/7 | live suite excluded |
| observation.v1 foundation | absent | 15/15 | replay/fake only |
| NBB | 189/189 historical this campaign | not re-run in closeout | preserved |
| full hermetic default | NOT_RUN | 770/827; 57 failed | OWNER-09 `HERMETIC_BOUNDARY_VIOLATION` |
| live provider suite | present | preserved, not executed | expected block without two signals |

Fixed failures: inventory 5/6, cortex 6/16, unfenced lab gateway, missing observation record.
Preserved pre-existing: full-suite duration, allowlist `_hand_yaml` TypeError without PyYAML.
Blocked: GitHub CI, live provider, restore, Brier reproduction.
Live tests not executed: `test_llm_routing_smoke.py`.

## Architecture state

- cognition boundary: AST deny-list, inspected scope only
- cortex/provider: SAFE_INFERENCE_BOUNDARY
- proposal/approval: fail-closed; no self-approval
- executor: action_bridge plus approved `code_brain → code_autonomy`
- lab gateway: ISOLATED_LAB_ONLY, default deny
- test-runner: child env loopback-only; OWNER-09 still mutated tracked `_ops/state` and `06-EVIDENCE`
- observatory: body_not_on_this_host
- observation: replay-safe record; no real sensor

## Obsidian synchronization

- Canonical vault: `<vault-root>`
- Worktree docs are the campaign source of truth for surgeries 2–5
- Closeout files 09–14 exist in the worktree. Copy into the dirty primary vault is not Git/Obsidian synchronization.
- No `.bak` or archive notes were updated
- Absolute `.claude/worktrees/...` links must not appear in GitHub-facing text

## GitHub synchronization

- branches pushed: 0
- force pushes: 0
- direct main pushes: 0
- PR created/updated: NO
- merge performed: NO
- deployment performed: NO
- reason: public repository + unrelated history (github-only 155 / local-only 1835, no merge base)

## Distance to 90%

- Code completion: 63% ± 7% (was 56% ± 7%)
- Evidence completion: 60% ± 8% (was 41% ± 8%)
- Operational completion: 30% ± 9% (was 29% ± 9%)
- Overall: 45% ± 8% (was 39% ± 7%)
- Active cap: 50% (owner governance still closed)

## Owner-only actions

See [[09-OWNER-ACTION-RUNBOOK]] and [[13-OWNER-INBOX]].

## Safety proof

- provider calls: 0
- external effects: 0
- service restarts: 0
- deployments: 0
- hardware actions: 0
- financial actions: 0
- secret exposures: 0
- owner gates modified: 0

## OWNER-09 measurement

- Command: `python -X utf8 _ops/tests/run_all.py`
- Start/end: `2026-08-30T08:30:08Z` / `2026-08-30T08:54:14Z` (1446s)
- Passed 770 / failed 57 / live skipped 1 / timed out 0 / hermetic executed 827
- Exit 1
- Sanitized log SHA-256: `58125d4a2c8535f96e9de0d02c2fe824fb38c34addd3b2ad70b9278f969cd48e`
- Receipt SHA-256: `c6395c0308fef9d418d4375baf0037b4384db28a1230863a391e316c679a285f`
- Campaign regression: `test_run_all_scoring.py` (expects REVOKE)
- Residue: 12 tracked files restored with `git checkout --`
- Repairs: 0. Push: 0. Vault copy: 0.

## Surgery file list for any later designed export

```text
_ops/tests/architecture/cognition_authority_policy.yaml
_ops/tests/test_cognition_authority_denylist.py
_ops/tests/test_llm_call_inventory.py
_ops/tests/test_full_loop_flash_stage_a.py
_ops/lab/full_loop_flash/gateway.py
_ops/lab/full_loop_flash/stages.py
_ops/tests/run_all.py
_ops/tests/test_run_all_hermetic.py
_ops/tests/test_cortex.py
_ops/observatory/observation_record.py
_ops/observatory/replay_adapters.py
_ops/tests/test_observation_v1_foundation.py
docs/octopus-surgery/**
```
