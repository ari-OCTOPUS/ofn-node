# METADATA-CONFIDENCE-AUDIT — system-wide (2026-08-19، هم‌زمان با Live-4)
## الف) وضعیت store کانونی (OBSERVED)
admitted=490 · با confidence=448 (۴۲ تاریخیِ فاقد — همگی EXCLUDED از واجدیت) · expiry=490/490=100% (وصلهٔ TTL مؤثر)
SYSTEM_DETERMINISTIC_RULE=0 ردیف فعلی — برچسب در کد فعال است ولی دو نویسنده از زمان وصله هنوز چرخه نخورده‌اند؛ در چرخهٔ بعدی SGC/receipt-critic ظاهر می‌شود (یافتهٔ زمان‌بندی، نه نقص)
## ب) حس‌ibilità confidence در ۱۱ تست پروموشن‌شده
| مجموعه | ناحیهٔ confidence | برچسب |
|---|---|---|
| cost_receipt ×9 | خارج از محور confidence (cost_method همان نقش برچسب روش را دارد: REPORTED/ESTIMATE/UNOBSERVABLE/FREE) | روش‌محور، هرگز عددِ پیش‌بینی نیست |
| INC1 ×2 | confidence=0.9 + source=SYSTEM_DETERMINISTIC_RULE + method=RULE-INC1-DETERMINISTIC-0.9 | سیستمی؛ از کالیبراسیون LLM مستثنی |
| prediction-ledger ×7 | confidence متعلق به پیش‌بینی‌کننده (observer/model) — محور Brier | پیش‌بینی‌محور |
نتیجه: هیچ عددی بین سه محور قاطی نمی‌شود — تفکیک برچسب‌محور برقرار.
## ج) نقاط شکاف خط لولهٔ promotion (کشف‌شده در این ممیزی)
FP1: پرچم paid_blocked آداپتور per-call است؛ ماندگاری بین فراخوانی‌ها فقط در سطح driver — نیازمند block-file پایدار (کارت COST-OBS-2)
FP2: ProviderResponse عمداً cost/usage را نمی‌رساند؛ مصرف‌کننده باید cost-receipts.jsonl بخواند (قرارداد مستند شد)
FP3: سیاست «fugu فقط کوتاه» فقط در driver اجرا می‌شود نه در router (کارت ROUTER-POLICY)
FP4: MemoryStore.insert مستقیم همچنان متادیتای ناقص می‌پذیرد (F3-full)
FP5: ثبت exit از pipeline (خطای اپراتور — دو بار رخ داد، هر دو ثبت و اصلاح شد)
FP6: الگوی t_* زیر pytest collect نمی‌شود (CARD-D هنوز باز)
## د) چک‌لیست پاک‌سازی: گذار قرنطینه→پروموشن با سطح confidence راستی‌آزمایی‌شده
| گذار | شاهد تست | confidence |
|---|---|---|
| P2 admission+radar | 8/8 | گیت‌محور؛ LLM فقط propose |
| P4 prediction-ledger | 7/7 | پیش‌بینی‌محور (ضد-backdating) |
| P5 evaluator | artifacts | پوشش provenance سنجیده |
| TTL-patch گیت | پوشش expiry 490/490 | سیستم |
| INC1 دو نویسنده | 2/2+11/11 | SYSTEM_DETERMINISTIC_RULE |
| COST-OBS hook | 11/11+smoke | REPORTED/AUD با FX پین |
هر گذار: diff+rollback+هش در costobs1/ و live1-3/.
