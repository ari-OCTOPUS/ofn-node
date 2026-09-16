# OCTOPUS 2030 — Program Charter

> نسخه: 0.1 · وضعیت: Phase-0 baseline proposal · تاریخ: 2026-07-12

## مأموریت
تبدیل «پازل هشت‌پا» به برنامه‌ای قابل‌حکمرانی، سنجش، بازیابی و انتقال بین مدل‌ها، بدون ایجاد دو حاکم یا مسیر مستقیم LLM→production.

## سلسله‌مراتب مصوب
- **L0 — Owner (Armin/Ari):** منشور، پول، اقدام بیرونی، Orange/Red، kill/rollback.
- **L1 — Architect/_ops:** مرجع حکمرانی مادر در `F:\backup`؛ در این workspace مشاهدهٔ زنده نشده است.
- **L2 — NBB-CP:** `Portable Sibling` و `shadow-only` طبق VQ-ROOT-001=A؛ خروجی non-binding.
- **L3 — Tenants/Brains/Tools:** شش tenant، 4D مغز پژوهشی مستقل، VaultScanner ابزار فقط‌خواندنی.

## اصول غیرقابل‌مذاکره
1. Improve, don't rewrite.
2. یک execution authority در هر لحظه.
3. Model ≠ Identity؛ Memory ≠ Identity؛ Self-improvement ≠ Permission.
4. Event Ledger منبع حقیقت؛ Graph/Vector/Report نمای مشتق‌شده.
5. Plan→Propose→Policy Check→Approve→Execute→Verify→Record.
6. هیچ secret/PII در حافظهٔ مشترک یا LLM.
7. External actions و تغییر policy/identity همیشه hard-gated.
8. هر تغییر: Current / Delta / Preserved / Rollback.

## محدودهٔ Phase 0
- baseline حکمرانی و policy status؛
- source-of-truth matrix و decision register؛
- WBS، RACI، risk register؛
- Event Ledger specification؛
- NBB shadow contract؛
- acceptance tests.

## خارج از محدوده
- اتصال زنده یا write از NBB به `_ops`/tenantها؛
- اجرای 30روزهٔ 4D؛
- Memory Graph عملیاتی پیش از Ledger Gate؛
- repair خودکار `_ops`؛
- publish/send/spend/trade/pay/lodge/deploy/create-account؛
- خواندن یا انتقال secret/PII.

## Workstreams
1. Governance & Control Plane
2. Evidence, Ledger & Memory
3. Tenant Business Readiness
4. Platform Reliability & Recovery

## Milestones
- **M0 Truth:** conflict/unknown/SOT مشخص.
- **M1 Governance:** VQ-ROOT-003 و policy baseline بسته.
- **M2 Evidence:** ledger schema و tests تصویب.
- **M3 Shadow:** NBB contract و no-write verification.
- **M4 Tenant readiness:** Accounting→Lead→Ziman؛ بقیه تحت کف استقلال.

## Governance cadence
- هر تغییر Yellow: log + rollback.
- Orange/Red: approval دقیق با scope، artifact/diff، issued/expiry و rollback.
- هر مرحله: evidence packet + acceptance gate + handoff.

## Escalation
ابهام authority/policy، secret/PII، side effect، نبود rollback یا sandbox ادعایی → توقف و یک سؤال متمرکز از Owner.

## معیار پایان Phase 0
- active-policy conflict بحرانی = 0
- duplicate decision authority = 0
- NBB live write path = 0
- historical report بدون برچسب = 0
- ledger event بدون idempotency/provenance = 0 در نمونه‌های پذیرش
- external action = 0

---

## پیوندهای سیستمی (System Links)

> **کانال‌های ساخته‌شده (Wave 2):**
> - [[Channels/CH-04|CH-04 · Telegram Bot Unified]] — بات یکپارچه
> - [[Channels/CH-07|CH-07 · Health Score]] — سلامت ترکیبی
> - [[Channels/CH-10|CH-10 · Git Watcher]] — نگهبان گیت
> - [[Channels/CH-11|CH-11 · Tracer + Audit]] — ردگیری و حسابرسی
> - [[Channels/CH-14|CH-14 · HITL Queue]] — صف تأیید انسانی
> - [[Channels/CH-16|CH-16 · Neural Vitals]] — علائم عصبی
> - [[Channels/CH-17|CH-17 · Watchdog Alerts]] — هشدارهای نگهبان
>
> **معماری:**
> - [[Architecture/Dataflow|Dataflow]] — جریان داده
> - [[Architecture/Backbone|Backbone]] — ستون فقرات داده
> - [[Architecture/Admin-UI|Admin-UI]] — داشبورد ادمین
>
> **مرجع کد:** [[Code-Reference|Code-Reference]] — نقشهٔ فایل‌ها
- active-policy conflict بحرانی = 0
- duplicate decision authority = 0
- NBB live write path = 0
- historical report بدون برچسب = 0
- ledger event بدون idempotency/provenance = 0 در نمونه‌های پذیرش
- external action = 0
