# LANE-REPORT — PR-259-RESOLVE-20260918

GOV_VERSION=V8 · LADDER=L2 · repo: `ari-OCTOPUS/ofn-node` · کار روی PR #259 (نویسنده: Elahe-z)

## خواسته
رفع کانفلیکت PR #259 با main پس از merge شدن #248 — با دو قضاوت مشخص: (۱) `tools/log_outcome.py` نسخهٔ main (#248) برنده است، (۲) در `tools/owner_digest.py` هر دو قابلیت باید زنده بمانند.

## آنچه شد
1. worktree جدا `F:/wt-pr259` (کلون اصلی dirty بود — دست‌نخورده ماند).
2. `git merge origin/main` (main=**2ec0aeda**) روی شاخهٔ `fix/accounts-100-cap`.
3. **فقط یک کانفلیکت واقعی**: `tools/log_outcome.py` (add/add) → با نسخهٔ main حل شد (`git checkout origin/main --`)، الان byte-identical با main (۰ خط diff).
4. `tools/owner_digest.py` **خودش تمیز merge شد** (دو diff روی ناحیهٔ متن مشترک تصادم نکردند). تأیید وجود هر دو مجموعه:
   - شاخهٔ #259: `_MOBILE_RE` (۳) · `_is_direct` (۴) · `_direct_caveat` (۳) · `_has_mobile` (۲) · `_extract_mobiles` (۲) · `--include-unverified` · `AUTO_DISCOVERY_TAG` (۳)
   - main #248: autofill دیجست روزانه، تایمرهای git-sync، مرتب‌سازی mobile-priority
5. **verify محلی:** کل سوئیت `9866 passed, 29 skipped, 8213 subtests` (۱۱۰s) — شامل `test_log_outcome.py` (مال main)، `test_b2b_discovery.py`، `test_enrichment.py`، تست‌های digest و `test_root_hygiene.py`.
6. push بدون force: `b3b68ce5..f208a458  HEAD -> fix/accounts-100-cap` (fast-forward؛ تاریخ نویسنده دست‌نخورده).

## وضعیت PR بعد از push (اندازه‌گیری‌شده)
- `mergeable: MERGEABLE` (قبلاً CONFLICTING) · `mergeStateStatus: BLOCKED`
- چک‌ها روی head جدید `f208a458`: `hygiene` pass · `require-fresh-base` **pass** · تست‌های ubuntu/observation/restore/observatory pass · `full-suite` در حال اجرا · **تنها fail: `require-independent-approval`** (ساختاری — فقط Elahe-z یا aram-ui، هرگز نویسنده/بات).
- نکتهٔ فنی: گیت `require-fresh-base` تعریفش «PR head must contain the current base head» است — **merge کافی است، rebase لازم نیست**؛ لذا شاخهٔ نویسنده force-push نشد. (رانِ دومِ همین چک با وضعیت `cancelled` از رویداد `pull_request_review` بود، نه شکست.)

## #262 (تصمیم صریح: دست نزدم)
merge-base آن با main روی `dba9971a` است (قبل از #248) و کدش به helperهای موبایلِ #259 تکیه دارد؛ rebase قبل از merge شدن #259 یعنی از دست دادن آن helperها. ترتیب درست: **#259 اول merge شود، بعد #262**.

## rollback
- شاخه: `git push origin b3b68ce5:fix/accounts-100-cap --force-with-lease` (بازگشت به وضعیت قبل؛ نیاز به force → فقط با تصمیم مالک).
- worktree: `git worktree remove F:/wt-pr259` (کلون اصلی untouched).

## evidence
- کامیت resolve: `f208a458` (parents: `2ec0aeda` + `b3b68ce5`)
- PR: https://github.com/ari-OCTOPUS/ofn-node/pull/259 · head `f208a458ae1bbb9650853d52da5d1114e8ddab98`

---

## ضمیمه — موج دوم (PR #260 + merge #259، 2026-09-18 01:30–01:45Z)

### #259 MERGED (squash → `88840181`, 01:33:37Z)
- چون `require-independent-approval` بعد از push اول باطل شده بود، `aram-ui` روی head جدید (`f208a458`) دوباره **APPROVED** داد (01:26:56Z)؛ هر دو رانِ گیت بازاجرا شدند → **صفر چک failing** → merge با روش مخزن (squash، مثل #248/#254).

### #260 (`fix/enrichment-bugs-and-digest-regex`) — کانفلیکت رفع و push شد (`3d74b757`)
- **طبقه‌بندی قرمزها (که قبلاً نامعلوم بود):** قرمزی CI این شاخه **نقص نبود، اثر ترتیب**: `tests/test_enrichment.py` به ۴ ماژول `ofn.enrichment.{evidence,lessons,sources,strategy}` نیاز داشت که فقط روی شاخهٔ #259 بودند. با merge شدن #259، ماژول‌ها به main آمدند.
- رفع‌ها: `phones.py`/`researcher.py`/`agents/b2b_discovery.py` → نسخهٔ شاخه (سوپرستِ اصلاحی، +137 خط) · دو فایل تست → نسخهٔ شاخه (۱۰۰۳/۱۱۷۹ خط در برابر ۹۳۳/۱۱۴۲؛ صفر و یک خط منحصربه‌main → چیزی از main حذف نشد) · `tools/owner_digest.py` → فایل main + فیکس regex موبایل شاخه (جداکنندهٔ فاصله/خط‌تیره در پیش‌شمارهٔ کشور + فرم پرانتزی «(+61)»).
- **verify محلی:** ۱۸۶ تست پاس (شامل ۶ تست regex موبایل)؛ diff نهایی نسبت به main فقط افزوده است (۳۱۰ insert / ۱۲ delete) و **صفر فایل صفر-بایت**.
- وضعیت فعلی #260: `MERGEABLE` · hygiene pass · fresh-base pass · تست‌ها در حال اجرا · **نیازمند ریویو** (درخواست ریویو از aram-ui فرستاده شد).

### درس‌های عملیاتی این موج (ثبت شده برای ایجنت بعدی)
1. **هر push، تأییدهای قبلی را باطل می‌کند** (`dismiss_stale_reviews: true`) → ترتیب درست: پوش نهایی، بعد ریویو، بعد merge.
2. **تلهٔ redirection:** `git show :3:<path> > <path>` وقتی stage وجود ندارد، فایل را **صفر بایت** می‌کند. همیشه با `wc -l` بعد از بازنویسی تأیید کن و `git diff --cached --numstat` را برای فایل‌های خالی چک کن.
3. `git checkout --ours` در کانفلیکت add/add فایل را می‌نویسد ولی **index را stage نمی‌کند** → `git add` لازم است.
4. `git worktree add` برای هر PR جدا (کلون اصلی dirty بود و دست‌نخورده ماند).

### #262 (تصمیم: همچنان دست نمی‌زنم تا #260 هم merge شود)
- الان `APPROVED` ولی `BEHIND` است (main به `88840181` رسید). با strict بودن گیت‌ها، آپدیت آن **تأیید فعلی را باطل می‌کند** و نیاز به ریویو تازه دارد؛ helperهای موبایلی که کدش به آن‌ها تکیه داشت حالا روی main هستند، پس آپدیتش ایمن است — ولی منظورش را باید در یک پنجره با ریویو تازه انجام داد.
