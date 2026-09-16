---
type: evidence
created: 2026-08-18
updated: 2026-08-18
tags: [a2-001, quarantine, mirror-verifier]
author: "custodian-191 after owner approved development_canonical"
---

# A2-001 QUARANTINED_PASS — development_canonical (.191)

Owner approved `development_canonical` only (chat 2026-08-18 ~03:17 +10).
`ofn/bridge` not written. No merge, push, deploy, TCB, or `.180` execution.

## Binding in force (dev)

- path: `F:\backup\octopus-bridge`
- branch: `equip/g10-cognition-20260816`
- base_commit: `d10887cbb5c80ec2c3e347f070556ba8276d8a79`

## Tests (acceptance)

```
python -X utf8 F:\backup\octopus-bridge\tests\test_mirror_verify.py
Ran 10 tests in 0.094s  OK
Ran 10 tests in 0.081s  OK
```

CLI golden twice, byte-identical reports, `report_hash=dec366425716357258df7d0f4239c0086523a097d23b7df5d1813fbd8cde68f7`
cwd `octopus-bridge`, fixture under `artifacts/run-20260818T032046/` (not inside `--tree` of production).

Stub blobs unchanged vs HEAD:
`__init__.py` `2c9fc52a718ab397b809cfb63cbc341a6e9ad856`
`models.py` `2dca966ccaa312ec44817d5ff859e7d2e6f0e3f8`

## Added (not rewritten)

- `octopus-bridge/schemas/manifest.v1.schema.json`
- `octopus-bridge/schemas/receipt.v1.schema.json`
- `octopus-bridge/octopus_bridge/mirror_verify.py`
- `octopus-bridge/tests/test_mirror_verify.py`
- `octopus-bridge/.gitignore`

Receipt hash-chain = `integrity_hint: hash-chain-unkeyed` only.

## Promotion

`QUARANTINED_PASS` ≠ merge. Patch: `06-EVIDENCE/a2-001/A2-001.patch` sha256 `731dda9f0c6acdc50ee4c3d79a5ca67c35b140288fc084eae16c152a9c8a2edb`
