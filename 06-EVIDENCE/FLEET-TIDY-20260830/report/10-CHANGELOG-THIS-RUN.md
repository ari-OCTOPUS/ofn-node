# 10 — تغییرات دقیق همین اجرا (OWNER-AUTH-20260830-FLEET-TIDY-01)

## در گیت‌هاب ari-OCTOPUS/ofn-node (فقط شاخهٔ جدید — main دست نخورد)
1. `backup/board180-20260830` جدید @ `28209eff` — والد: 76db516 (کمیت پوش‌نشدهٔ قبلی برد) + ۴۳ فایل (اسناد ریشه، vault/board-life-001، artifacts/concept-tour-phase2، octopus_board_validation.py). مسیر push: برد→لپ‌تاپ→برد ۱۳۸→گیت‌هاب (۱۸۰ اعتبارنامه نداشت). تأیید ls-remote ✓
2. `backup/board182-20260830` جدید @ `294d51c1` — snapshot بدون‌تاریخچهٔ قبلی (orphan root) با ۷۸۴ فایل/۶.۷M. همان مسیر رله. تأیید ls-remote ✓

## روی بردها (فقط-افزودنی)
- ۱۸۰: شاخهٔ backup جدید + یک commit در /opt/octopus/lab (فایل‌های untracked انتخابی stage شدند؛ هیچ فایل tracked تغییر نکرد)
- ۱۸۲: ساخت scratch `/tmp/oct182-preserve-work` (git init محلی) + کپی FIXTURES برای تست (untracked — شاخهٔ پوش‌شده تمیز ماند)
- ۱۳۸: worktree موقت /tmp/octopus-test-138-c1969bce (ساخته و حذف شد) + دریافت دو شاخهٔ رله (backup/board180، backup/board182)

## روی لپ‌تاپ
- EV و reportهای همین پکیج؛ فetch شاخه‌های گیت‌هاب برای تاریخ‌ها؛ هیچ push از لپ‌تاپ به گیت‌هاب انجام نشد

## شمارنده‌های امنیتی
```
MAIN_TOUCHED=NO · FORCE_USED=NO · MERGES_DONE=0 · SERVICES_RESTARTED=0 · EXTERNAL_MESSAGES=0
BRANCHES_DELETED=0 · HISTORY_REWRITES=0 · SECRETS_COMMITTED=0
SCRATCH_LEFT=/tmp/oct182-preserve-work@182 (تصمیم مالک در 07)، /tmp/fleet-*.sh روی ۱۳۸/۱۸۰
```

## پیوست ۱۴۰۵-۰۶-۰۸ بعدازظهر — وضعیت ruleset روی main
- اجرای درخواست فوری مالک (فعال‌سازی ruleset): **BLOCKER** — مرورگر in-app خارج از session گیت‌هاب است (Sign in نمایان)؛ ورود با پسورد یا استخراج token طبق HARD RULES ممنوع. تب تنظیمات آمادهٔ handoff است.
- پس از لاگین مالک، مسیر دقیق: Settings → Rules → Rulesets → New ruleset → «New branch ruleset» → target: `main` → فعال‌سازی: Require a pull request before merging (+1 approval) · Require status checks · Require branches up to date · Block force pushes · Restrict deletions.
- یادآوری: تا وقتی status check واقعی (CI) تعریف نشده، فعال‌کردن «Require status checks» merge را عملاً قفل می‌کند — یا CI اضافه شود یا این گزینه خالی بماند.

## پیوست دوم — اجرای ۷ حکم مالک (2026-08-30 بعدازظهر)
1. ruleset main: **گated — منتظر لاگین گیت‌هاب مالک در مرورگر in-app** (بعد از لاگین: ۵ قاعده ساخته می‌شود)
2. ۲۲۰ فایل ۱۸۰: **DONE — شاخهٔ `archive/board180-unprotected-20260830@c6d6a47b`** (۱۹۶ فایل واقعی، اسکن ۰، پوش رله، ls-verify ✓) — شاخهٔ حفاظتی دست نخورد
3. P4/P5: آماده و **gated روی ruleset** (P5 کامل در patch-proposals/)
4. pytest@182: **DONE — venv ایزوله `.test-venv` + سوئیت exchange اولین اجرا: 17 passed** (manifest کامل)
5. آرشیو evidence: **تست restore PASS** (306 فایل بازیابی) + نسخه دوم روی برد ۱۳۸ (sha256 یکسان)
6. hypno-fugu-mini: **DONE — `backup/hypno-fugu-mini-20260830@0f225571`** (۱۱ فایل سورس، اسکن ۰، ls-verify ✓)
7. حذف integration-138: **DONE — `integration/138-business-spine-20260828` از گیت‌هاب حذف شد** (SHA a27eb053 در SWITCH-CHECK برای بازیابی ثبت است) · scratch سه برد پاک شد
8. repoهای خصوصی لپ‌تاپ: **گated — نیاز به auth (لاگین مرورگر یا credential لپ‌تاپ)**
دریفت جزئی whitespace در vault@۱۸۰ (۱۷ فایل/۲۲خط) شناسایی شد — کاندید P5 آینده، عمداً کامیت نشد.

## پیوست سوم — تصحیح سازمان + آرشیو باندل (2026-08-30 شب)
1. **REPO_RENAMED**: کانونیکال = `ari-OCTOPUS/ofn-node` (حکم مالک). اثبات یک‌بودن مخزن: هر دو URL همان refها را می‌دهند (HEAD=c1969bce، pull/1=d94c42c، pull/2=678975b)؛ وبِ آدرس قدیمی 404 است ولی git-endpoint قدیمی هنوز سرویس می‌کند (rename/transfer). تمام pushهای امروز درست به مخزن کانونیکال رسیده‌اند.
2. **BOARD_PUSH_BROKEN**: بعد از انتقال، push از برد ۱۳۸ با origin جدید = 403 (اعتبارنامهٔ برد به سازمان write ندارد). کامیت `272c06f` (تصحیح CURRENT-TRUTH) از طریق لپ‌تاپ رله و پوش شد ✓. **از این پس pushهای کانونیکال فقط از لپ‌تاپ.**
3. report layer: `ari322/ofn-node` → `ari-OCTOPUS/ofn-node` در تمام گزارش‌ها اصلاح شد (rawها به‌عنوان شاهد تاریخی دست‌نخورده). origin برد ۱۳۸ و لپ‌تاپ به URL سازمان set شد.
4. **BUNDLES**: سه vault غیرمنتشرشده به‌صورت git bundle (کل تاریخچه + همهٔ refها): backup-deploy-lab ‏۲۰۷MB · backup-SAFE ‏۲۵۱MB · phase0-isolated ‏۲۵۲MB — همگی `bundle verify: okay` + sha256 + نسخه دوم روی برد ۱۳۸ ✓ (tar تجربه شد: برای درخت‌های حجیم untracked نامناسب — ۳.۵GB ناتمام حذف شد).
