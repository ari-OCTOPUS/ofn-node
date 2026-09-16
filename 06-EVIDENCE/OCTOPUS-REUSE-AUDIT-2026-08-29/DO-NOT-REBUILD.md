---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [octopus, reject, no-rebuild]
created: 2026-08-29
updated: 2026-08-29
created_by: agent
language: fa
sources:
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/REUSE-MAP]]"
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/MISSING-EDGES]]"
---

# DO-NOT-REBUILD

هر ردیف: اگر ساخته شود، کدام عضو موجود را دور می‌زند و چرا REJECT است.

| ممنوع | عضو موجود که دور می‌زند | دلیل رد |
|---|---|---|
| Event Store دوم | ledger OFN + ledger ارگانیسم + mesh receipts | source-of-truth موازی |
| Command Bus دوم / `/api/control/v2` | `POST /api/v1/decide` + OwnerReads | API سوم روی همان outbox |
| جداول `cp_resources` / `cp_events` / `cp_commands` | outbox + ledger + CockpitV2ReadModel | projection runner موازی |
| Memory framework (Mem0/Zep/Letta/…) | facts.sqlite + calibration.jsonl + MemoryGate | قرارداد حافظه هست؛ framework هویت را می‌دزدد |
| Approval schema جدید | `OwnerDecision` ۱۲ فیلد @ `6881337` + decide فعلی | schema دوم |
| Witness service جدید | worker 182 + `witness_mint.py` | ۱۸۲ canonical است |
| Executor جدید | `fake_executor` (تست) + `approve_manual` + manual complete | مسیر اثر از قبل fail-closed است |
| Orchestrator جدید | scheduler + verify-dispatcher + cycle-settler | `56e9369`: فقط explicit connection |
| UI سوم | panel.html + `web/cockpit-v2` + MiniApp `_ops` | دو پنل کسب‌وکار کافی است؛ سومی parity را می‌شکند |
| Telegram bot / sender جدید | `__owner__` + `alert.py` + bridge مرده | پنج token، صفر poller |
| Projection framework مستقل | `CockpitV2ReadModel` | ۶ resource + envelope آماده است |
| LangGraph / Temporal / DBOS | outbox + lease + approve_manual | شکاف proven برای runtime موازی نیست |
| کپی V2/spine به داخل vault/germline | خانوادهٔ ofn-node | lineage UNRELATED (`c803dee`  confuses HEAD) |
| ادغام کاکپیت MiniApp با OFN Cockpit V2 | دو دامنه | coupled-not-merged |
| نصب مدل / dataset / flag / bind `0.0.0.0` | — | خارج از محدودهٔ این ممیزی |

## ایده‌های صریح REJECT (حداقل ۵)

1. **Control plane سبز از صفر** — `/api/v2/owner` و decide موجودند.  
2. **Durable execution با Temporal** — kill/replay را روی outbox موجود تزریق کن، نه runtime جدید.  
3. **Unified panel از نو** — پوسته V2 و legacy هر دو هستند؛ parity یعنی یک read model.  
4. **Witness HTTP service روی ۱۹۱** — ۱۸۲ canonical است.  
5. **Bot ششم برای کارت approve** — renderer روی هویت موجود.  
6. **Memory capsule product** — اول invalidation روی facts/calibration؛ framework نه.

## Reuse اجباری (اگر زمانی پچ مجاز شد)

| نیاز | جزء |
|---|---|
| Unified Read API | `GET /api/v2/owner` |
| Projections | `CockpitV2ReadModel` |
| Owner Shell | `web/cockpit-v2` + اجزای business پنل legacy |
| Approval contract | `OwnerDecision` |
| Binding | `payload_sha` `artifact_sha` `verdict_sha` |
| Witness | 182 + قرارداد `witness_mint` |
| Idempotency | outbox + قواعد fake_executor |
| Effects | outbox only |
| Receipt | ledger / receipt path موجود |
| Export | `business_source_export` |
| Debug | audit-138 + discovery-138 |
| E2E baseline | ۳۷ تست fake spine |

سکوت مالک = HOLD. هیچ merge به `main` از این سند مجاز نیست.
