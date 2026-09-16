---
type: morning-cards
status: active
created: 2026-08-19 (for 2026-08-20 morning)
tags: [octopus, morning-cards, reminders]
---

# 2026-08-20 MORNING-CARDS — سه کارت قبل از هر چیز

## 🃏 کارت ۱ — C-035: ناهماهنگی Var_eff (پیش از هر مراسم TCB بعدی)
محاسبهٔ canonical ‏`solve_from_stds` → Var_eff=0.199136؛ لنگرِ settings → 0.208232 (≈۴٪ اختلاف).
**باید روشن شود**: آیا این ناهماهنگی منبع خطای پایین‌دستی است — به‌ویژه در I_pred/Var_ex که دیروز وصل شدند
(آن دو با لنگر مطابقت دارند، پس یا Var_eff مستقل است یا جبران‌شده)؟ بررسی: نقطهٔ عملیاتی متفاوت؟ transcription؟
مدرک: `01-TRUTH/CONTRADICTIONS.md` (C-035) · `4d_system/core/model.py` ANCHORS (Var_eff عمداً اضافه نشد).

## 🃏 کارت ۲ — رفع هماهنگِ آلودگی لجرها (پیش از نسل دوم candidate)
تست‌های تیم‌های D/F/G ردیف‌هایی در لجرهای تولیدی shared گذاشته‌اند (mutation-ledger/viability/beliefs).
**پیش‌شرط نسل دوم**: قاعدهٔ «ورودی تست → دایرکتوری آزمایشی جدا» + پاکسازی نقطه‌ای با بازبینی دوسشن‌ای؛
وگرنه fitness نسل دوم هم آلوده می‌شود. (آیتم حاکمیتی مستقل در `F:/backup-island/GENESIS-DECISIONS.md`.)

## 🃏 کارت ۳ — زنجیرهٔ primary: قاعدهٔ claim (مالک، حکم نهایی)
هر فرآیندی که اول RBA تازه را دید → پین FX (**هر دو فایل**: `FX-RECORD.json` + `pricing_pinned.json`) →
فوری ثبت `FX_PIN_CLAIMED_BY: <session-id>, <ts>` در `F:/backup-island/NEXT_ACTION.md`.
بقیه با دیدن قفل → **audit-only** (نقش ممیز مستقل — الگوی موفق امروز: سه خطای واقعی گرفت).
سپس صاحب قفل: پروب V4a هشت‌تایی (گیت ۸/۸ خوانا) → فریز V4 (ارجاع به رضایت §۱) → primary ‏۲×۱۵
با سیاست void سختِ پیش‌ثبت — بدون ادغام با نمونهٔ ابطال‌شدهٔ V2.

---
*ترتیب پیشنهادی: کارت ۳ (پنجرهٔ RBA وقت‌حساس است) → کارت ۱ → کارت ۲. کارت‌های ۱و۲ پیش‌شرط مراسم TCB بعدی و نسل دومند، نه زنجیره.*
