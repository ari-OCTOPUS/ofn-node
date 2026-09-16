---
type: doc
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: active
tags: [creator-business, architecture]
created: 2026-07-20
updated: 2026-07-20
---

# 02 · STATE MACHINES — با گاردهای گذارِ غیرقانونی (تست: `tests/test_state_machines.py`)

## Acquisition (brain/acquisition_pipeline.py)

```mermaid
stateDiagram-v2
    [*] --> drafted: auto_plan (dedup md5(hook+channel))
    drafted --> approved: approve (نه اگر flagged)
    drafted --> rejected: reject
    approved --> ready: finalize (containment + warm-up + locks + link_code)
    approved --> rejected: finalize-containment-fail (fail-closed)
    ready --> [*]
    rejected --> [*]
```
غیرقانونی (fail-closed، تست‌شده): `ready→approved` · `rejected→approved` · `drafted→ready`. ‏`dryrun` هیچ گذاری ندارد (صفر mutation).

## DM HITL (brain/dm_pipeline.py — بدون متد send)

```mermaid
stateDiagram-v2
    [*] --> pending_review: draft (dedup md5(body+channel))
    pending_review --> ready_for_manual_send: approve (نه اگر flagged)
    pending_review --> rejected: reject
    ready_for_manual_send --> sent: mark_sent (فقط ثبتِ ارسالِ دستی A)
    sent --> [*]
    rejected --> [*]
```
غیرقانونی: `pending_review→sent` · `sent→ready_for_manual_send` · `rejected→ready_for_manual_send`.

## Studio Draft (studio/content_studio.py — ‏`_DRAFT_TRANSITIONS`)

```mermaid
stateDiagram-v2
    [*] --> pending: submit_draft (۴ self-cert اجباری)
    pending --> approved: set_status
    pending --> rejected: set_status
    approved --> published: set_status
    approved --> vault: handoff_to_vault (فقط approved + cert کامل؛ idempotent)
    published --> [*]
    rejected --> [*]
```
غیرقانونی: `pending→published` · `approved→approved` · `published→*` · `rejected→*`.

## زنجیرهٔ join استودیو↔اکتساب (backlog #2 — بسته شد)

`C: submit_draft(channel/hook/caption)` → `A: set_status(approved)` → `handoff_to_vault` → `VaultBank asset (cert حفظ می‌شود)` → `AcquisitionPipeline.auto_plan (vault_id روی آیتم)` → `/pf_ok` → `/pf_ready (link_code)` → **پستِ دستی انسان**.
