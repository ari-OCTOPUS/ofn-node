---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [octopus, recon, map, chrono]
created: 2026-07-08
updated: 2026-07-08
created_by: agent
---

# OCTOPUS-RECON-MAP — نقشهٔ کدِ موجود (Phase 0، نسخهٔ فشرده)

> گیتِ ورودی Phase 1 طبق [[04 - Architect System/octopus-build-prompts/00-INDEX|00-INDEX]]. هر ادعا با `path:line` — صفر fabrication. نسخهٔ فشرده: فقط بخش‌هایی که پرامپت‌های P1/P2/P5 ارجاع می‌دهند (§2، §3، §5، §9).

## §1. Layout

| ناحیه | مسیر | نقش |
|---|---|---|
| ارگانیسم | `_ops/organism.py` (194 خط) | حلقهٔ همیشه-روشن، tick=300s، HTTP 8771 (`organism.py:44-45`) |
| متابولیسم | `_ops/budget/*.py` (opslib, telemetry, organ_gate, governor_epoch, fitness, replication, budget_gate v2, money_gate, capability_gate, approval_channel, attribution, reconcile) | گیت‌ها/سنجش — enforcer فقط budget_gate |
| ledger ژنوم | `07 - Knowledge/genome-system/ledger/ledger.py` (220 خط) | تنها حافظهٔ ماشینی مشترک؛ JSONL + SHA-256 hash-chain |
| دکترها | `genome-system/agents/doctor.py` (117 خط) · `04 - Architect System/scripts/dashboard_doctor.py` (178 خط) | هر دو propose-only |
| اسکریپت‌های بقا | `scripts/germline-hourly.ps1` · `germline-backup.ps1` · `organism-watchdog.ps1` · `git-serialize.ps1` · `restore-drill.ps1` | لایهٔ P0.5/Track C |
| تست‌ها | `_ops/tests/run_all.py` (۱۱ فایل، سبز طبق HANDOFF جلسه ۲۹) | الگوی harness ایزوله (`harness.py:56`) |

## §2. Heart / substrate — چه هست، چه نیست

**نیست (verified 2026-07-08، grep سراسری روی `_ops`، `genome-system`، `scripts`):** هیچ کدی برای `pacemaker` / `HLC` / `langar_ledger` / `age_tick` / `experience_rate` / `EffectorGate` وجود ندارد. تنها match یک کامنت است: `04 - Architect System/scripts/governor_shadow.py:41` (واژهٔ «langar» در متن فارسی). → Phase 1 از صفر می‌سازد، چیزی برای wrap وجود ندارد جز موارد زیر که **extend** می‌شوند:

- **Hash-chain موجود (پایهٔ LANGAR):** `ledger.py:120-166` — `Ledger.append()` با قفل دولایه (`ledger.py:63-117`)، بدنهٔ hash‌شده = `(id, ts, type, actor, payload, meta, prev)` (`ledger.py:198-201`). `EVENT_TYPES` بسته (`ledger.py:31-37`). **فیلد age/is_human ندارد.**
- **حلقهٔ همیشه-روشن:** `organism.py:138-190` — جای سوارکردن pacemaker به‌عنوان background task (P-Chrono-1).
- **کهنگی germline (بخشی از S-5 از قبل هست):** `opslib.py:58-82` (`germline_lag_hours`, WARN=2h/ERR=26h) + مصرفش `organism.py:146-153`.
- **پرچم‌ها/kill:** `opslib.py:48-52,201-222` (STOP/FREEZE) — kill-switch supreme از قبل قرارداد است.
- **ApprovalChannel (برای P2/P3):** `_ops/budget/approval_channel.py` (pluggable + NotWiredStub/Mock — HANDOFF جلسه ۲۸).

## §3. Event flow (وضعیت فعلی)

تک‌مسیر ماشینی: هر ماژول → `opslib.ledger_note()` (`opslib.py:266-275`) → NOTE+subtype به ledger ژنوم (V2). شکست → `_ops/state/ledger-fallback.jsonl`. هیچ bus رویدادیِ عمومی وجود ندارد؛ broadcast/ack هم نیست (Chrono Bus در P1 ساخته می‌شود). خواندنی‌های انسانی: `_memory/HEARTBEAT.md` (append-only، `opslib.py:232-236`) و `governor-alerts.md`.

## §5. Doctor(s) — سه دکترِ موازی (برای P2)

1. `genome-system/agents/doctor.py` — adjudicator هفتگی propose-only؛ `_distance_from_genome` (`doctor.py:56-62`)؛ restart-duty **ندارد**.
2. `scripts/dashboard_doctor.py` — سلامت vault؛ نقص شناخته: `VERIFY_RULES` کلاس‌محور (`dashboard_doctor.py:42-47`) که [[04 - Architect System/scripts/DOCTOR-BLUEPRINT-v1|DOCTOR-BLUEPRINT-v1]] §4 با `stable_read` نمونه‌محور جایگزینش می‌کند (+ کمربند ویندوزیِ اجباری برای verdict=corrupt، §4 residual).
3. `genome-system/research_loop.py` — حلقهٔ پژوهش، دکتر نیست ولی مصرف‌کنندهٔ آینده.
هیچ‌کدام: sandbox-build/RFC/critic/`restart_from_known_good` ندارند — Phase 2 می‌سازد.

## §9. Incidents (برای P5)

- **INC-1** مرگ ارگانیسم ~2026-07-07 20:53 (teardown سندباکس ایجنت؛ درس: تولد فقط owner-launched). واکنش موجود: `scripts/organism-watchdog.ps1` (فقط revive، تسلیم به STOP — `organism-watchdog.ps1:16-23`). **زمان‌بند نصب‌شده نیست** (نصب owner-only مانده).
- **INC-2** شکست germline-hourly @20:49 (stderr گم). فیکس فعلی: capture در `germline-hourly.ps1:38-48` + قفل `git-serialize.ps1`. **retry/backoff هنوز ندارد.**
- سه فایل soma-state هنوز tracked (open-decision #8).

## Δ نقشه↔نقشه (برای ایجنت بعد)

Phase 1 این جلسه ساخته شد → [[_ops/ORGANISM-SPEC|ORGANISM-SPEC]] §Chrono. مرجع طراحی verbatim: DataSchemas (`_Archive/CHRONOS-FABLE-OS/10_Implementation/DataSchemas.md`) + DOC-B (`_Archive/CHRONOS-FABLE-OS/01_SourceMap/_primaries/OCTOPUS_CHRONO_ARCHITECTURE.md`) §8/§9/§11 + HeartDesign (`_Archive/CHRONOS-FABLE-OS/08_Safety/HeartDesign_PulseCore.md`). (پوشه بعداً به _Archive منتقل شد؛ ۲۰۲۶-۰۸-۱۲ به متن‌ساده تبدیل شد چون validator عمداً _Archive را ایندکس نمی‌کند — رجوع: find_broken_links.py:14/36.)
