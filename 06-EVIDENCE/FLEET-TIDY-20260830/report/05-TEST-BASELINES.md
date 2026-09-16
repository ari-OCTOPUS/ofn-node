# 05 — baseline تست هر نود (مستقل، هر کدام روی SHA تأییدشدهٔ خودش)

| نود | runner | collected | passed | failed | errors | skipped | محیط |
|---|---|---|---|---|---|---|---|
| ۱۳۸ | pytest 8.3.5 | **2136** | 2131 | 0 | 0 | 5 | worktree جدای /tmp روی `c1969bce`، env: PYTHONDONTWRITEBYTECODE/PYTHONNOUSERSITE/PYTHONHASHSEED=0/TZ=UTC — پس از تست `git status` خالی بود ✓، compileall RC=0 ✓ |
| ۱۸۰ | رسمی ندارد (پوشهٔ tests/ خالی؛ ۹۴ فایل .py tracked) | — | — | — | — | — | `compileall` روی tracked py: RC=0 ✓ |
| ۱۸۲ | unittest (۲ سوئیت) | ~21 | 21 | 0 | 0 | 0 | سوئیت `SANDBOX/tests/test_validator.py`: همه PASS (failures: 0). سوئیت `exchange/tests/test_exchange.py`: **NOT_RUN — pytest روی نود نصب نیست** (نصب = تغییر سیستم → ممنوع). compileall cognition/core/shared: RC=0 ✓ |

## اختلاف شمارش ۲۰۷۶ (قدیمی) با ۲۱۳۶ (امروز)
- اجرای مرجع قدیمی (۰۸-۲۹، روی a27eb05): 2076 collected / 2065 pass / 1 error / 10 skip — **دستور و env آن اجرا هیچ‌جا ثبت نشده** (تناقض C-055 در vault).
- اثبات‌شده: درخت تست `c1969bce` با `a27eb05` برابر است (فقط +۱ فایل خارج‌از-collection)؛ درخت زندهٔ برد و worktree کانونیکال هر دو دقیقاً 2136 جمع می‌کنند.
- جست‌وجوی سازوکار داخل repo: فقط دو فایل تست رفتار وابسته به env دارند (`tests/test_cockpit_v2_owner_queue.py`، `tests/test_cockpit_v2_http.py`) — این skipها را توضیح می‌دهد (۵ در برابر ۱۰) اما +۶۰ اختلاف جمع را نه؛ هیچ `collect_ignore` در conftest نیست.
- **حکم: علت نهایی +۶۰ اثبات نشد (TEST_COUNT_DISCREPANCY_EXPLAINED=NO)؛ مظنون اصلی envِ undocumentedِ آن session است. عدد مرجع از امروز: 2136/2131/0/0/5.**

## به‌روزرسانی 2026-08-30 (حکم مالک: venv ایزوله روی برد)
سوئیت `exchange` برای اولین بار اجرا شد — **17 passed / 0 failed (0.2s)** در venv ایزولهٔ `/opt/octopus-agent/.test-venv` (بدون تغییر سیستم).
env-manifest کامل (طبق BASELINE-MANIFEST-TEMPLATE.txt): python 3.13.5 · pytest 9.1.1 · start=octopus-agent/exchange/tests · NODEID_SHA256=770fdb999db463d1 — raw/182/exchange-baseline.txt
**جمع baseline ۱۸۲: 38 تست (21 validator + 17 exchange)، صفر شکست.**

## پیوست نهایی — P4/P5 اجرا شد (2026-08-30 شب، با مجوز مالک)
- **P4** = `work/board182-test-discovery-init@ea48f421` (از 294d51c1، دو __init__.py). نکتهٔ ریشه‌ای: `test_exchange.py` **pytest-style** است (import pytest، توابع ساده) — unittest به‌درستی ۰ جمع می‌کند؛ runner رسمی این سوئیت **pytest** است (venv برد: 17 passed ✓). unittest-style سوئیت validator با discover/مستقیم هر دو کار می‌کند.
- **P5-138** = `chore/untrack-runtime-artifacts-20260830@1185cc1b` — ‏1783 آرتفکت `.tmp-test*/` از index خارج شد (فایل‌ها روی دیسک باقی‌اند) + `.gitignore`
- **P5-180** = `chore/untrack-evidence-inbox-20260830@24529c3` — ۱۴ فایل evidence/inbox از index خارج شد + `.gitignore` (آرشیوشان: sha256=2ba2da1e)
- هر سه شاخه: ls-verify ✓ · صفر force · شاخه‌های backup لمس نشدند
- باقی‌مانده gated: ruleset main (لاگین مرورگر) · repo خصوصی ۶ repo لپ‌تاپ (GitHub Desktop → Publish repository → Private)
