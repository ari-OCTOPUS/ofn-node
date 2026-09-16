---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [octopus, miniapp, lifecycle, live-verify]
created: 2026-08-29
updated: 2026-08-29
created_by: agent
language: fa
sources:
  - "[[06-EVIDENCE/OCTOPUS-TELEGRAM-WEBAPP-PHASE0-2026-08-29]]"
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/P1-RESULT]]"
---

# Undefined lifecycle card — live verification

```text
SOURCE_COMMIT=0016cdfa5a91e92e484872ff3bbc262bde576804
BRANCH=rescue/octopus-live-tree-20260821
GATEWAY_PID_BEFORE=20800
GATEWAY_PID_AFTER=26892
TARGETED_TESTS=28/28
STATIC_ASSET_HTTP=200
STATIC_ASSET_HAS_FAIL_CLOSED=true
ROOT_HTTP=200
LISTENER_8774_PID=26892
OLD_PID_ABSENT=true
OTHER_CORE_LISTENERS_UNCHANGED=true
TELEGRAM_SENDS=0
EXTERNAL_EFFECTS=0
```

RED:

- card بدون `rfc_id` رشتهٔ `undefined` را رندر می‌کرد.
- برای دو card (یک ناقص، یک معتبر)، ۲ approve و ۲ reject می‌ساخت.

GREEN:

- card ناقص فقط‌خواندنی و با badge «شناسه نامعلوم» است.
- card معتبر دقیقاً یک approve و یک reject دارد.
- backend lifecycle privacy contract تغییر نکرد.

Fast-forward فقط دو فایل را تغییر داد. restart از مسیر کانونیکال
`_ops/RESTART-PROCESS.ps1 gateway` انجام شد. آخرین مرحلهٔ probe با
`Get-NetTCPConnection` به‌علت failure ماژول NetTCPIP شکست؛ این failure پس از
restart و HTTP 200 رخ داد و با netstat جداگانه reconcile می‌شود.

Reconciliation:

- `netstat` نشان داد 8774 روی PID 26892 LISTEN است.
- PID قدیمی 20800 دیگر وجود ندارد.
- 8771/8772/8773/8776 روی PIDهای قبلی 16860/10052/18096/22352 ماندند.
- `GET /miniapp` و `GET /app.js` هر دو 200.
- asset سرو‌شده عبارت fail-closed را دارد.
- loaded branch HEAD = `0016cdf`.

Authenticated lifecycle payload با initData واقعی probe نشد؛ هیچ token یا
Telegram action استفاده نشد.

## Owner reproduction reconciliation

After the owner reported the issue again, `miniapp-hits.jsonl` showed no new
authenticated WebView request after the gateway reload. The only new rows were
the local static verification requests. The currently served root references
asset version `283890b7ee`, and that asset contains the fail-closed renderer.

Current verdict:

```text
REPRODUCTION_ON_NEW_ASSET=NOT_OBSERVED
CACHE_OR_OPEN_WEBVIEW=SUPPORTED_INFERENCE
ALTERNATE_MINIAPP_URL=INCONCLUSIVE
SECOND_RENDERER=INCONCLUSIVE
LITERAL_STRING_UNDEFINED=INCONCLUSIVE
```

No further code change is justified until a closed/reopened WebView creates a
fresh authenticated hit.

## Root-URL cache follow-up

The owner reported the issue again, but the hit log still contained no new
authenticated WebView request. The root URL stored for the bot is stable and
has no query version, while only subassets are versioned. This matches the
known Telegram behavior documented in `miniapp_gateway.py`: WebView may ignore
`no-store` for the root.

An isolated patch versions the root web_app URL from the four asset mtimes:

```text
BRANCH=fix/miniapp-root-cache-bust-20260829
COMMIT=c43bc91
RED=13/14
GREEN=14/14
RELATED_TARGETED=90/90
DEPLOYED=true
CENTER_PID_BEFORE=22352
CENTER_PID_AFTER=23808
CENTER_SOURCE_SHA256=f305ea49d4eabbff28a5d7a53f0b8766b88a1b4a09a55be0dd5482bf54b1be54
CACHE_TOKEN=e290d6a0ec
```

Deployment was initially blocked because live `center.py` already had unrelated
WIP (typed polling/SenderBridge/config reset). After explicit Proceed, the
non-overlapping cache patch was applied without reverting that WIP.

Follow-up validation:

- 11 combined targeted suites passed before restart.
- no Git commit anywhere contains the live `poll_updates_typed`,
  `_config_cache_reset` or SenderBridge center wiring.
- two runtime modules remain untracked.
- Center restarted through `_ops/RESTART-PROCESS.ps1 center`; one supervisor and
  one Center remain.
- one owner-only boot receipt succeeded (`boot_receipt_pid=23808`).
- first post-restart sample briefly retained `lease:duplicate-consumer`; the
  next completed poll recovered to failures=0 and empty reason.
- poll lease owner is PID 23808, generation 42.

Runtime provenance is file-hash bound, not commit-clean: Git HEAD is `0016cdf`
while the loaded Center source includes uncommitted WIP plus cache patch.

## Persistent Menu Button root cause

Owner confirmation identified the launch source as Telegram's persistent Menu
Button, not the fresh `/start` inline keyboard. These are separate Telegram
objects:

- `_home_keyboard()` now emits a versioned root URL.
- `miniapp_registration.py` is deliberately read-only and calls only `getMe`
  and `getChatMenuButton`.
- repository search found zero production `setChatMenuButton` call sites.

Therefore the code fix cannot mutate an already-registered persistent menu.
Updating it requires an explicit owner-side `setChatMenuButton`/BotFather
operation with the versioned URL. That is an external Telegram mutation and
remains disabled for this agent.

## Reproduction clarification

The owner confirmed that the repeated “Issue reproduced, please proceed”
messages came from Cursor's Proceed control; no `/start` was sent and no
Telegram Mini App was opened during those iterations. This agrees with runtime:
`poll_updates_total` remained 29 and no new authenticated MiniApp hit appeared.
Those Cursor messages must not be treated as Telegram reproduction or external
action authorization.

## Fresh WebView reached the gateway

A later launch did fetch the new `/miniapp/app.js`, `tg_shell.js` and CSS, then
made authenticated reads to approvals/tasks/legs/obsidian/governor/state. This
proves the current WebView loaded the new asset. It did not request
`/api/lifecycle`, so the lifecycle list was not opened in that run.

The current approvals projection is also ID-complete:

```text
pending=0
pending_missing_proposal_id=0
recent_decisions=8
decisions_missing_proposal_id=0
sandbox_hidden=4
```

No second missing-ID renderer is currently evidenced.

## Owner-confirmed closure

The fresh WebView subsequently called `/api/lifecycle`. The owner confirmed
that the missing-ID card displayed «شناسه نامعلوم» without action buttons.

```text
UNDEFINED_RENDERER_FIXED=true
FRESH_KEYBOARD_PATH_FIXED=true
OWNER_CONFIRMED=true
DEBUG_INSTRUMENTATION_REMOVED=true
CLEANUP_COMMIT=1c163ea
RESTART_REQUEST=pending_owner_choice
```

The pending restart request was left untouched per owner choice. The persistent
Telegram Menu Button remains a separate, unversioned registration object; the
confirmed working launch path is the fresh `/start` Dashboard button.

Temporary H14/H21 instrumentation and `debug-bbea48.log` were removed after
runtime proof and owner confirmation; behavioral regression tests remain.
