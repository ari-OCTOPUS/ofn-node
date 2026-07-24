# FROZEN-BEAT FIX — pause-not-die برای STOP-METABOLIC

**تاریخ:** 2026-07-24 · **وضعیت:** LANDED در `F:\backup` (commit روی شاخهٔ جاری) · **restart: owner-gated**
**تغییر:** `_ops/chrono.py` (`Pacemaker.run_forever` + helperِ نو `_tick_decision`)
**تستِ نو:** `_ops/tests/test_pacemaker_pause_not_die.py` (ثبت‌شده در `run_all.py`)

---

## ۱. باگ (ریشه، تأییدِ کد)

`Pacemaker.run_forever` قبلاً:
```python
if opslib.STOP_ORGANISM.exists() or opslib.halted():
    return
```
`opslib.halted()` (`opslib.py:296`) برای `master_halted()` (HALT-ALL / STOP معمار) **و** `STOP-METABOLIC` truthy است.

عدمِ تقارنِ کشنده: `organism.py` فقط روی `master_halted()` خارج می‌شود — نه STOP-METABOLIC — ولی `run_forever` روی `halted()` **return** می‌کرد. پس در STOP-METABOLICِ **کاذبِ** ۲۰۲۶-۰۷-۲۳ پروسه زنده ماند اما نخِ pacemaker مرد و نبض روی `beat=9890` یخ زد (تا restartِ 00:40).

## ۲. فیکس (pause-not-die، حداقلی)

تصمیمِ هر تیک به helperِ تست‌پذیر `_tick_decision` استخراج شد:
- **`stop`** — `STOP_ORGANISM` یا `master_halted()`: خروجِ دائم (kill supreme، بایت‌به‌بایت مثلِ قبل).
- **`pause`** — `STOP_METABOLIC`: توقفِ برگشت‌پذیر (`sleep`+`continue`)؛ نخ زنده، `beat_once` با رفعِ شرط خودکار resume.
- **`beat`** — عادی.

**تنها تغییرِ رفتاری = STOP-METABOLIC (مرگ → توقفِ برگشت‌پذیر).** kill-switchهای مالک دست‌نخورده؛ ترتیبِ شدت حفظ؛ لاگِ صادقِ PAUSED/RESUMED (append، fail-soft).

## ۳. راستی‌آزمایی (اجرا شد)

- ابتدا در sandboxِ ایزوله (`git archive HEAD _ops`, `ORG_ROOT`→temp): **۱۰/۱۰**.
- سپس علیهِ **درختِ زندهٔ `F:\backup`** پس از اعمال: تستِ نو **۱۰/۱۰** + رگرسیون سبز (`test_chrono_heartbeat`, `test_master_halt` ۵/۵, `test_d2_halt_coverage` ۰ failure, `test_panic_command` ۶/۶). **صفر رگرسیون.**
- روشِ ایمن: harnessِ خودِ پروژه `ORG_ROOT` را به vaultِ موقت pin می‌کند → **صفر نوشتن روی stateِ زنده**. فقط فایل‌های سورس ویرایش شدند.

## ۴. مرزی که رعایت شد

- ✅ فقط ۴ فایلِ خودم commit شد (partial-commit)؛ تغییراتِ commit-نشدهٔ جلسهٔ دیگر (renameهای اونلی فنز) دست‌نخورده و staged باقی ماند.
- ❌ **restart نشد** — فیکس فقط با boot بعدی فعال می‌شود (نخِ زندهٔ فعلی هنوز کدِ قدیم را در حافظه دارد).
- ❌ هیچ flag/STOP/DB عوض نشد.

## ۵. مانده (رأی/دستِ مالک)

1. اجرای کاملِ `run_all.py` (هدف ۲۷۵/۲۷۵) + barrier suite.
2. merge شاخهٔ جاری به trunk طبقِ روالِ خودت.
3. **restart ارگانیسم** تا فیکس زنده شود.

> نبض الان سالم است (پس از restart 00:40)؛ این تاب‌آوری برای STOP-METABOLICِ کاذبِ بعدی است، نه رفعِ قطعیِ فعلی.

## ۶. follow-up (خارج از scope)

`opslib.halted()` مصرف‌کننده‌های دیگری هم دارد (cortex/work_pump/center)؛ ممیزیِ کوتاهِ «کدام لوپ باید pause-not-die شود در برابر کدام باید stop» ارزشمند است.
