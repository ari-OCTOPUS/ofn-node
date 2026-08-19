---
type: decision
kind: owner-directive
decision_id: OWNER-DIRECTIVE-ACTIVATE-FULL-INTERNAL-EXECUTION-v1
effective: 2026-08-19T23:36+10:00
scope: PRIVATE-LAB
status: APPROVED
recorded_by: pipeline (MEGA-FINISH-ALL-v1)
---

# Owner Directive — Activate Full Internal Execution

Verbatim owner text (authority: owner directive):

```text
OWNER-DIRECTIVE: ACTIVATE-FULL-INTERNAL-EXECUTION-v1
effective: 2026-08-19T23:36+10:00
scope: PRIVATE-LAB
status: APPROVED

1. پنجگانهٔ §17 تأیید شد.
2. Wave B شامل R02 و R08 فعال شود.
3. CARD-001 برای کدنویسی B2 داخلی، تستشده و برگشتپذیر تأیید است.
4. فازهای MEGA-FINISH-ALL-v1 بهترتیب وابستگی ادامه یابند:
   ابزار سنجش → Novelty Archive → Sandbox → Doctor →
   Ablation → Life Currency → Organogenesis →
   Web App/Chat → Obsidian Sync.
5. اجرای موازی فقط برای شاخههای مستقل مجاز است.
6. پس از هر فاز، گیت ماشینی اجرا شود؛ شکست گیت یعنی توقف همان شاخه،
   نه متوقفکردن شاخههای مستقل.
7. ایجنت لازم نیست برای هر patch داخلی B2 دوباره از مالک اجازه بگیرد،
   مشروط به تست، rollback، receipt و صفر اثر بیرونی.
8. خروجی مدل دوم بدون artifact واقعی همچنان PENDING بماند؛
   هیچ نتیجهای به Kimi/GLM نسبت داده نشود.
9. هر عدد با path + method + timestamp + grade ثبت شود.
10. شکستها، VOIDها و ادعاهای مرده حذف نشوند؛ append-only بمانند.
```

## Boundaries that remain owner-gated (not lifted by this directive)

- TCB / keys / hard stops / B0 constitution changes
- Sending messages, public publishing, signatures, external commitments
- Payments, purchases, budget-cap increases, money activation
- Public deploy or architecture disclosure
- SSH / boards / ESP32 / hardware-node activation
- Git history rewrite or data/ledger deletion
- Changing frozen metrics after results
- Any mutation without a verified sandbox
- Paid K=9 or live judge beyond a pre-registered budget

## Execution contract recorded by the pipeline

- All phases run in dependency order; independent branches may not run in parallel in this session (agents depend on an API that is failing; sequential execution is the deterministic path).
- Each phase ends with a machine gate; a failed gate stops only that branch and is recorded append-only (rule 6, rule 10).
- Numbers are recorded with `path + method + timestamp + grade` (rule 9) in `_ops/state/pipeline/phase-gates.jsonl`.
- No result is attributed to Kimi/GLM; all artifacts here are authored and verified on this machine with receipts (rule 8).
- No paid judge run and no live-organism restart occur in this execution; paid K=9 pilot remains pending a pre-registered owner budget (boundary list).
- B0 files are not edited. B1 files (`cardiac.py`, `life_currency.py`, `doctor.py`, `labels.json`, `budgets.yaml`) are not edited; required B1 changes are filed as proposal cards only.

This record is append-only and does not by itself change any runtime state.
