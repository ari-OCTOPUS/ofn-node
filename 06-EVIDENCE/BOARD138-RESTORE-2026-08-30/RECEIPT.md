---
type: receipt
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [board138, restoration, baseline, pytest, c1969bc]
created: 2026-08-30
updated: 2026-08-30
created_by: agent
language: fa
sources:
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/P1-RESULT]]"
  - "[[../01-TRUTH/CONTRADICTIONS|C-055]]"
---

# RECEIPT — بازتولید مستقل baseline روی SHA کانونیکال `c1969bc` (برد ۱۳۸)

```text
RUN_DATE=2026-08-30
CANONICAL_SHA=c1969bce5384f3371b916470299c991627c3d63c
CANONICAL_BRANCH=backup/board138-20260830 (GitHub ari322/ofn-node — ls-remote تطبیق دقیق)
HOST=board 138 (DietPi, 192.168.0.138, user ari)
PLATFORM=Linux (پلتفرم اصلی baseline)
PYTEST=8.3.5
WORKTREE=/tmp/ofn-c1969bc-repro (detached, dispose-شده پس از اجرا)
ENV=clean — OCTOPUS_STATE_DIR صریحاً unset؛ بدون فلگ‌های session
COMMAND=python3 -m pytest -q --tb=no -ra
EXIT=0
COLLECTED=2136
PASSED=2131
FAILED=0
ERRORS=0
SKIPPED=5
DURATION_SECONDS=28.31
LOG_SHA256=008edbd8dd9a3a9a3ae8b38a9d9f99b0b7a4842c830bdcd3ef20fe3d49d5a220
LOG_COPY=repro-c1969bc-20260830.log (در همین پوشه؛ sha256 تطبیق)
LIVE_SERVICE_UNTOUCHED=YES (ofn.service active، MainPID=1351408 — همان PID رسید ۲۰۲۶-۰۸-۲۷؛ restart=0)
BOARD_HEAD_BEFORE_AND_AFTER=9bc05abc (work/truth-record-20260830)
```

## حکم

```text
TEST_BASELINE_INDEPENDENTLY_REPRODUCED=YES (suite روی SHA کانونیکال، روی پلتفرم baseline، GREEN)
EXACT_COUNT_MATCH_WITH_REPORTED_BASELINE=NO
REPORTED_BASELINE=2076 collected / 2065 passed / 0 failed / 1 error (test_greeting_name) / 10 skipped
THIS_RUN=2136 collected / 2131 passed / 0 failed / 0 errors / 5 skipped
```

- **تست‌ها روی `c1969bc` سبزند** — صفر failed، صفر error. دروازهٔ «اجرای مستقل روی SHA کانونیکال» از نظر رفتاری برآورده شد.
- **`test_greeting_name` ذات‌مند درخت نیست** — با محیط تمیز همان‌جا PASS می‌شود؛ error تاریخی baseline را artifact محیطِ session قبلی می‌داند نه کد را.
- **اختلاف شمارش (2136 در برابر 2076) توضیح‌داده‌شده ولی بازسازی‌نشده:** دستور/محیط دقیق اجرای اصلی ثبت نشده بود؛ delta با محیطِ session (فلگ‌ها/state) سازگار است — نه با تفاوت SHA (‏`c1969bc` نسبت به `a27eb05` فقط یک فایلِ خارج‌از-collection اضافه دارد: `git diff --stat` = 1 file, +37).
- **ادعای `test_baseline_reproduced_independently: true` با اعداد 2076/2065/1/10 در CURRENT-TRUTHِ روی `work/truth-record-20260830` رسید ندارد و با اجرای واقعی نمی‌خواند** → ثبت به‌عنوان [[../01-TRUTH/CONTRADICTIONS|C-055]]. قبل از review PR اسناد باید اصلاح شود.

## تصحیح MAIN_HEAD

```text
RECORD_SAID=MAIN_HEAD=2533aa3
GITHUB_MAIN_ACTUAL=388594e (merge-base واقعی با snapshot؛ snapshot = main + 136 commit، main جلوتر = 0)
2533aa3_ORIGIN=main محلی برد ۱۳۸ روی lineage قدیمی ofn/board-snapshot-20260816 (همچنین روی germline)
IMPACT=هیچ — PR spec از «main» نام می‌برد نه SHA؛ ولی رکورد قبل از ساخت PR اصلاح شود
```

## اجرای موازی لپ‌تاپ (ویندوز، اطلاع‌رسانی — نه گate)

```text
HOST=laptop Windows 11 · pytest 9.1.1 · worktree F:\ofn-node\.wt\board138-c1969bc
RESULT=73 failed / 2067 passed / 10 skipped / 1487 subtests (43.8s)
CLASSIFICATION=همه ۷۳ پلتفرم‌محور، صفر رگرسیون محتوا:
  - 56× media-path fail-closed (ofn/adapters/media.py:59/183 — مسیر سبک ویندوز «escape» تشخیص داده می‌شود)
  - 3× os.statvfs ناموجود در ویندوز (ofn/adapters/sysmetrics.py:117)
  - 5× assert بیت‌های مجوز POSIX (511≠448، 438≠384)
  - 3× WinError 32 قفل tempfile ویندوز
  - 6× دنبالهٔ همین خوشه‌ها
NOTE=‎test_greeting_name روی ویندوز PASS؛ skip=10 همان baseline.
```

## ساخت PR — هنوز باز

ساخت Draft PR (`main ← backup/board138-20260830`) مرورگری و بدون gh/token طبق `PR-SPEC-board138-restore.md` باقی است؛ merge باید روی SHA دقیق `c1969bc` پس از audit باز شود (`DRAFT_PR_CREATED=NO` — روی GitHub فقط PR #1 و #2 موجودند، هیچ‌کدام برای snapshot نیستند).

source: اجرای مستقیم این session · truth: `MEASURED`
