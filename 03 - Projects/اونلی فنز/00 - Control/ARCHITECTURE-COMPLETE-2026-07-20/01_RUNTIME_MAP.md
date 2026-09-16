---
type: doc
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: active
tags: [creator-business, architecture]
created: 2026-07-20
updated: 2026-07-20
---

# 01 · RUNTIME MAP — پس از sprint ‏2026-07-20

> منطبق بر کدِ برنچ `claude/project-f-governance-sprint-515cf3`. جانشینِ RUNTIME-SCAN-04 برای این برش.

## نقشهٔ ماژول‌ها

```
Operator A ══ Telegram ══▶ langar/langar_bot.py  (تنها egress → فقط chat-id ‏A، OpsecGuard fail-closed)
                             ├─ pf_admin.py   → brain/acquisition_pipeline.py  (+LinkState +audit +dryrun)
                             ├─ dm_admin.py   → brain/dm_pipeline.py           (بدون متد send — ساختاری)
                             ├─ fan_admin.py  → brain/store.FanDB
                             ├─ vault_admin.py→ brain/store.VaultBank
                             ├─ /kpi /kpi_record /kpi_import → store.KPIRollup(+funnel) + LinkState
                             ├─ /guards /report_* → brain/guards.py (Warmup + ChannelLocks fail-closed)
                             └─ /octopus_tick → orchestrator.py (advisory؛ compliance از manifest، fail-closed)
Creator C ══ Telegram ══▶ studio/creator_studio.py (فقط chat-id ‏C؛ HALT + STOP-aware)
                             ├─ content_studio.py (موتور درفت + set_status + handoff_to_vault)
                             ├─ creator_brain.py (LLM محلی/Fugu پشت فلگ؛ GuardLayer)
                             └─ affirm.py (رشته‌ساز خالص)
پل فایل‌ها: drafts.json · to_operator.json(⇦legacy to_ari) · for_creator.json(⇦legacy for_saba) · capacity.json · HALT
orchestrator.py: importهای _ops/neural حالا lazy با fallbackِ stdlib → بوتِ standalone (استقلال 10/10)
pf_os/ (فقط درخت زنده، untracked): incubating — صفر wiring (ADR: [[../PF_OS_CANONICALITY|PF_OS_CANONICALITY]])
```

## RACI (خلاصه)

| مؤلفه | R (اجرا) | A (پاسخ‌گو) | C | I |
|---|---|---|---|---|
| هر پست/DM/پرداخت واقعی | **فقط انسان (A)** | A | C (وتو) | DecisionLog |
| درفت محتوا | ContentStudio/AcquisitionPipeline | A ‏(/pf_ok) | C ‏(cert+وتو) | approvals.jsonl |
| DM draft | DmPipeline/faq_engine | A ‏(/dm_ok) | — | approvals.jsonl |
| مرز محتوا | C ‏(/halt — حرف آخر) | A | — | to_operator.json |
| kill سراسری | مالک (فایل STOP در `_ops`) | مالک | — | همهٔ باتها |
| compliance ‏tick | `orchestrator._load_compliance_checks` (fail-closed) | manifest | dual_brain guards | TickResult |
| KPI/funnel | A دستی (‏/kpi_record، ‏/kpi_import) | A | — | kpi.json/link_state.json |

## سه محورِ «wired» (درسِ truth-map)

هر ادعای «فعال» فقط با هر سه: (۱) فلگ/env روشن، (۲) reachability (caller واقعی)، (۳) side-effect قابل‌مشاهده.
امروز: **egress تلگرام عملاً بسته است** — `langar_config.json` غایب → OpsecGuard ‏deny-by-default. BotFather تولیدی هم هنوز ساخته نشده (NO-GO).
