# RULESET-WORKFLOW-SECURITY-MATRIX — نسخهٔ verify شدهٔ لوکال (جایگزین ویرایش ریموت)
# mission: OCTOPUS-UNIFIED-RECON-AND-VAULT-CANONICALIZATION-20260917
# generated: 2026-09-17 AEST · credential: ari322 (keyring, https) · همهٔ اعداد همین نشست با gh api / ls-remote گرفته شده

## 1. وضعیت repoها (همه مستقیم verify شد)

| Repo | Visibility | Default | HEAD (ls-remote) | شاخه‌ها (ls-remote) | Tracked (کلون) | Open PRs | Tags | Releases |
|---|---|---|---|---|---|---|---|---|
| ofn-node | public | main | `dba9971a80…` | **164** | 3454 | 11 | 16 | 0 |
| Armin | public | main | `4193de1fd1…` | 3 | 5 | 0 | 0 | 0 |
| langar | public | main | `ec039bb7cd…` | 3 | 97 | 0 | 0 | 0 |
| vbaa-patches | public | main | `16d3bff320…` | 4 | 31 | 0 | 0 | 0 |

انطباق با `octopus-repo-facts.json` مالک: **کامل**. اختلاف قبلی ۱۶۹/۱۶۴ = هم‌پوشانی مرز صفحه‌بندی API بود (تأیید ایجنت ریموت + این نشست).

## 2. Ruleset (این بار با جزئیات — بستن آیتم باز ۶)

`protect-main` (id 21988861)، enforcement=**active**، فقط `refs/heads/main`:
قواعد: `deletion`, `non_fast_forward`, `required_linear_history`, `pull_request`.

**نتیجه: ۱۶۳ شاخهٔ دیگر ofn-node + همهٔ شاخه‌های سه repoی دیگر بدون ruleset حفاظتی‌اند.**
(حفاظتِ ad-hoc قدیمی `protected:true` فقط روی main دیده شد.)

## 3. Workflows (تفکیک authored از dynamic)

| Repo | فایل‌های authored | dynamic |
|---|---|---|
| ofn-node | **۵**: full-suite, independent-review-gate, observation-contract, observatory-fixture, restore-drill (همه active) | ۱: github-code-scanning |
| langar | **۰** | ۱: github-code-scanning |
| Armin / vbaa-patches | ۰ | ۰ |

عدد «۶» در فایل مالک درست است اما ترکیبش شفاف نبود؛ «۱» langar اصلاً فایل نیست، dynamic است.

## 4. Secret scanning (جدید — برای ایجنت ریموت مرئی نبود)

**۲ alert باز** در ofn-node، هر دو `telegram_bot_token`، validity=unknown:
- alert#1: created 2026-09-16T12:56:38Z
- alert#2: created 2026-09-16T13:44:08Z

هر دو در بازهٔ رویدادهای push protection دیروز ساخته شده‌اند. هیچ value خوانده/چاپ نشد.
حکم مالک ثبت‌شده (نشست ۰۹-۱۷): rotate = «بعداً». → کارت ۵.

## 5. تلهٔ ابزاری PR (تأیید مجدد با gh)

`gh api .../pulls?state=all` برای PRهای merge شده `merged=null` برمی‌گرداند درحالی‌که `merged_at` پُر است.
`gh api .../pulls/{n}` (get) درست می‌گوید. **قانون: همیشه get.**

## 6. Non-actions این نشست
هیچ push/merge/close/review/comment/reaction/dispatch/branch-delete/ruleset-change/secret-change/restart/deploy/ارسال بیرونی انجام نشد. fetch لوکال (refs/remotes فقط) و clone و ssh فقط‌خواندنی تنها تماس‌های بیرونی بودند.
