---
type: evidence
task: DISC-20260820-01
tags: [judge-bias, benchmark, position-bias, verbosity, heatmap, directive-9]
created: 2026-08-20T15:40+10:00
created_by: agent B (ZCode) — lease 2ef1d046
authority: OWNER-DIRECTIVE-09 · D-JUDGE · English task #1
cost: zero_aud · executable=false
code: research/judge_bias/{framework,metrics,run_offline}.py
outputs: research/judge_bias/out/{results.json, heatmap_position.png, heatmap_verbosity.png, heatmap_quality.png}
---

# DISC-01 — چارچوب بنچمارک سوگیری داور LLM (آفلاین، zero-cost)

## قرارداد §۴

- **question:** آیا چارچوب ما سوگیری جایگاه/طول داور را جدا از کیفیت آشکار می‌کند؟
- **hypothesis:** پنج داور با سوگیری تزریقی معلوم، دقیقاً همان سوگیری‌ها را در متریک‌ها نشان می‌دهند.
- **falsifier:** هر فرضیه H1–H5b که در جهت تزریق نیامد = چارچوب رد.
- **method:** unit/offline simulation · data_source: مصنوعی seed=20260820 ·
  risk: none · touches_live_code: false · duration: ~30m.

## اندازه

- ۲۰ تسک (۱۰ استدلالی + ۱۰ خلاقانه) × ۶ جفت = **۱۲۰ جفت** با کیفیت نهانی و
  طول کنترل‌شده و **decorrelated** (طراحی k0–k5: بهتر=بلندتر/کوتاه‌تر/خنثی +
  دو probe خالص طول + شکاف کیفیت).
- ۵ داور × ۱۲۰ جفت × ۲ جای‌گشت = **۶۰۰ قضاوت**. قطعی (بازتولید ✓).

## نتیجه — همهٔ ۷ فرضیه CONFIRMED

| داور (سوگیری تزریقی) | flip | first_pos | quality_acc | longer | تشخیص |
|---|---|---|---|---|---|
| J-neutral | 0.041 | 0.592 | **0.981** | 0.478 | تمیز ✓ |
| J-first (p_first=.85) | 0.696 | **0.867** | 0.610 | 0.489 | جایگاه ✓ |
| J-verbose (p_longer=.75) | 0.275 | 0.592 | 0.624 | **0.836** | طول ✓ |
| J-noisy (acuity=.4) | 0.345 | 0.667 | 0.725 | 0.634 | کیفیت ضعیف ✓ |
| J-shallow | 0.438 | 0.633 | 0.573 | 0.668 | ترکیبی ✓ |

هیت‌مپ‌ها (judge × task): position/verbosity/quality — سه PNG در out/.

## سه باگ واقعی که در حین ساختن چارچوب پیدا و رفع شد (درس‌ها)

1. **مختصات قاطی:** بازگشت quality در مختصات بازو ولی سوگیری در مختصات جایگاه —
   متریک‌ها را فاسد می‌کرد. رفع: تبدیل统一 به مختصات نمایش + معکوس در متریک.
2. **hash() پایتون:** با PYTHONHASHSEید تصادفی → seedهای غیرقابل‌بازتولید.
   رفع: sha256 پایدار؛ تست قطعیت سبز.
3. **confound کیفیت×طول:** طراحی اولیه «بهتر=بلندتر» بود → داور کیفیت‌محور
   طول‌گرا به نظر می‌رسید. رفع: طراحی decorrelated + probeهای خالص.

## ممیزی خط لولهٔ ارزیابی خودمان (actionable)

- متریک «قضاوت پایدار در دو جای‌گشت» (H3/flip) معیار پذیرش قضاوت است — همان
  توصیهٔ ادبیات و تأیید D6. برای هر قضاوت واقعی آینده: اجرای دوجهته + پذیرش
  فقط قضاوتِ flip-نا.
- برای داورهای واقعی DeepSeek/GLM: کارت پیش‌ثبت لازم است —
  `RealJudge` در کد fail-closed است و بدون
  `02-DECISIONS/PRE-REG-JUDGE-BIAS-REAL-2026-08-20.md` امضاشده (Ed25519)
  اجرا نمی‌شود (R10). هزینهٔ تخمینی: ۵ داور × ۱۲۰ جفت × ۲ = ۱۲۰۰ فراخوان.
