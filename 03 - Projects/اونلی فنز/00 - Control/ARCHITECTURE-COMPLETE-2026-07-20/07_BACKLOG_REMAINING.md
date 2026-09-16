---
type: doc
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: active
tags: [creator-business, architecture]
created: 2026-07-20
updated: 2026-07-20
---

# 07 · BACKLOG — انجام‌شده vs باقی‌مانده

> نکتهٔ صداقت: سند «RUNTIME-SCAN-04» با شماره‌گذاری اصلی backlog روی دیسک پیدا نشد (SYNTH-05 هم تأیید کرد ورودی‌های نام‌برده غایب‌اند). آیتم‌های 1–6+14 از متن مگاپرامپت مالک بازسازی و **انجام** شدند؛ «باقی‌مانده» از گپ‌های شواهدمحورِ SCAN-LOCK بازسازی شده و با شناسهٔ R-* شماره خورده تا با شماره‌های نامعلومِ 7–13/15 قاطی نشود.

## ✅ انجام‌شده در این sprint (1–6 + 14 + الحاقات)

| # | آیتم | وضعیت |
|---|---|---|
| 1 | compliance ‏fail-closed از manifest (‏C0) + lazy ‏neural + ‏standalone | ✅ + ۹ تست |
| 2 | join استودیو↔اکتساب (channel/hook/caption/vault_id + set_status + handoff_to_vault) | ✅ + ۳ تست |
| 3 | LinkState + link_state.json + کد روی ‏/pf_ready | ✅ + تست |
| 4 | فیلدهای funnel در KPIWeek + ‏/kpi_import ‏CSV (بدون API زنده) | ✅ + تست |
| 5 | RLock + atomic tmp+replace روی acq/dm | ✅ |
| 6 | dedup ‏md5 (acq: hook+channel؛ dm: body خام+channel) | ✅ + ۳ تست |
| 14 | تست‌های گذارِ غیرقانونی (سه ماشین‌وضعیت) | ✅ ‏(21 تست state-machines) |
| + | approvals.jsonl · ‏/pf_dryrun · تست STOP سراسری · tests/README · فیکس fail-open ‏ChannelLocks · C1 ‏rename کامل استودیو + پاکسازی PII سورس | ✅ |

## ⏳ باقی‌مانده (R-*؛ هیچ‌کدام بلاکر NO-GO→GO نیستند مگر گفته شود)

| ID | آیتم | چرا/مرجع | اندازه |
|---|---|---|---|
| R1 | ‏pipeline کامل EXIF/WM رسانه (الان فقط قاعدهٔ WM در اسناد؛ stub کافی بود) | صریحاً OUT در §C3 مگاپرامپت | M |
| R2 | ‏`_global_stop` روی exception ‏fail-open است → fail-closed کردن + تست | SCAN-LOCK R-گپ | S |
| R3 | ‏scrub یکپارچه: GuardLayer استودیو ↔ OpsecGuard لنگر ماژول مشترک شوند (`_scrub_shared`) | ARCH-SCAN C10 | M |
| R4 | ‏`events_schema` تایپ‌دار + `test_boundary_egress` قبل از هر فعال‌سازی pf_os | ARCH-SCAN §8.4 | M |
| R5 | commit ‏pf_os با PII-scrub + فیکس باگ path ‏(«F:backup») + flag-gate در publish/emit — فقط با ADR جدید | PF_OS_CANONICALITY | L |
| R6 | ‏LearningBridge پیش‌فرض واقعی در `_default_pipe` (‏with_bandit فعال است ولی سنجش regression کامل نه) | PROJECT.md مرحلهٔ ۵ | S |
| R7 | داشبورد بصری KPI (‏kpi-dashboard-spec) | 04_OBSERVABILITY | M |
| R8 | ‏rename باقی‌ماندهٔ نام در **اسناد** (SABA-STUDIO-SPEC، README-SABA-RUNBOOK، msg-to-saba-question8، kindهای dual_brain ‏brief_saba/report_for_ari) — طبق PROP-D4، با رأی ballot ‏Q11 | opsec hygiene | M |
| R9 | scrub «Sydney» از **کپی عمومی آماده** (Playbook/30-Clips/Content-Topics + twinهای docs/) — الگو: «Aussie/Down Under» | rule#6 / P0-opsec Q#9؛ **قبل از هر bio/پست لازم است** | M |
| R10 | انتقال PII از tracking: دو سند + ۸ عکس `test/` → ‏`08 - Partner (PII)` یا `_Archive` + ‏`git rm --cached` | **فقط با رأی مالک** (حذف/انتقال) | S |
| R11 | چک‌لیست ۲۴بندی OpSec (THREAD-CLOSURE T4) + بازکردن Security Gate | شرط GO | انسان |
| R12 | quarantine list ماژول‌های خفته: `studio/studio_telegram.py`، `studio_telegram_v3.py` (نسل قبل UI — استفاده‌نشده)، `Fable5-Build-Spec.md` (NOT BUILT) | P2 hygiene | S |
