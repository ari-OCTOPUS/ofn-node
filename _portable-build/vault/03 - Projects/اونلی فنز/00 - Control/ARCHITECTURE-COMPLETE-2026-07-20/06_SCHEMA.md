---
type: doc
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: active
tags: [creator-business, architecture]
created: 2026-07-20
updated: 2026-07-20
---

# 06 · SCHEMA — قراردادهای داده (پس از sprint 07-20)

## AcqItem (dict — `brain/acq_queue.json`)

```jsonc
{
  "id": "PF-xxxxxxxxxx",          // uuid4[:10]
  "status": "drafted|approved|ready|rejected",
  "channel": "reddit|x|of|fansly",
  "tag": "...", "hook": "...", "caption": "...",   // flagged ⇒ هر سه sanitized
  "flagged": false,
  "created": 1789...,
  "approved_by": "operator|null", "approved_at": 1789,
  "dedup": "md5(hook|channel)",   // 2026-07-20 — idempotency صف
  "vault_id": "V-... | null",     // منبع VaultBank (fair rotation)
  "link_code": "L-xxxxxx",        // بعد از finalize (LinkState)
  "ready_at": 1789, "reject_reason": "..."
}
```

## DraftSubmission (dataclass — `studio/content_studio.py`، فایل `studio/drafts.json`)

```python
draft_id: str            # DRAFT-%04d
title: str
self_cert: dict          # faceless/feet_only/no_explicit/over_18 — هر ۴ اجباری
status: str              # pending → approved|rejected → published (گذارها fail-closed)
ppv_tier: str|None
price_hint: float
channel: str = "reddit"  # 2026-07-20 — join استودیو↔اکتساب
hook: str = ""
caption: str = ""
vault_id: str|None       # پس از handoff_to_vault (idempotent)
```

## LinkState (`langar/link_state.json`)

```jsonc
{"links": {"L-xxxxxx": {"code", "item_id", "channel", "assigned": ts,
                         "clicks": 0, "last_import": ts|null}}, "updated_at": ts}
```
`assign(item_id, channel) → code` ‏(sha1(item_id)[:6]، idempotent) · `record_clicks(code, n)`.

## KPIWeek (bucket در `langar/kpi.json`)

```jsonc
{"week_start": ts, "fans_total", "new_fans", "revenue_usd", "ppv_unlocks",
 "posts", "delivery_rate", "segments": {},
 "clicks", "follows", "free_subs", "paid_conversions"}   // funnel — 2026-07-20
```
CSV ‏import (ترتیب ستون‌ها): `revenue_usd,ppv_unlocks,posts,delivery_rate,new_fans,clicks,follows,free_subs,paid_conversions`.

## DmItem (dict — `brain/dm_queue.json`)

```jsonc
{"id": "DM-...", "status": "pending_review|ready_for_manual_send|sent|rejected",
 "channel": "of|fansly|feetfinder|reddit|x", "kind": "welcome|followup|ppv_offer|winback|custom_reply|general",
 "subject", "body", "context_note", "flagged", "proposed_by", "created",
 "approved_by", "dedup": "md5(raw_body|channel)", "sent_at"}
```

## approvals.jsonl (رکورد audit — `langar/approvals.jsonl`، append-only)

```jsonc
{"ts", "event": "pf_approve|pf_reject|pf_ready|dm_approve",
 "id", "actor", "status", "channel", "kind?", "link_code?", "reason?"}
// content-free — هرگز متن کامل hook/caption/body ثبت نمی‌شود
```
