---
type: runbook
schema: octopus-heart-g4-promotion-runbook/1
status: BLOCKED_UNTIL_LEDGER_TIP_GREEN
created: 2026-08-25
---

# G4 promotion runbook — اعمال کنترل‌شدهٔ پچ روی درخت زنده

پیش‌نیاز مطلق: گیت genome سبز (`verify()` ∧ `verify_tip()` هر دو PASS).
تا آن زمان این runbook اجرا نشود (وضعیت فعلی: tip count mismatch ۳۶۲ — شاهد:
`GENOME-TIP-PROMOTION-BLOCKER.md`).

## ۰. پیش‌شرط‌ها (همه باید PASS باشند)

```powershell
# a) هیچ STOP/HALT/FREEZE
#    فایل‌های _ops/STOP-ORGANISM، _ops/HALT-ALL، 04 - Architect System/STOP نباید باشند
# b) ledger
python -X utf8 -c "import sys; sys.path.insert(0,r'F:/backup/_ops/budget'); import opslib; lg=opslib.genome_ledger(); v=lg.verify(); t=lg.verify_tip(); print(v,t); assert v[0] and t[0]"
# c) hash هدف زنده مطابق manifest
#    pulse_arbiter.py == ac131604... (PHASE-0-MANIFEST.json → promotion_guards)
# d) organism زنده (port 8771) و beat جلو می‌رود
```

اگر (b) قرمز بود: فقط پس از ریشه‌یابی forensic، کم‌خراب‌ترین اقدام
(`seal_tip()` — طراحی‌شده برای همین کلاس) با ثبت رسید جدا اجرا شود؛ سپس از ۰ ادامه.

## ۱. اعمال پچ (فقط پنج فایل؛ بدون commit/push)

```powershell
cd F:\backup
git apply --check "06-EVIDENCE/HEART-G4-AUTHORITY-2026-08-25/G4-PROMOTION.patch"  # باید بی‌خطا
git apply     "06-EVIDENCE/HEART-G4-AUTHORITY-2026-08-25/G4-PROMOTION.patch"
python -X utf8 -m py_compile _ops/heart/pulse_arbiter.py _ops/tests/test_pulse_arbiter_authority.py _ops/tests/test_pulse_arbiter_wire_readiness.py _ops/tests/test_bounded_read.py _ops/tests/run_all.py
python -X utf8 _ops/tests/test_pulse_arbiter_authority.py   # باید 27/27
```

## ۲. ری‌استارت کنترل‌شدهٔ فقط organism

```powershell
# marker استاندارد ری‌استارت (STOP مالک هرگز پاک نمی‌شود؛ launcher خودش marker را می‌خورد)
New-Item -ItemType File "F:\backup\_ops\RESTART-REQUESTED"
# صبر تا خروج تمیز پروسه (چند beat)؛ سپس launcher همان مسیر تولید:
Start-Process -FilePath "F:\backup\_ops\RUN-ORGANISM.bat" -WorkingDirectory "F:\backup\_ops" -WindowStyle Hidden
```

## ۳. راستی‌آزمایی چند beat (حداقل ۲ beat؛ هر beat ~۹۶s)

در `arbiter-latest.json` و `arbiter-shadow.jsonl`:

- رأی control_law: `present=false`، `eligible_for_live=false`، `authority=SHADOW_ONLY`، `observed_period_s` حفظ شده
- `authority_policy="pulse-authority-g4.v1"`، `authority_floor_s` = آخرین period زندهٔ pre-G4 (نه کندتر، نه تندتر)
- `candidate_period_s` (~۵۵–۶۰s) < `effective_period_s` = anchor؛ `driver="authority-hold"` در اولین beatها
- `beat` جلو می‌رود؛ خطای تازه در governor-alerts نیست؛ Telegram/DeepSeek رفتار پیش‌فرض

## ۴. بازگشت (اگر هر شرطی قرمز شد)

```powershell
cd F:\backup
git checkout -- _ops/heart/pulse_arbiter.py _ops/tests/test_pulse_arbiter_wire_readiness.py _ops/tests/test_bounded_read.py _ops/tests/run_all.py
Remove-Item _ops/tests/test_pulse_arbiter_authority.py
New-Item -ItemType File "F:\backup\_ops\RESTART-REQUESTED"   # ری‌استارت برگشتی
```

## ۵. ثبت

به‌روزرسانی `VERIFICATION-SUMMARY.json` → `status: PROMOTED` + شاهد beats، و
بروزرسانی C-054 در `01-TRUTH/CONTRADICTIONS.md` به `resolved (owner-ratified?)`.
