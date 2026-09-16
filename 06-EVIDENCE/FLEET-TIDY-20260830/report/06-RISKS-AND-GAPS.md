# 06 — ریسک‌ها و شکاف‌ها (با شدت)

| # | ریسک | شدت | شواهد | اقدام پیشنهادی |
|---|---|---|---|---|
| 1 | evidence/رسیدها فقط روی بردها هستند (۱۸۰: ~۳۷۰ فایل evidence در lab؛ ۱۳۸: ۳۹ untracked؛ ۱۸۲: RUNS/RECEIPTS/REPORTS) — قواعد اجازهٔ کامیت‌شان را نمی‌دهد | بالا | raw/180/lab-untracked.txt، raw/138/discovery.txt | تصمیم مالک: بایگانی دوره‌ای tar+sha256 به vault (نه گیت عمومی) |
| 2 | branch protection روی `main` فعال نیست — هر کلونی می‌تواند main را جابه‌جا کند | بالا | raw/github-branch-dates.txt | فعال‌سازی UI: require PR + 1 approval + status checks + block force + block deletion |
| 3 | repoهای لپ‌تاپ بدون remote: romajan، Black Box (۹۸فایل)، backup-deploy-lab، backup-SAFE، phase0-isolated، C:\Users\Armin@a3000f0 | متوسط | raw/laptop/repos-inventory.txt | تصمیم مالک: push به گیت‌هاب خصوصی یا بایگانی |
| 4 | hypno-fugu-mini روی ۱۳۸: بدون remote + ۱۰۷ untracked (۱۱ سورس‌مانند) | متوسط | raw/138/discovery.txt | حفاظت جداگانه یا تصمیم رهاشدگی |
| 5 | pytest روی ۱۸۲ نیست → سوئیت exchange هرگز اجرا نشده | متوسط | raw/182/baseline2.txt | نصب pytest با تصمیم مالک (تغییر سیستم) |
| 6 | شاخهٔ `integration/138-business-spine` الان محتوایش داخل main است — شاخهٔ زائد (حذف = تصمیم مالک) | کم | raw/180 (SYNC-CHECK) | بعد از فعال‌شدن protection، آرشیو/حذف |
| 7 | ۵ فایل untracked رسیدی روی ۱۳۸ (e8-unittest.*) | کم | raw/138/board-branches | بایگانی evidence |
| 8 | فایل آشغال `--help` در $HOME برد ۱۸۲؛ scratch های این اجرا در /tmp بردها | کم | raw/182 | پاک‌سازی آینده (لیست در 10) |

## اصلاح ریسک ۱۸۲ (اندازه‌گیری دقیق 2026-08-30 بعدازظهر)
عدد اولیهٔ «۶,۶۱۶ فایل سورس» venv را هم می‌شمرد. واقعیت:
- سورس واقعی (بدون venv): **۱,۰۱۴** · tracked در شاخهٔ حفاظتی: **۷۸۴ (۷۷٪)**
- بستهٔ `octopus_cognition`: **۱۰۰٪ محافظت شده** (تنها باقی‌مانده: `.pytest_cache/README.md` — آشغال)
- ۲۸۴ فایل untracked باقی: ‏RUNS(۱۲۳)+SANDBOX-run-outputs(۱۲۱)+REPORTS(۲۱)+RECEIPTS(۱۰)+FIXTURES(۴)+متفرقه(۵) — همگی runtime/evidence طبق سیاست
- نتیجه: ریسک «کد اصلی فقط روی eMMC» **بسته شد**؛ آنچه مانده نیاز به تصمیم evidence-archival دارد (بند ۲ تصمیمات مالک)
شواهد: raw/182/not-tracked-analysis.txt · raw/182/coverage.txt

## گیت‌های pre-publish شش repo لپ‌تاپ (raw/laptop/prepublish-gates.txt)
| repo | tracked | secret-hit | >1MB | آماده publish؟ |
|---|---|---|---|---|
| romajan | 187 | 0 | 0 | ✅ بله |
| _______Black Box | 98 | 0 | 0 | ✅ بله (پیشنهاد rename بدون underscoreها) |
| backup-deploy-lab | 1883 | 0 | 0 | ✅ بله |
| backup-SAFE-2026-07-19 | 5262 | **۳** | 0 | ⛔ تا پاک‌سازی: ‏lunarcrush×2 + scout.py محتوای حساس دارند |
| octopus-phase0-isolated | 5696 | **۳** | 0 | ⛔ همان سه فایل (کپی هم‌خانواده) |
| C:\Users\Armin | 5 | 0 | 0 | ⚠️ توصیه: publish نشود — ۵ فایل پراکندهٔ Desktop/Documents است؛ آرشیو بهتر است |
سه فایل مشترک مشکل‌دار (در هر دو repo قدیمی): `03 - Projects/Crypto - etoro/…/lunarcrush_2026-06-15-06-20-24.json` (×۲) و `03 - Projects/Mining/02 - Code/Robo-data/scout.py` + سه سند با نام SECRETS (اسناد متنی دربارهٔ rotation — بازبینی چشمی). قبل از publish: این مسیرها exclude یا ردکت شوند.
