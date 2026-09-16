---
title: ENGINEERING ENTRYPOINT 2026-09-06
updated: 2026-09-06T01:20:00Z
tags: [octopus, handoff, entrypoint]
---

# نقطهٔ ورود مهندسی — 2026-09-06

**جایگزینِ به‌روزشدهٔ** `ENGINEERING-ENTRYPOINT-2026-09-04.md` برای وضعیت فعلی. سند قبلی حذف نمی‌شود.

## تک‌منبع وضعیت

- **ops/STATE|ops/STATE.md]]** — GENERATED از `ops/STATE.json` با `ops/tools/state_compute.py`. دستی ویرایش نکن.
- `binding_gate = GATE-3` · GATE-1 (MEASURE) و GATE-2 (WIRING) بازند با رسید.
- نگاشت نام‌های قدیمی (G0، Gate H/M/B/D/A، G1/G2) در `legacy_name_map` داخل STATE.json است.

## زنجیره‌های رسید فعال

| زنجیره | رکورد | محتوا |
|---|---|---|
| `receipts/mega-debug-20260906T0830Z.jsonl` | 51 | فورنزیک حادثه + HARDENING پایش |
| `receipts/p0-wedge-20260906T2325Z.jsonl` | 58+ | اجرای P0 + CLOSEOUT + GO-FORENSICS + W-00..W-03 |

## رویدادهای کلیدی ۲۴ ساعت گذشته

1. **مدل احیا شد** — llama-server تک‌اسلات (`--parallel 2` فعلاً treatment) با یک restart کران‌دار؛ `T_WEDGE_DURATION=20168s` (بازنام‌گذاری: `OWNER_LATENCY_S`)؛ `TIME_TO_WEDGE≈5.94–6.16h` n=1.
2. **چشم باز شد** — supervisor با patch `6b7912788` قابلیت مدل را می‌بیند؛ `model_capability_degraded` یک incident + یک alert per episode؛ باگ ماسک ts حذف.
3. **GO_DIED_AT=NO_READER** — GO دیروز (CHECKOUT-1) هیچ خواننده‌ای نداشت؛ packet امروز (`OWNER-GO-PAINTING-RANK-DRAFT`) هم در `state/owner-go/` بدون خواننده نشسته → پس از پنجره، wired-reader اولین PR.
4. **S13** — احراز packet با تطبیق نام است (`STRUCTURAL_NOT_AUTHENTICATED`)؛ INV-W13 قرمز رسمی (۲FAIL/۱PASS)؛ fix = registry-hash، پشت رأی.
5. **W-00..W-03 بسته** — سرشماری: ۱۴ ردیف/۵ بی‌مصرف/تصمیم کامل؛ INV-W1 سبز؛ OWNER-CARD.md اولین خوانندهٔ alert.

## فریز و پنجره

`PREREG-WEDGE-2` (sha `72e53ec9…`) در جریان است: پنجرهٔ پیش‌بینی wedge دوم `05:33–05:46Z` (ابطال اگر تا 12:00Z سالم). **فریز ۱۸۰** تا بستن پنجره. پایش ۳۰دقیقه‌ای خودکار: `automation-24d62717` → زنجیرهٔ p0-wedge.

## ⛔ CAP-3 — توقف اجباری پیش از W-04

SHELF-1 (یک محصول کامل روی قفسهٔ زیمان) **تصمیم محتوایی مالک** می‌خواهد (محصول/قیمت/توضیح — ACK-SHELF1: `will_not_choose`). CHECKOUT-1 کارت مالک می‌خواهد. تا یکی بسته نشود، W-04 شروع نمی‌شود.

## ممنوعه‌های فعال

AUTO_RESTART (تا n≥3 episode) · MEMORY_CEILING_RAISE · DISK_CLEANUP_180 · تولید خودکار packet · bypass backoff · push/merge · Event Spine (پشت GATE-6) · هر زیرسیستم تازه.
