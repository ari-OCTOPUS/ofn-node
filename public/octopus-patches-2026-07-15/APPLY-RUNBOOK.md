# 🐙 Runbook اعمال — همهٔ کارها (2026-07-15)

من نمی‌توانم روی `F:\backup`ِ زنده بنویسم (سیستمِ مجوز). همهٔ کد در worktree ساخته و تست شد؛
هر ۳ patch با `git apply --check` روی masterِ زنده **پاک** شدند. تو با چند خط اعمالشان کن.

## پیش از هر چیز — checkpoint
```
cd F:\backup
git branch backup/pre-truthful-cockpit-2026-07-15
```

## پچ‌ها (به ترتیب؛ همه relative به master، apply-check پاس)

مسیرِ پچ‌ها: پوشهٔ scratchpad این جلسه.

### ۱) کابینِ راست‌گو — امن، read-only (P1+P3)
```
git apply "1-truthful-cockpit.patch"
```
شامل: reader دوشکلهٔ business_legs · متادیتای stale برای channel-status (داشبورد + readmodel) ·
mintِ correlation_id در emit · `read_truth_cards()` · فرمان‌های `/wiring` و `/health` در تلگرام ·
۴ تستِ نو + به‌روزرسانیِ قراردادِ test_phase1_envelope.
> ⚠️ پچِ قدیمیِ `p1-truthful-fixes.patch` را **نادیده بگیر** — این پچ superset آن است.

### ۲) فیکسِ money-integrity (DUP-01) — جدا چون پول
```
git apply "2-baseline-money-fix.patch"
```
enforcerِ واقعی (`04 - Architect System/scripts/budget_gate.py`) وارد fingerprint می‌شود؛ فایلِ غایب
دیگر ساکت رد نمی‌شود. **بعد از اعمال، یک بار re-baseline لازم است** (چون fingerprint تغییر می‌کند):
```
python -X utf8 -c "import sys; sys.path.insert(0,'_ops'); sys.path.insert(0,'_ops/budget'); import baseline; print(baseline.capture_baseline())"
```
(یا هر مسیرِ capture که در گردشِ کارِ خودت داری.)

### ۳) ثبتِ تست‌های نو در run_all — جدا چون capability marker
```
git apply "3-runall-register.patch"
```
۵ تستِ نو + ۲ تستِ ziman (سبز، ثبت‌نشده بودند) به run_all اضافه می‌شوند.
> چون run_all در fingerprintِ capability دخیل است، بعد از اعمال marker را refresh کن (گردشِ کارِ خودت).

## تأیید بعد از اعمال (روی درختِ زنده که marker دارد)
```
cd F:\backup\_ops
python -X utf8 tests/run_all.py
```
انتظار: سبز. (اگر test_phase5/test_box/test_box_wiring/test_cockpit_v2 «capability revoked» دادند،
یعنی marker refresh نشده — نه رگرسیون. روی worktree هم همین‌ها به‌خاطرِ نبودِ marker می‌افتادند.)
سپس organism را restart کن تا فرمان‌های `/wiring` و `/health` زنده شوند.

## آزمایشِ کابین در تلگرام
به بات بفرست: `/wiring` (نقشهٔ اتصال‌ها با آیکنِ صادق) و `/health` (قلب/capability/پول/halt).
قانون در کد اجرا می‌شود: فقط فایلِ موجودِ تازه 🟢؛ غایب ⚫؛ کهنه 🟠.

## پچ‌های جداگانه که هنوز پیشنهادند (اعمال نکن مگر بخواهی)
- `PATCH-tg-execute-v2.md` — «دکمه‌های تلگرام واقعاً اجرا کنند» (consumer روی beat-thread، پشتِ فلگِ
  خاموشِ OCTOPUS_TG_EXEC). دو بار adversarial-review شد. طبقِ Phase-1 اسپکِ خودت، کابین فعلاً read-only
  می‌ماند؛ این را وقتی خواستی جدا اعمال کن.
- فیکسِ باگِ AXON cli (کرشِ «≥» روی cp1252): `PYTHONIOENCODING=utf-8` — یا یک‌خط try/except در _print_summary.

## آنچه عمداً نشد (owner/PHI)
- خواندنِ اسنادِ AXON-MS (گاردِ PHI خودت) — سوال در `00 - Inbox/AGENT_QUESTIONS.md` ثبت شد.
- اجرای هیچ گامِ پولیِ AXON (T0.4/wave/Boltz) — صفر هزینه.
