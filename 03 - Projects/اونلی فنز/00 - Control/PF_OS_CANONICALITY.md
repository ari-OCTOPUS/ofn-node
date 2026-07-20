---
type: report
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: active
tags: [creator-business, architecture]
created: 2026-07-20
updated: 2026-07-20
---

# PF_OS_CANONICALITY — 2026-07-20 (ADR)

## حکم (ADR-PF-2026-07-20-01)

**langar + studio (دوکاکپیت propose-only) = runtime کانونی. `pf_os/` = incubating — از langar صدا زده نمی‌شود و تا ADR بعدی نباید صدا زده شود.** هیچ dual-runtime خاموشی مجاز نیست.

## شواهد [FACT]

1. `pf_os/` **فقط در درخت زنده** (`F:\backup\03 - Projects\اونلی فنز\pf_os\`) وجود دارد و **کاملاً untracked در git** است (`git status --porcelain` تأیید) — یعنی تک‌نسخه، بدون تاریخچه، با ریسک ازدست‌رفتن. در worktree این sprint اصلاً وجود ندارد.
2. `grep` روی langar/ و studio/ زنده: **صفر import از pf_os** → هیچ wiring زنده‌ای وجود ندارد؛ ادعای «لایهٔ OS موازی» فقط کدِ خفته است.
3. هر ۴ فلگ وایرینگ pf_os پیش‌فرض **OFF**.
4. **گپ مرزی:** `bridge.publish()` در سطح تابع flag-check ندارد و `events.emit()` اصلاً flag-gate نیست → «flag-off = بی‌اثرِ مطلق» برقرار نیست؛ هر import مصرف‌کننده می‌تواند به `_ops/state/*.jsonl` بنویسد.
5. **اثر جانبی اثبات‌شده:** دو دایرکتوری با نام PUA-escaped ‏«F:backup» (U+F03A/U+F05C به‌جای `:` و `\`) در ریشهٔ پروژهٔ زنده و داخل pf_os، هرکدام حاوی کپی `_ops/state/events.jsonl` — یعنی emit ‏pf_os حداقل دوبار زیر runtime شبه‌POSIX اجرا شده و eventها **به مقصد واقعی نرسیده‌اند** (silent loss).
6. literalهای PII-کلاس (نام/شهر/خیابان در scrub-listهای brain.py / bridge.py / bridge_beat.py زنده) — قبل از هر commit باید placeholder شوند.
7. تنها egress غیرمحلی pf_os: ‏Telegram long-poll در `run_saba.py` حالت LIVE (token-gated، امروز خاموش)؛ cortex ‏(:8772) و REST ‏(:8780) فقط localhost.

## پیامدهای عملی (این sprint)

- آداپتور اختاپوس برای Project-F ‏**SHADOW_ONLY** می‌ماند (قرارداد: [[ARCHITECTURE-COMPLETE-2026-07-20/05_OCTOPUS_ADAPTER_SHADOW|05_OCTOPUS_ADAPTER_SHADOW]]).
- langar هرگز pf_os را import نمی‌کند تا ADR جایگزین + این پیش‌نیازها: (۱) commit شدن pf_os با PII-scrub، (۲) flag-gate در سطح `publish()`/`emit()`، (۳) فیکس باگ path (دایرکتوری‌های F:backup)، (۴) schema مرزی event (بدون متن/PII — فقط aggregate).
- «مرده/خفته» برای quarantine list (سند [[ARCHITECTURE-COMPLETE-2026-07-20/07_BACKLOG_REMAINING|07_BACKLOG]]): `studio/studio_telegram.py` و `studio_telegram_v3.py` (نسل قبل UI — jayguzin langar/saba_studio)، pf_os به‌عنوان کل (incubating)، `Fable5-Build-Spec.md` (ابزار خارجی NOT BUILT).

## اگر روزی pf_os برنده شد (مسیر مهاجرت بدون شکستن HITL)

فقط با ADR جدید + رأی مالک: (۱) اول commit + تست سبز در CI محلی؛ (۲) هم‌ارز کردن گاردها (OpsecGuard fail-closed + STOP-respect در همهٔ ماژول‌ها)؛ (۳) مهاجرت فایل‌های handoff با قرارداد نسخه‌دار؛ (۴) دورهٔ shadow دوهفته‌ای که در آن pf_os فقط می‌خوانَد؛ (۵) هرگز دو حلقهٔ زندهٔ هم‌زمان روی یک state.
