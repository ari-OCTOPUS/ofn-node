# brain/ — مغزِ Project-F

> نقشهٔ ماژول · ۲۰۲۶-۰۸-۰۳

## نقش
لایهٔ هوشِ orchestration: مغزِ دوگانه (DualBrainV3 + CortexAugmented)، اکتساب، یادگیری (bandit)، pipeline‌های DM/acquisition، guards، audit.

## Entry points
| فایل | دستور | نقش |
|---|---|---|
| `learning.py` | `python brain/learning.py` | Thompson bandit standalone |
| `audit.py` | (has `__main__`) | تستِ append audit |

## کتابخانه‌های فعال
`dual_brain_v3` (مغز اصلی) · `cortex_augmented` (flag-gated، DualBrainV3 + insight cortex) · `acquisition` + `acquisition_pipeline` · `learning` (Thompson/UCB bandit) · `store` (VaultBank، KPIRollup، LinkState) · `dm_pipeline` · `guards` · `audit` · `brand_naming` · `faq_engine` · `kpi_dashboard`

## ⚠️ یتیم‌های احتمالی (کاندیدِ archive — بررسیِ بیشتر لازم)
این فایل‌ها **هیچ reference فعالی** در کد ندارند (تأییدشده با grep):
- `ab_tracker.py` — آخرین commit: ۲۰۲۶-۰۷-۱۱
- `content_engine.py` — آخرین commit: ۲۰۲۶-۰۷-۱۰
- `project_f_brain.py` — آخرین commit: ۲۰۲۶-۰۷-۱۱
- `lifecycle.py` — آخرین commit: ۲۰۲۶-۰۷-۱۱

**توصیه**: قبل از حذف، `git log -p` و بررسی دستی محتوا. اگر واقعاً مرده‌اند → `09 - Archive/superseded-code/`.

## Env vars
| کلید | نقش |
|---|---|
| `PF_BRAIN_DIR` | مسیرِ state مغز (تست/harness) |
| `PF_AUDIT_FILE` | مسیرِ فایلِ حسابرسی |
| `PF_AUDIT_ORIGIN` | `live` \| `test` مهرِ منشأ |
| `OCTOPUS_WIRE_PROJECTF_CORTEX` | flag: CortexAugmentedBrain فعال |

## وابستگی‌ها
- **درون‌پروژه‌ای**: `pf_os` (cortex_augmented)، `studio`، `langar`
- **اختاپوس**: `_ops/cortex` (via cortex_client pf_os)
- **خارجی**: صفر (stdlib-only)

## تست‌ها
`test_acquisition_pipeline` · `test_dual_brain_v3` · `test_learning` + تست‌های سراسری در `tests/`
