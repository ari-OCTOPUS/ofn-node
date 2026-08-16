---
type: design
status: draft
created: 2026-08-16
updated: 2026-08-16
created_by: agent
tags: [octopus, pep, lease]
sources:
  - "[[06-EVIDENCE/PHASE02-2026-08-16]]"
  - "[[06-EVIDENCE/UPDATE-DEBUG-SWEEP-2026-08-16]]"
---

# Telegram lease — spec, issuance OFF

## Shadow already judges real sends [A]

`_ops/state/telegram-pep-shadow.jsonl` (2 lines):

- 2026-08-16T05:32:55 `tg_api._call_post` `editMessageText` verdict=deny reason=`no-lease (deny-by-default)` params_sha=`04733cd66d9fc1ad777a2fcb` lease=null
- 2026-08-16T05:43:40 same sender/action, params_sha=`13f5e47ef2c38f11eb9dff4c`

Hooks [A source]:

1. `_ops/telegram_center/tg_api.py` `TelegramBot._call_post` — **before** the POST/retry loop, `telegram_pep_shadow.hook(...)` then send proceeds anyway.
2. `_ops/budget/approval_channel.py` `_url_json_post` — same pattern. No lines from this sender in the log yet.

`hook()` always calls `observe(..., lease=None)`. `Lease` / `PepState.evaluate` already implement deny-by-default, revoke, replay, TTL, params hash. Issuance is off: nothing constructs a `Lease` on the live path.

## Minimal real lease (not issued)

| field | rule |
|---|---|
| bind | sha256(canonical json of `[action, params]`)[:24] — existing `params_sha` |
| single-use | `consumed=True` on allow; replay → deny |
| TTL | 30s (`_TTL_S` already) |
| signed | owner Ed25519 over `(lease_id, action, sha, nonce, exp)` — **not wired**; today Lease has no signature field |
| replay | nonce store + `consumed` |
| kill | `PepState.revoked` |
| default | no lease → deny |

Issuance stay OFF until owner vote after ≥7 days shadow (PHASE02 ADR draft). Enforce would currently deny **all** production sends.

## Attach point (design)

In `_call_post`, immediately after the existing shadow `hook`, **before** `_post`:

```text
# NOT WIRED
# lease = load_issued_lease_for(method, body)   # always None today
# r = pep.evaluate(method, body, lease)
# if os.environ.get("OCTOPUS_TG_PEP_ENFORCE") == "1" and r["verdict"] != "allow":
#     return None
# real HTTP follows
```

Same insert on `_url_json_post`. Doctor has no direct send (center relay). Councils remain `capability_token=None`.
