---
type: checklist
status: active
created: 2026-08-12
updated: 2026-08-12
tags: [octopus, 100-steps, execution]
---

# اجرای ۱۰۰ قدم — وضعیت زنده

> رأی: «همشو میخوام».  
> `done` · `partial` · `blocked-owner` · `queued`

## تو باید بدهی (وگرنه پول واقعی نمی‌آید)

1. **suburb/آدرس لید 667951** یا بستن لید  
2. **CSV واریزی** یا پذیرش PARK  
3. **رأی سقف** بعد از 2026-08-13  
4. هفته‌ای **approve حافظه** + ۱۵دقیقه approvals  
5. یک‌بار **kill drill**

## وضعیت ۱–۱۰۰ (موج ۱)

| # | وضعیت | یادداشت |
|---|---|---|
| 1 | set_aside | لید 667951 کنار — رأی مالک |
| 2 | set_aside | claim از این لید ممنوع |
| 3 | blocked-owner | CSV/PARK جدا؛ اختیاری بعداً |
| 4 | done | MONEY-CLAIM-VS-CONFIRM |
| 5 | done | `/api/money-caps` + UI |
| 6 | blocked-owner | رأی سقف |
| 7 | done | armed≠productive در UI |
| 8–12 | queued/partial | fitness shadow؛ SK labels بعداً |
| 13 | done | honesty A حفظ |
| 14 | blocked-owner | رأی B اختیاری |
| 15–17 | done | honesty + Home + adapter |
| 18–22 | queued/partial | KPI اعتماد؛ SoT هست |
| 23–26 | done | recall+session+INT |
| 27–35 | queued | digest/RAG/identity_touch |
| 36 | done | Sources/file-bridge قبل‌تر + Home |
| 37–40 | queued | auto brain-guide confirm |
| 41–44 | done | Home SPEC_NOT_BUILT |
| 45–48 | queued | deep_think SK؛ unified brief |
| 49–51 | partial | registry/runner gate |
| 52 | done | runner_apply_gate armed_inert |
| 53–60 | queued | budget_judge beat؛ redteam card |
| 61–62 | queued | tools read-only؛ SSE stages |
| 63 | done | octopus_useful_20 اسکلت ۱۰/۱۰ |
| 64–69 | queued | A/B مدل؛ OTLP local dash |
| 70 | done | WHAT-WE-ARE.md |
| 71–75 | queued | burn forecast؛ approvals UX |
| 76 | done | UI-04 unknown default |
| 77 | done | ARCHITECTURE errata |
| 78 | done | INT-02..05 تست سبز |
| 79–88 | queued | doctor dedupe؛ sigma؛ HANDOFF archive |
| 89–90 | done/partial | kernel قبل‌تر؛ bias در state |
| 91–95 | queued | legs label؛ mining nodes |
| 96–100 | blocked-owner / definition | روتین مالک + تعریف ۹۰روزه |

Evidence: `_ops/state/adr-033/reports/DISCOVERY-WIRE-2026-08-12/06-100-STEPS-EXEC.md`  
Canvas: `octopus-100-next-steps`
