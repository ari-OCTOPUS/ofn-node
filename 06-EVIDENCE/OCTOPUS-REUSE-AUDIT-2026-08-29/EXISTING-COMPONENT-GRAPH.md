---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [octopus, graph, reuse]
created: 2026-08-29
updated: 2026-08-29
created_by: agent
language: fa
sources:
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/REUSE-MAP]]"
  - "[[06-EVIDENCE/OCTOPUS-L191-FINDINGS-2026-08-28]]"
---

# EXISTING-COMPONENT-GRAPH

یک organ per function — از `56e9369` `HOW-TO-CONNECT.md`. این گراف همان اعضا را نشان می‌دهد، نه اعضای پیشنهادی.

## سطوح

```
[Owner human]
    |  view                 |  command (امروز)
    v                       v
Cockpit V2 shell        legacy panel.html
GET /api/v2/owner/*     POST /api/v1/decide
CockpitV2ReadModel      OwnerReads / Node.owner_decide
    |                       |
    +------ sources --------+
            |
     facts / ledger / outbox / mesh dirs
            |
     outbox (sole egress)
            |
     [MISSING] OwnerDecision binding
     [MISSING] 182 witness on live run
     [MISSING] 180 proposal drain (EDGE-6)
            |
     manual packet / complete   OR   fake_executor (tests only)
            |
     ledger VERDICT / receipt JSONL
```

## گره × writer × reader

| گره | writer مجاز | reader | SoT؟ |
|---|---|---|---|
| outbox SQLite | Node / adapters پس از gate | panel, OwnerReads, Cockpit queue projection | بله برای اثر خروجی |
| ledger OFN | Node.ledger.append | owner events, Cockpit audit projection | بله برای VERDICT |
| CockpitV2ReadModel | هیچ (derived) | `/api/v2/owner` | نه — projection |
| panel.html state | مرورگر فقط نمایش | انسان | نه |
| OwnerDecision object | تست spine / (آینده) renderer | fake_executor | قرارداد؛ هنوز SoT runtime نیست |
| witness JSONL mint | witness_mint در تست | fake_executor | تست |
| 182 worker | disk mesh | settle | canonical witness طبق body-map |
| 180 proposal.v1 | cognitive worker | باید به ۱۳۸ برود | ساخته می‌شود؛ **drain شکسته** |
| `_ops` MiniApp cockpit | telegram center | مالک ارگانیسم | SoT جدا (ارگانیسم ≠ کسب‌وکار) |
| vault notes | ایجنت/مالک | انسان | supersede طبق discovery |

## دو چیز هم‌نام «Cockpit V2»

| | OFN | ارگانیسم vault |
|---|---|---|
| فایل | `web/cockpit-v2` + `cockpit_v2_read_model.py` | `_ops/budget/cockpit_readmodel.py` |
| تست | `tests/test_cockpit_v2_*.py` در ofn-node | `_ops/tests/test_cockpit_v2.py` |
| دامنه | کسب‌وکار ۱۳۸ | MiniApp تأیید ارگانیسم |
| حکم | یکی نگه دار؛ نام را در سندها qualify کن | بازنویسی/ادغام ممنوع |

## تکرارهای ثبت‌شده `56e9369` (بدون تفسیر تازه)

1. Telegram ×۳ → یک Owner Control path؛ بقیه archive  
2. Router ×۲ → هر دو بمانند (domain جدا)  
3. Memory ×۴ → facts + calibration canonical  
4. Witness ×۲ → ۱۸۲ canonical  
5. Brain ×۲ → ۱۸۰ canonical  
6. Orchestration ×۳ → connect explicit؛ orchestrator نو ممنوع  
7. Truth docs ×۳ → `ofn/docs` root  
8. Backup ×۴ → timer canonical  
9. Constitutions ×۲ → publish یک‌طرفه

## یال‌های موجود vs یال‌های غایب

موجود و کدشده:

- panel → decide → outbox.approve_manual → ledger  
- run.py → CockpitV2ReadModel → GET v2  
- cockpit shell → GET v2 only  
- fake spine chain در تست  
- export snapshot ۱۳۸→۱۸۰ + ACK (شواهد 2026-08-28)

غایب (اتصال، نه ماژول):

- cockpit/legacy → OwnerDecision  
- OwnerDecision → outbox item  
- outbox/proposal → 182 claims-embedded verify  
- 180 outbox.persist/transmit روی شاخهٔ spine (EDGE-6)  
- Telegram card renderer روی bot `__owner__`  
- restart receipt ↔ `ofn.service` tree  
- backup timer ↔ `~/octopus-mesh`  
- یک عدد canonical برای unittest discovery  
