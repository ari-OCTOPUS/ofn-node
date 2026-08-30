---
type: design
status: active
created: 2026-08-16
updated: 2026-08-23
created_by: agent
tags: [octopus, pep, lease]
sources:
  - "[[06-EVIDENCE/PHASE02-2026-08-16]]"
  - "[[06-EVIDENCE/UPDATE-DEBUG-SWEEP-2026-08-16]]"
---

# Telegram lease — enforcement seam implemented, production issuer OFF

> **IMPLEMENTATION UPDATE 2026-08-23:** both Telegram HTTP boundaries can now
> enforce a real `octopus_v3.lease.CapabilityLease`. Enforcement remains
> default-off; no production caller issues a lease yet. Runtime verification
> covered no-lease deny, one valid use, replay, action/parameter drift, expiry,
> revocation, kill, approval-channel parity, and fail-closed hook errors:
> **6/6 PASS**. See
> [[../06-EVIDENCE/UPDATE-DEBUG-SWEEP-2026-08-23]].

## Current contract

- Gate: `OCTOPUS_TG_PEP_ENFORCE` (absent/off by default).
- Authority key: `OCTOPUS_TG_PEP_HMAC`; missing or shorter than 16 characters
  cannot mint or validate a real lease.
- Lease: HMAC-signed, exact `action + params` binding, maximum 30-second TTL,
  one call, network allow-list limited to `api.telegram.org`.
- Context: `use_real_lease()` binds the permit to the current execution context.
- Kill/revoke: `OCTOPUS_TG_PEP_KILL` and local lease-id deny-list.
- Boundary behavior: shadow mode remains fail-soft; enforcement mode fails
  closed before network I/O.
- Remaining gap: owner-approved production issuance and arming. Only tests call
  `issue_real_lease()` today.

## Historical 2026-08-16 shadow state

`_ops/state/telegram-pep-shadow.jsonl` (2 lines):

- 2026-08-16T05:32:55 `tg_api._call_post` `editMessageText` verdict=deny reason=`no-lease (deny-by-default)` params_sha=`04733cd66d9fc1ad777a2fcb` lease=null
- 2026-08-16T05:43:40 same sender/action, params_sha=`13f5e47ef2c38f11eb9dff4c`

Hooks [A source]:

1. `_ops/telegram_center/tg_api.py` `TelegramBot._call_post` — **before** the POST/retry loop, `telegram_pep_shadow.hook(...)` then send proceeds anyway.
2. `_ops/budget/approval_channel.py` `_url_json_post` — same pattern. No lines from this sender in the log yet.

At that time `hook()` always called `observe(..., lease=None)`. This paragraph
describes the pre-implementation state and is retained as provenance.

## Historical proposed lease

| field | rule |
|---|---|
| bind | sha256(canonical json of `[action, params]`)[:24] — existing `params_sha` |
| single-use | `consumed=True` on allow; replay → deny |
| TTL | 30s (`_TTL_S` already) |
| signed | superseded: implementation reuses the existing HMAC-signed `CapabilityLease` |
| replay | nonce store + `consumed` |
| kill | `PepState.revoked` |
| default | no lease → deny |

Production issuance and arming remain OFF pending an owner decision. If
enforcement is enabled without a valid contextual lease, all sends are denied by
design.

## Attach points (implemented)

`TgClient._call_post` and `approval_channel._url_json_post` call the shared hook
before transport. A deny in enforcement mode returns without invoking the HTTP
transport. Doctor still sends through center relay. Councils remain outside this
issuer path.
