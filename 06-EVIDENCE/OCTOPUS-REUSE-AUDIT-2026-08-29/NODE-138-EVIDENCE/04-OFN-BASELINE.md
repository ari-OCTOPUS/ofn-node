---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [octopus, node-138, ofn, baseline]
created: 2026-08-29
updated: 2026-08-29
created_by: agent
language: en
sources:
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/P1-RESULT]]"
  - "[[03 - Projects/OFN-Board/ofn/config.py]]"
---

# 04 — OFN baseline

```text
observed_at=2026-08-29T05:32:32Z
method=ssh_readonly_plus_vault_config_names
scope=this_host_only
SAFE_TESTS=NOT_RUN
```

414–492 is **not** used as a baseline.

## Path and interpreter

| Field | Value | Truth |
|---|---|---|
| repo | `/home/ari/ofn` | `LIVE_VERIFIED` |
| HEAD | `a27eb0536793c7fc040917bb645e9057707298f4` | `LIVE_VERIFIED` |
| dirty tracked | no | `LIVE_VERIFIED` |
| Python | 3.13.5 (`/usr/bin/python3.13`) | `LIVE_VERIFIED` |
| preflight | `python3 -m ofn.preflight` via `ofn-boot.service` | `LIVE_VERIFIED` |
| web | `/home/ari/ofn/web/cockpit-v2/src/pages/queue.js` present; vault `panel.html` is the other tree | `LIVE_VERIFIED` / `REPO_VERIFIED` |
| packs | `/home/ari/ofn/packs/{ziman,lead,studio,hypno}.yaml` | `LIVE_VERIFIED` |
| ports | 8791–8794 loopback ofn; 8796 bridge | `LIVE_VERIFIED` |

## Database / state path **names** (values not read)

From `ofn/config.py` `os.environ.get` names only:

`OFN_STATE_DIR`, `OFN_PACKS_DIR`, `OFN_PRODUCTS_DB`, `OFN_STUDIO_DB`, `OFN_PAINTING_DB`, `OFN_MARKETING_DB`, `OFN_ASSISTANT_DB`, `OFN_INBOX_DB`, `OFN_AUDIENCE_DB`, `OFN_CONSENT_DB`, `OFN_PHOTOS_DIR`, `FUGU_MEMORY_DB`.

Default state root name: `~/.local/share/ofn` (unit `ReadWritePaths` includes `/home/ari/.local/share/ofn`). Live SQLite files were **not** opened.

source: `config.py` on 138 via grep · method: source read · observed_at: 2026-08-29T05:32:32Z · truth: `LIVE_VERIFIED` names / `NOT_RUN` contents

## Test census (not execution)

| Metric | Value | Truth |
|---|---|---|
| `tests/test_*.py` files | **118** | `LIVE_VERIFIED` |
| runner implied by prior 138 reports | `unittest` | `DOCUMENTED` |
| includes | `test_cockpit_v2_owner_queue.py`, `test_owner_decision_fake.py`, `test_witness_mint.py`, `test_greeting_name.py`, … | `LIVE_VERIFIED` listing |

### This session

```text
command=NONE
commit=a27eb05
start/end=n/a
exit=n/a
SAFE_TESTS=NOT_RUN
reason=live_DB_and_import_side_effects_not_proven_hermetic_on_runtime_host
```

### Prior documented runs (not re-executed)

| Run | Result | Truth |
|---|---|---|
| P1 targeted cockpit | 73 collected / 73 passed | `DOCUMENTED` `P1-RESULT.md` |
| P1 full | 2076 collected; 2065 pass; 1 historical `test_greeting_name`; 10 skip | `DOCUMENTED` |
| E8 fake spine | 37 OK | `DOCUMENTED` `CHECKPOINT.md` |
| audit `f09681a` | 2028 collected / 2017 pass / 1 error / 10 skip | `DOCUMENTED` `REUSE-MAP.md` |

Do not collapse 2028 / 2076 / 414–492 into one number.

## Line counts on 138 HEAD

| File | physical | nonempty | bytes | Truth |
|---|---|---|---|---|
| `cockpit_v2_read_model.py` | 3058 | 2860 | 113356 | `LIVE_VERIFIED` |
| `http_api.py` | 1844 | 1731 | 99192 | `LIVE_VERIFIED` |
| `node.py` | 4061 | 3749 | 200845 | `LIVE_VERIFIED` |

E0 CHECKPOINT (pre-P1) cockpit physical **2966**. Delta +92 lines is consistent with P1 additive projection (`inference` from counts + `git show --stat`).
