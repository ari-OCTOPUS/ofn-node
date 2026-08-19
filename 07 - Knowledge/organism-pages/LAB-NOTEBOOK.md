# LAB-NOTEBOOK (ماشینی)

> machine-generated · grade=MEASURED · منبع: `_ops/lab/runner.py` + `_ops/tests/test_lab_runner.py`

## حکم صادقانهٔ جعبه

- سطح ایزولاسیون: `policy_workspace_env_timeout` — پیشاسکن الگو + scrub محیط + workspace اختصاصی + timeout با کشت درخت + پساسکن.
- `os_namespace_isolation = False` (ویندوز: mount/network-namespace ندارد) → **آزمایشگاه سختِ OS-level نیست**؛ LAB-DOCTOR-CONTRACT gate3 = NOT_VERIFIED.

## تستهای منفی (سبز)

| سناریو | نتیجه |
|---|---|
| import socket | BLOCKED |
| subprocess / os.system | BLOCKED |
| مسیر مطلق (C:/…، ~/…) | BLOCKED |
| دسترسی os.environ (رازها) | BLOCKED |
| حلقهٔ بیپایان | timeout + کشت درخت |
| نوشتن داخل workspace | OK |

## سیاست رویداد امنیتی

هر تلاش برای فرار/دسترسیِ ممنوع: توقف فوری + ثبت append-only + قرنطینه + ارجاع مالک. هیچ mutation بدون عبور از همین گیت اجرا نمیشود.
