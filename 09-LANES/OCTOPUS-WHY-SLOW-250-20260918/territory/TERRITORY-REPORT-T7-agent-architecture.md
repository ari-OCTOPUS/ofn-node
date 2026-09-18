# TERRITORY-REPORT — T7-agent-architecture (معماری ایجنت)

`checked: 20 hypotheses · sources: 19 file/probe families · refuted: 0 · confirmed: 6 · partial: 4 · unverified: 10 · owner-needed: 0 · verified-this-session: 4`

## چرا این قلمرو مشکوک بود

> هر نشست از صفر؛ runtime≠commit

## یافته‌های تأییدشدهٔ برتر

- **W-S09** (I4×F3) — دانش پراکنده باعث می‌شود هر ایجنت از صفر جهت‌گیری کند؛ هزینهٔ بازکشف در هر نشست ثابت است
  - دلیل: ENGINEERING-ENTRYPOINT برای همین ساخته شد ولی به 09-04 اشاره می‌کند (F-036)
  - شاهد: 07-HANDOFF/ENGINEERING-ENTRYPOINT-2026-09-04.md, F-036
  - مخرج: یک entry-point زندهٔ ماشینی (STATE.json) بساز که ایجنت فقط آن را بخواند
- **W-146** (I3×F3) — entry-point پروژه به سند ۰۹-۰۴ اشاره می‌کند در حالی که ۰۹-۰۶/۰۹-۰۷ هم وجود دارند و هیچ‌کدام لِین‌های جدید را نمی‌بینند
  - دلیل: F-036: engineering-entrypoint chain stale: AGENTS.md points at 09-04
  - شاهد: AGENTS.md → 07-HANDOFF/ENGINEERING-ENTRYPOINT-2026-09-04.md (F-036)
  - مخرج: AGENTS.md را به یک entry-point زنده وصل کن (نه تاریخ‌دار)
- **W-161** (I3×F3) — رجیستر ۱۶۰ موردی بدهی با ۰ resolved / ۰ executed عملاً فقط انباشت است
  - دلیل: DASHBOARD: by_state open 65 / verified 95 / executed 0 / resolved 0
  - شاهد: 138:state/deep-scan/DASHBOARD.json
  - مخرج: قاعدهٔ جریان: هر هفته n مورد باید به executed/resolved برود وگرنه رشد انبار
- **W-S10** (I3×F3) — دو فایل CURRENT-TRUTH زنده هم‌زمان وجود دارند؛ انتخاب توسط mtime است نه قاعده
  - دلیل: memory: TWO live CURRENT-TRUTH files (OCTOPUS/ + 06-EVIDENCE/)
  - شاهد: 06-EVIDENCE/OCTOPUS-OWNER-BOARD-2026-08-24/CURRENT-TRUTH.md, OCTOPUS/CURRENT-TRUTH
  - مخرج: یکی را کانونیک اعلام و دیگری را pointer تک‌خطی کن
- **W-147** (I4×F2) — runtime دقیقاً worktree را اجرا می‌کند نه commit را — commit رفتار را توصیف نمی‌کند
  - دلیل: DC-03D: glass/imap/selfmodel ExecStart into /home/ari/ofn؛ 5 tracked dirty (+1222/-551)
  - شاهد: 09-LANES (DC-03D) 06-EVIDENCE/board138 dirty overlay
  - مخرج: قاعدهٔ «deploy = commit + checkout» را روی ۱۳۸ اعمال کن (پایان اجرای dirty)
- **W-148** (I3×F2) — ۵ فایل tracked روی runtime آلوده است و self_model_producer سه بدنهٔ واگرا دارد
  - دلیل: DC-03D: 5 tracked dirty؛ self_model has THREE divergent bodies (win/main/runtime)
  - شاهد: 09-LANES (DC-03D)
  - مخرج: سه بدنه را مقایسه و یکی را کانونیک کن؛ دو تای دیگر archive_

## سایر ورودی‌ها (خلاصه)

- W-160 [PARTIAL] خود deep-scan باید سرویس شود وگرنه به همان فراموشی‌ای که فهرست کرده برمی‌گردد
- W-164 [PARTIAL] ۵ سند «نقطهٔ ورود» موازی وجود دارد؛ جهت‌گیری ایجنت مبهم است
- W-149 [PARTIAL] ۵۱۸۴ فایل untracked (۱۰۷MB، ۹۸٪ state) روی runtime — سطح state از git جدا شده
- W-150 [UNVERIFIED] پیش‌بینی‌ها/آمار trackers با runtime اختلاف دارند (PB-4 در سند NOT_RUN، زنده IMPROVED)
- W-151 [UNVERIFIED] یک سند مستندات به‌صراحت «دروغ» علامت خورده (COMMIT-GAP) و هرگز اصلاح نشد
- W-152 [UNVERIFIED] از ۵۰ سیم‌کشی گم‌شده فقط ۲ مورد خودکار رفع شد؛ ۴۸ سیم‌کشی هنوز غایب است
- W-153 [UNVERIFIED] consolidation tick چهار‌بعدی ۱۱ روز مرده بود و پیوستگی خوراکش دوباره اثبات نشده
- W-156 [UNVERIFIED] آرتیفکت‌های N-ALIVE هرگز به ۱۳۸ کپی نشدند (find_channels.py + CATALOG.json)
- W-162 [PARTIAL] ۴۷ فایل با status-word باز (pending/NOT_RUN) در رجیستر بدهی — وضعیت‌ها فقط کلمه‌اند نه ماشین‌خوان
- W-154 [UNVERIFIED] ledger کانونیک GAP وجود ندارد (۰ ردیف در برابر ۶۴ ردیف نسخهٔ markdown) — L6 برای همیشه باز
- W-155 [UNVERIFIED] مُهر QA فاز P6 استناد شده ولی فایل مستقیمش پیدا نمی‌شود
- W-157 [UNVERIFIED] فایل listener imap روی ۱۳۸ (۱۵۸۷۵B) هرگز تأیید نشد و نام‌گذاری lane-matrix تناقض دارد
- W-158 [UNVERIFIED] سه ادعای متناقض درباره llama روی ۱۳۸/۱۸۰ وجود دارد و هیچ‌کدام بازconciliation نشده (resolution: null)
- W-159 [UNVERIFIED] تناقض سه‌مستأجری پورت ۸۷۹۱ با resolution: null رها شده و مسیر callback را مبهم می‌کند
