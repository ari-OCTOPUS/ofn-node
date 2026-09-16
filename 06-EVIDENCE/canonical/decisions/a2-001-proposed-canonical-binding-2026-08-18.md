---
type: evidence
status: active
created: 2026-08-18
updated: 2026-08-18
created_by: agent
tags: [octopus, a2-001, canonical, custodian, proposed, owner-gate]
sources:
  - "[[../../02-DECISIONS/A2-001-MIRROR-MANIFEST-VERIFIER]]"
  - "[[a2-001-proposed-canonical-binding-2026-08-18.json]]"
---

# A2-001 proposed canonical binding (owner approval required)

`decision_id`: **A2-001-CANONICAL-BINDING-PROPOSAL**  
`observed_at`: **2026-08-18T03:16:21+10:00** · host `DESKTOP-KA9RFN5`  
`owner_approval_required`: **true**  
`canonical_binding_contradiction`: **false** (stated commits and paths matched live git)  
Machine record: `a2-001-proposed-canonical-binding-2026-08-18.json`  
`report_hash` (canonical JSON without that field): `dbfb145574ef4e1fc6f52b08fe48c25fb479742d2b55cf421e29f7b1fd40db80`  
File sha256: `d9b18839b3242a1f08ad780ef1e84d5cb1d0f9023184f68b23dd6e67e9eda8b0`

No code change. No merge, push, deploy, or service edit.

## Live identities (commands, not narrative)

**A — development candidate**

```
git -C F:\backup rev-parse HEAD
d10887cbb5c80ec2c3e347f070556ba8276d8a79

git -C F:\backup rev-parse --abbrev-ref HEAD
equip/g10-cognition-20260816

git -C F:\backup remote -v
germline  E:/germline/octopus.git
```

Path `F:\backup\octopus-bridge` exists. It is **not** a standalone repo (`octopus-bridge\.git` absent). Containing toplevel = `F:\backup`.  
`ls-tree HEAD octopus-bridge` = two blobs (`__init__.py` `2c9fc52a…`, `models.py` `2dca966c…`). Working-tree `hash-object` matches those blobs.  
`schemas/` absent. `mirror_verify.py` absent.  
ls-tree sha256: `1a1c84d8b6f53337bdda88f337dba7bd5cd57470658b0a089265eea07ffa6468`

**B — deployment mirror candidate**

```
git --git-dir=E:/germline/octopus.git rev-parse refs/heads/ofn/bridge
e21f20d7c690e4660894226b1cef1bd47b219b5a

git --git-dir=E:/germline/octopus.git rev-parse e21f20d
e21f20d7c690e4660894226b1cef1bd47b219b5a
```

Bare repo. `remote -v` empty. Tree is full `octopus_bridge/` at **repo root** (38 ls-tree lines), not folder `octopus-bridge/`. Subject: `octopus-bridge: board half of board_cp — armed 2026-08-16 (G7)`.  
`schemas/` absent. `mirror_verify.py` absent.  
ls-tree sha256: `e7804428bb9d3e89d90ea204e92996aab2f78bd9f93108feb0f1059bb2c0f041`

## Proposed binding (not in force until owner approves)

```yaml
development_canonical:
  repo_path: F:\backup\octopus-bridge
  branch: equip/g10-cognition-20260816   # live HEAD; not guessed
  base_commit: d10887cbb5c80ec2c3e347f070556ba8276d8a79
  purpose: A2-001 source development and quarantined patch creation

deployment_mirror:
  repo_path: E:\germline\octopus.git
  branch: ofn/bridge
  base_commit: e21f20d7c690e4660894226b1cef1bd47b219b5a
  purpose: mirror/deployment verification only
  write_authority: none
```

## Rationale

Stated prefixes `d10887c` and `e21f20d` and the two paths match live git. The earlier `UNKNOWN_CANONICAL` still describes **package identity** (stub vs full board package). This file does not collapse them; it records the owner's proposed split.

## Uncertainty

- Development path is a vault subdirectory, not its own git repo.
- Bare `octopus.git` has no remotes.
- Neither tree already contains A2-001 schemas/CLI.
- Vault worktree is dirty overall; `octopus-bridge` tracked files still match HEAD.
- Untracked `__pycache__` under `octopus-bridge`.
- Germline `equip/g10-cognition-20260816` also equals `d10887c`.
