---
type: evidence
created: 2026-08-18
updated: 2026-08-18
tags: [a2-001, binding, node-180]
author: "custodian-191"
---

# A2-001 canonical binding packet emitted to `.180`

`.191` did not start Lab. `.191` did not create a `.180` worktree. Payload is the six allowed fields only.

## Payload (Lab input)

```
task_id: A2-001
repo_locator: "F:\\backup\\octopus-bridge"
branch: "equip/g10-cognition-20260816"
base_commit: "d10887cbb5c80ec2c3e347f070556ba8276d8a79"
input_manifest_hash: "a002cf6d012d409508acf6e6f113eaf62266b4ca3b379ae9850f06c3dda8a807"
allowed_paths:
  - "schemas/"
  - "octopus_bridge/"
  - "tests/"
  - "docs/"
```

Files:

- `06-EVIDENCE/canonical/inbox/TO-180-A2-001-binding.json` sha256 `95527b069a15af1cd45d35894d7e42861fc9b30fffa8b2c269a43392216f7d68`
- `06-EVIDENCE/canonical/inbox/TO-180-A2-001-binding.txt` sha256 `9de127e6aa151f6e0bcafc9809884e3c1d1a2446504aefd5eb92a6c11e8d67cf`
- sidecar (not Lab input): `06-EVIDENCE/canonical/receipts/TO-180-A2-001-binding-191-sidecar.json`

`input_manifest_hash` is the tree at **immutable** `base_commit` for those prefixes. At that commit `schemas/`, `tests/`, and `docs/` are empty; only OFN stub blobs exist under `octopus_bridge/`. Do not mix with the uncommitted `.191` working tree.

Git toplevel is `F:\backup`. `repo_locator` is a subdirectory, not a standalone git repo.

## Lab wait state (healthy)

```
STATE: BLOCKED_BY_CANONICAL_BINDING
NEXT_ALLOWED_INPUT:
- repo_locator
- branch
- immutable base_commit
- input_manifest_hash
- allowed_paths
- task_id=A2-001

DO NOT:
- search for alternative repos again;
- infer a branch;
- create a skeleton;
- run Fugu or DeepSeek;
- create a worktree;
- start A2-002 or A2-003.
```

After ACK: A2-001 only on a fresh worktree of `d10887cbb5c80ec2c3e347f070556ba8276d8a79`. Success = `QUARANTINED_PASS`. Promotion still forbidden.

`.191` local `QUARANTINED_PASS` is not Lab execution.
