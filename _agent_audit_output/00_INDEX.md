# فهرستِ بستهٔ ممیزی — F:\backup (2026-07-16)

> ممیزیِ شواهدمحورِ READ-ONLY (Gate 0–3 کامل). صفر تغییرِ فایلِ اصلی، صفر working-copy، صفر Patch. Gate 4+ منتظرِ رأیِ توست (`14_questions_and_answers.md`).

## سطحِ بلوغ: **L2 — «مهارشده ولی کور»** · نمرهٔ کلی: ستونِ ایمنی ۴/۵، معماری/ارزیابی ۱.۵–۲/۵

## فایل‌ها
| فایل | محتوا |
|---|---|
| [01_executive_summary](01_executive_summary.md) | حکم + بلوغ + نمرهٔ ۹ نقش + ۴ تصحیحِ صادقانه |
| [02 directory_inventory](directory_inventory.md) | نمای دایرکتوری + دسته‌بندی |
| [04 architecture_extracted](architecture_extracted.md) | معماریِ واقعی + دیاگرام (+ بلوکِ تصحیح) |
| [10 threat_model](10_security_threat_model.md) | تهدیدهای پرتأثیر + کنترل/شکاف |
| [12 risk_register](12_risk_register.md) | R-01..R-20 با P0–P4 + مهار/اصلاح/تأیید |
| [14 questions](14_questions_and_answers.md) | ۱۵ سوالِ تصمیم‌ساز (Gate 2) |
| [15 target_2027](15_target_architecture_2027.md) | توصیهٔ گزینهٔ B (بازآراییِ ماژولار) |
| [21 final_scorecard](21_final_scorecard.md) | کارت‌امتیازِ ۲۵-محور |
| [22 sources](22_sources_and_version_assumptions.md) | منابع + فرضیاتِ نسخه + تصحیح‌ها |
| [mega_prompt_for_agent](mega_prompt_for_agent.md) | مگاپرامپتِ خود-ممیزیِ آماده |
| [agent_response_template](agent_response_template.md) | قالبِ ۱۷بندیِ پاسخ |
| [risks_and_security_audit](risks_and_security_audit.md) | ممیزیِ ریسکِ نسخهٔ قبلی |
| [v2_architecture_proposal](v2_architecture_proposal.md) | V2 (سه سندِ پایه + ۷ افزوده) |
| [testing_plan](testing_plan.md) | قوانینِ سوئیت + شکاف‌های پوشش |
| [**20 security_architecture_review 2026-07-16**](20_security_architecture_review_2026-07-16.md) | **ممیزیِ ۶-محورِ ۳۰۵-ایجنته (خصمانه): ۳ High دستی-تأییدشده (CWE-93 RCE، دور زدنِ STOP، revokeِ خاموشِ گارد) + ۹ Med + ۷۲ Low + ۵ ریشه + رودمپ ۳۰-۶۰-۹۰. صفر Critical.** |

## سه چیزِ فوریِ محتاجِ توجه (از حکم)
1. **ارزیابی تقریباً وجود ندارد** — صفر eval-datasetِ خصمانه؛ ۱۲ تستِ یتیم/green-lie.
2. **PIIِ ویژه (DNA/EEG + پارتنر)** فقط با policyِ متنی — نه گاردِ کد، نه مسیرِ حذف.
3. **یک اجرا را نمی‌شود input→output بازسازی کرد** — correlation_id نویزِ per-emit، structlog تاریک.

## قدمِ بعد
پاسخ به `14_questions` → Gate 4 (معماریِ هدف) → Gate 5 (برنامهٔ Patch) → Gate 6 (working-copy) → Gate 7 (تست+rollback). هیچ‌کدام بدونِ رأیِ صریحِ تو.
