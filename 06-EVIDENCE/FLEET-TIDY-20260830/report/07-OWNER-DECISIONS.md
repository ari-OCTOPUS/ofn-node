# 07 — هفت تصمیم مالک (هر کدام: گزینه‌ها / ریسک / rollback)

| # | تصمیم | گزینه‌ها | ریسک | rollback |
|---|---|---|---|---|
| 1 | **فعال‌سازی ruleset روی main** (درخواست فوری مالک) | الف) UI گیت‌هاب: require PR + 1 approval + status checks + up-to-date + block force + restrict deletion؛ ب) فقط block force/deletion فعلاً | الف) اگر CI نداریم status check اجباری merge را قفل می‌کند → «Require status checks» را بدون تعریف check خالی نگذارید؛ ب) محافظت ضعیف‌تر | Ruleset را Disable/Delete کنید — بدون تغییر تاریخچه |
| 2 | بایگانی evidence بردها (۱۸۰: ~۳۷۰ فایل؛ ۱۳۸: ۳۹؛ ۱۸۲: RUNS/RECEIPTS/REPORTS) | الف) tar+sha256 دوره‌ای به vault؛ ب) rsync به مقصد دوم؛ ج) بی‌action | ریسک صفر در الف/ب (فقط-خواندنی)؛ بی‌action = مرگ دیسک برد = از دست رفتن تاریخچه | حذف آرشیو از vault |
| 3 | repoهای محلی لپ‌تاپ بدون remote (romajan، Black Box، backup-deploy-lab، backup-SAFE، phase0-isolated، C:\Users\Armin) | الف) push به repo خصوصی گیت‌هاب؛ ب) بایگانی tar؛ ج) رها | الف) نیاز repo خصوصی جدید (تصمیم مالک)؛ ج) ریسک از دست رفتن | حذف remote/push مخالف — کل تاریخچه در tar می‌ماند |
| 4 | hypno-fugu-mini روی ۱۳۸ (بدون remote + ۱۰۷ untracked) | الف) preserve branch مثل ۱۸۰/۱۸۲؛ ب) بایگانی؛ ج) رها | الف) یعنی commit untrackedها در برد — به اسکن secret نیاز دارد | حذف شاخه (قبل از protection) یا نگه‌داشتن |
| 5 | نصب pytest روی ۱۸۲ | الف) pip install --user روی برد؛ ب) venv جدا برای تست؛ ج) اجرا در worktree لپ‌تاپ | الف/ب = تغییر سیستم برد (نیاز مجوز صریح)؛ ج) بدون تغییر برد | pip uninstall / حذف venv |
| 6 | شاخه‌های زائد (`integration/138-business-spine-20260828` که محتوایش در main است؛ بالقوه `ofn/board-snapshot-20260816` از ۰۸-۱۶) | الف) حذف بعد از فعال‌شدن protection؛ ب) archive (rename)؛ ج) رها | حذف شاخه بدون保护 = بازسازی‌پذیر از main؛ ریسک کم | دوباره push از SHA موجود در پیام‌های رسید |
| 7 | پاک‌سازی scratch این اجرا (`/tmp/oct182-preserve-work@۱۸۲` شامل کپی FIXTURES؛ `/tmp/fleet-*.sh@۱۳۸/۱۸۰`) | الف) پاک‌سازی کامل؛ ب) نگه‌داری تا اولین PR merge شده | الف) هیچ (شاخه‌ها روی گیت‌هاب تأیید شده‌اند)؛ ب) اشغال ۲۰۰M دیسک | — |

**اولویت پیشنهادی: 1 → 2 → 7 → بقیه.**
