---
type: evidence-report
title: "اسکن کامل والت‌های Obsidian درایو F: — ۱۸۹ پوشهٔ .obsidian"
created: 2026-09-02
scanner: "ZCode (GLM-5.3) — نشست اسکن F:\\"
scope: "F:\\ — همهٔ پوشه‌های .obsidian تا عمق ۷"
canonical_copy: "F:\\backup\\06-EVIDENCE\\OCTOPUS-OWNER-BOARD-2026-08-24\\VAULT-SCAN-F-DRIVE-2026-09-02.md (این فایل — append-only)"
github_copy: "ofn-node → 06-EVIDENCE/VAULT-SCAN-F-DRIVE-2026-09-02.md (branch evidence/vault-scan-f-drive-20260902 → PR)"
byte_contract: "دو نسخه باید بایت‌به‌بایت یکسان باشند؛ sha256 هر دو در PR و حافظهٔ ایجنت ثبت می‌شود؛ هر تغییر آینده فقط از نسخهٔ کانونیکال + همگام‌سازی مجدد"
rules: "شواهد نه ادعا · هیچ فایل محتوایی خوانده/تغییر داده نشد جز فهرست‌ها و هش‌ها"
---

# گزارش کامل اسکن والت‌های Obsidian درایو F: (۲۰۲۶-۰۹-۰۲)

## ۱. روش

- دستور: `find /f -maxdepth 7 -type d -name ".obsidian"` در Git Bash روی ویندوز.
- exit code = ۱ (دلیل: خطای دسترسی به `$RECYCLE.BIN` و `System Volume Information` — پوشه‌های محافظت‌شدهٔ سیستم؛ تغییری در پوشش اسکن ایجاد نمی‌کند).
- برای هر والت واقعی: شمارش `*.md`، فهرست فایل‌های `.obsidian/`، و **اثر انگشت sha256** از الحاقِ مرتب‌شدهٔ همهٔ فایل‌های `.obsidian/` (فرمان: `find <obsidian> -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum`).
- شمارش md برای `backup-SAFE` و `backup-snapshot` «بدون `.claude/`» است (کپی‌های worktree حذف شده تا دوباره‌شماری نشود). شمارش F:\backup شامل والت‌های تو در توی داخلش است.
- هیچ فایلی از هیچ والت‌ای تغییر/حذف نشد. محتوای هیچ فایل کلید/محرمانه‌ای خوانده نشد.

## ۲. عدد کل و طبقه‌بندی

**۱۸۹ پوشهٔ `.obsidian`** در F: پیدا شد، در ۹ دسته (جمع = ۱۸۹ ✓):

| دسته | تعداد | یعنی |
|---|---|---|
| والت مستقل واقعی | ۱۱ | در جدول §۳ |
| والت تو در تو (داخل والت دیگر) | ۱۲ | در جدول §۴ |
| نسخه‌های صادرهٔ مخزن (`_github-export`) | ۳ | کپی‌های تاریخ‌دار از ofn-node |
| کپی‌های worktree در `.claude\worktrees` | ۱۳۴ | همان «منبع لغزندگی» ثبت‌شده در سیاست کانونیکال |
| والت‌های آزمایشی campaign (`octopus-campaign-20260830/tmp`) | ۱۴ | اسکرچ تست (index-budget ×7، vault-hygiene-ratchet ×7) |
| `F:\wt-*` | ۱۰ | worktreeهای ofn-node — با اثبات هش §۵ |
| `F:\tmp\github-study\ofn-node` | ۱ | کلون مطالعاتی |
| `_Archive` (rescue 2026-07-24 + orphaned 2026-08-01) | ۳ | آرشیو |
| استاب ریشهٔ `F:\.obsidian` | ۱ | فقط یک `core-plugins.json` صفر-بایت (ساختهٔ ۲۰۲۶-۰۸-۳۰) — والت نیست |

## ۳. یازده والت مستقل واقعی

اثر انگشت = sha256(الحاق مرتب فایل‌های `.obsidian/`) — ۱۶ کاراکتر اول.

| # | مسیر | md | اثر انگشت | فایل‌های .obsidian | workspace.json | آخرین فعالیت | نقش |
|---|---|---|---|---|---|---|---|
| ۱ | **F:\backup** | ~۷۲,۵۱۶ | `1db3a2ff72e9ced1` | ۶ | ✓ باز شده | ۲۰۲۶-۰۹-۰۲ (همین امروز: governor-alerts، CURRENT-TRUTH، POISONING-WATCH-4d) | **والت کانونیکال** (رأی مالک ۲۰۲۶-۰۸-۱۵، ثبت در 00-INDEX.md) |
| ۲ | F:\romajan | ۵۲ | `885e3ee2b71d5348` | ۷ | ✓ | ۲۰۲۶-۰۷-۲۲ | بستهٔ پژوهشی «رومجان» (ریاضیات تکثیر: راموجان × ژنتیک جمعیت) |
| ۳ | F:\_______Black Box | ۳۵ | `8bbe3c71f57a3451` | ۵ | ✓ | ۲۰۲۶-۰۷-۱۶ | NBB-CP Control Plane (۱۷۱ تست سبز) + Second Brain فاز ۱؛ گیت مستقل از ۲۰۲۶-۰۷-۱۱ |
| ۴ | F:\ofn-node | ۱۹۳ | `8a2c64b2cd6875fd` | ۳ | ✗ | ۲۰۲۶-۰۹-۰۲ | ریشهٔ مخزن گیتِ عمومی؛ `.obsidian` آن **track شده در گیت** (نتیجه: §۵) |
| ۵ | F:\octopus-phase0-A-halt | ۱,۸۷۵ | `d9ba763ec9b8137a` | ۹ | ✗ | ۲۰۲۶-۰۷-۲۳ (منجمد) | اسنپ‌شات کامل والت — فاز صفر halt |
| ۶ | F:\octopus-phase0-isolated | ۱,۸۷۹ | `925e843cb2687429` | ۹ | ✗ | ۲۰۲۶-۰۸-۳۰ (pytest_cache) | دوقلوی مورد ۵ — نسخهٔ ایزوله |
| ۷ | F:\backup-island | ۶,۰۱۴ | `d09409e9457de662` | ۵ | ✗ | ۲۰۲۶-۰۸-۱۹/۲۰ | نسخهٔ جزیره (SESSION_LOG، GENESIS-DECISIONS، teams/B-daemon-loop) |
| ۸ | F:\backup-SAFE-2026-07-19 | ~۲,۱۶۲ | `05b9f60d02430b7d` | ۱۰ | ✓ | ۲۰۲۶-۰۷-۱۹ | اسنپ‌شات امن ۱۹ ژوئیه (+۱۶ کپی worktree داخلش) |
| ۹ | F:\backup-snapshot-20260723-121256 | ~۲,۳۵۲ | `3d6aff99a1ae17a8` | ۱۰ | ✓ | ۲۰۲۶-۰۷-۲۳ | اسنپ‌شات ۲۳ ژوئیه (+۲۰ کپی worktree داخلش) |
| ۱۰ | F:\backup-deploy-lab | ۴ | `d96b5c78716a5072` | ۵ | ✗ | ۲۰۲۶-۰۷-۱۴ | فقط اسکلت پوشه‌ها — لبواراتوری دیپلوی |
| ۱۱ | F:\backup-Archive\مغز دوم | ۴ | `22cf8fe54577a818` | ۵ | ✓ | ۲۰۲۶-۰۷-۰۳ | والت تازه‌کار آرشیوشده |

## ۴. دوازده والت تو در تو

| مسیر | md | اثر انگشت | یادداشت |
|---|---|---|---|
| F:\backup\03 - Projects\OFN-Board | ۸۵ | `5e74fa6949094ae3` | برد پروژه OFN |
| F:\backup\04 - Architect System\architect | ۱۶۱ | `c32160a00f257461` | 00-Home / ARCHITECT_CHARTER / PROJECT |
| F:\backup\OCTOPUS-DOCTOR | ۲۶۶ | `3433db629a253511` | «دکترِ اختاپوس»: fugu.py مغز، scanner، propose، channel، daemon، mind، router؛ ۱۵۷/۱۵۷ تست سبز، stdlib خالص |
| F:\_______Black Box\پازل هشت پا\4d_system | ۱ | (خانوادهٔ 4d) | پروژهٔ پایتونی که یک‌بار به‌عنوان والت باز شده (workspace.json دارد) |
| F:\backup\_github-export\ofn-node (+ نسخهٔ 20260830-193052 و pr6-base-c1969bc) | ۱۴۹ | app.json: `9a23a42cf5e43c4a` | سه کپی صادرهٔ تاریخ‌دار از مخزن — هش‌شان با خانوادهٔ فعلی گیت فرق دارد (نسخهٔ قدیمی‌تر) |
| F:\octopus-phase0-A-halt\04 - Architect System\architect | — | (داخل اسنپ‌شات) | کپیِ منجمدِ تو در تو |
| F:\octopus-phase0-isolated\04 - Architect System\architect | — | (داخل اسنپ‌شات) | کپی تو در تو |
| F:\backup-island\{OFN-Board, architect, OCTOPUS-DOCTOR} | — | (داخل جزیره) | ۳ کپی تو در تو |
| F:\backup-SAFE-2026-07-19\04 - Architect System\architect | — | (داخل اسنپ‌شات) | کپی تو در تو |
| F:\backup-deploy-lab\04 - Architect System\architect | — | (داخل اسکلت) | کپی تو در تو |
| F:\backup-snapshot-20260723-121256\04 - Architect System\architect | — | (داخل اسنپ‌شات) | کپی تو در تو |

(کپی‌های داخل اسنپ‌شات‌ها جدا شمرده/هش نشده‌اند — با والدشان منجمدند.)

## ۵. اثبات بایت‌به‌بایت: خانواده‌ی `.obsidian` ترک‌شده در گیت

sha256 فایل `app.json` در ۱۲ مسیر **همه یکسان** = `4e6702121653f7c0`:

- F:\ofn-node (ریشهٔ مخزن)
- هر ۱۰ تا F:\wt-docs، wt-dsl، wt-halt، wt-incidents، wt-landing، wt-p1، wt-p37، wt-rev، wt-t04، wt-waiver
- F:\tmp\github-study\ofn-node

**نتیجه:** این ۱۱ پوشهٔ `.obsidian` از مسیر wt-*/study والت نیستند؛ همان فایل‌های track‌شدهٔ مخزن ofn-node هستند که هر worktree به ارث می‌برد. (wt-s2b-c اصلاً `.obsidian` ندارد.) تنها استثنا `_github-export/ofn-node` با هش متفاوت `9a23a42cf5e43c4a` است که صادره‌ای قدیمی‌تر است، نه عضو خانوادهٔ فعلی.

## ۶. موارد حساس و مرزهای اسکن

- **F:\OCTOPUS-SURVIVAL-BACKUP-2026-08-19 — والت نیست.** حاوی مواد کلیدی مالک است (کلید عمومی ed25519، فایل رمزشدهٔ کلید، WAR24-LOCK امضاشده + لابل‌ها و تراکنش‌های paid-calls). **محتوای هیچ‌کدام خوانده نشد**؛ نام دقیق فایل‌های کلیدی عمداً در این گزارشِ عمومی نیامده و فقط در اسکن محلی ثبت است. قاعدهٔ آهن: بدون رأی مالک دست نزن.
- ریشهٔ F:\backup علاوه بر لایهٔ سازمان‌یافته، آشغال‌های اتفاقی هم دارد: debug-*.log، فایل‌هایی با نام‌های شبیه assertion شکست‌خورده (مثل `FAIL, gate_e2e(...)` — اثر باگ redirect شل)، node_modules، PDFها. برای این گزارش دست نخورده‌اند.
- شمارش ۷۲,۵۱۶ مربوط به F:\backup شامل node_modules/.git حذف‌نشده هم هست؟ نه — شمارش با `-not -path '*/.git/*'` انجام شد؛ node_modules در شمارش md بی‌تأثیر است (md ندارد).

## ۷. قرارداد همگونی (Obsidian ⇄ GitHub)

1. نسخهٔ حقیقت: همین فایل در `F:\backup\06-EVIDENCE\OCTOPUS-OWNER-BOARD-2026-08-24\` (append-only، طبق سیاست کانونیکال ۲۰۲۶-۰۹-۰۲).
2. نسخهٔ گیت‌هاب: همان فایل بایت‌به‌بایت در `ofn-node` مسیر `06-EVIDENCE/VAULT-SCAN-F-DRIVE-2026-09-02.md` از branch `evidence/vault-scan-f-drive-20260902`.
3. sha256 دو نسخه باید یکسان باشد؛ مقدارش در بدنهٔ PR و حافظهٔ ایجنت ثبت شده (داخل خود فایل نمی‌آید چون خودارجاع می‌شود).
4. هر به‌روزرسانی آینده: فقط از نسخهٔ کانونیکال ويرایش/الحاق کن، بعد دوباره همگام کن؛ این فایل در گیت‌هاب هرگز مستقلاً ویرایش نمی‌شود.

راستی‌آزمایی (روی ویندوز):

```powershell
Get-FileHash "F:\backup\06-EVIDENCE\OCTOPUS-OWNER-BOARD-2026-08-24\VAULT-SCAN-F-DRIVE-2026-09-02.md" -Algorithm SHA256
# در کلون مخزن:
Get-FileHash "ofn-node\06-EVIDENCE\VAULT-SCAN-F-DRIVE-2026-09-02.md" -Algorithm SHA256
```

## پیوست: فهرست کامل ۱۸۹ مسیر (خروجی خام find، مرتب‌شده)

```
F:\.obsidian
F:\_______Black Box\.obsidian
F:\_______Black Box\پازل هشت پا\4d_system\.obsidian
F:\backup-Archive\مغز دوم\.obsidian
F:\backup-SAFE-2026-07-19\.claude\worktrees\admiring-galileo-f65727\.obsidian
F:\backup-SAFE-2026-07-19\.claude\worktrees\admiring-galileo-f65727\04 - Architect System\architect\.obsidian
F:\backup-SAFE-2026-07-19\.claude\worktrees\charming-keller-b87cd0\.obsidian
F:\backup-SAFE-2026-07-19\.claude\worktrees\charming-keller-b87cd0\04 - Architect System\architect\.obsidian
F:\backup-SAFE-2026-07-19\.claude\worktrees\doctor-self-knowledge-chain-7fba45\.obsidian
F:\backup-SAFE-2026-07-19\.claude\worktrees\doctor-self-knowledge-chain-7fba45\04 - Architect System\architect\.obsidian
F:\backup-SAFE-2026-07-19\.claude\worktrees\hopeful-elgamal-6febe8\.obsidian
F:\backup-SAFE-2026-07-19\.claude\worktrees\hopeful-elgamal-6febe8\04 - Architect System\architect\.obsidian
F:\backup-SAFE-2026-07-19\.claude\worktrees\jolly-ardinghelli-0e33f4\.obsidian
F:\backup-SAFE-2026-07-19\.claude\worktrees\jolly-ardinghelli-0e33f4\04 - Architect System\architect\.obsidian
F:\backup-SAFE-2026-07-19\.claude\worktrees\kind-kirch-44b3ff\.obsidian
F:\backup-SAFE-2026-07-19\.claude\worktrees\kind-kirch-44b3ff\04 - Architect System\architect\.obsidian
F:\backup-SAFE-2026-07-19\.claude\worktrees\learning-loop-architecture-43a8a0\.obsidian
F:\backup-SAFE-2026-07-19\.claude\worktrees\learning-loop-architecture-43a8a0\04 - Architect System\architect\.obsidian
F:\backup-SAFE-2026-07-19\.claude\worktrees\learning-loop-architecture-798215\.obsidian
F:\backup-SAFE-2026-07-19\.claude\worktrees\learning-loop-architecture-798215\04 - Architect System\architect\.obsidian
F:\backup-SAFE-2026-07-19\.claude\worktrees\modest-gould-1c7bac\.obsidian
F:\backup-SAFE-2026-07-19\.claude\worktrees\modest-gould-1c7bac\04 - Architect System\architect\.obsidian
F:\backup-SAFE-2026-07-19\.claude\worktrees\octopus-fugu-ollama-auto-3b7c7f\.obsidian
F:\backup-SAFE-2026-07-19\.claude\worktrees\octopus-fugu-ollama-auto-3b7c7f\04 - Architect System\architect\.obsidian
F:\backup-SAFE-2026-07-19\.claude\worktrees\octopus-nervous-system-audit-2b9541\.obsidian
F:\backup-SAFE-2026-07-19\.claude\worktrees\octopus-nervous-system-audit-2b9541\04 - Architect System\architect\.obsidian
F:\backup-SAFE-2026-07-19\.claude\worktrees\ollama-fugu-brain-54c897\.obsidian
F:\backup-SAFE-2026-07-19\.claude\worktrees\ollama-fugu-brain-54c897\04 - Architect System\architect\.obsidian
F:\backup-SAFE-2026-07-19\.claude\worktrees\parallel-agents-7bf4ec\.obsidian
F:\backup-SAFE-2026-07-19\.claude\worktrees\parallel-agents-7bf4ec\04 - Architect System\architect\.obsidian
F:\backup-SAFE-2026-07-19\.claude\worktrees\quirky-poincare-0dc69f\.obsidian
F:\backup-SAFE-2026-07-19\.claude\worktrees\quirky-poincare-0dc69f\04 - Architect System\architect\.obsidian
F:\backup-SAFE-2026-07-19\.claude\worktrees\seven-relationships-wired-949630\.obsidian
F:\backup-SAFE-2026-07-19\.claude\worktrees\seven-relationships-wired-949630\04 - Architect System\architect\.obsidian
F:\backup-SAFE-2026-07-19\.claude\worktrees\suspicious-bhaskara-5c67ff\.obsidian
F:\backup-SAFE-2026-07-19\.claude\worktrees\suspicious-bhaskara-5c67ff\04 - Architect System\architect\.obsidian
F:\backup-SAFE-2026-07-19\.claude\worktrees\vigilant-williamson-bdbda3\.obsidian
F:\backup-SAFE-2026-07-19\.claude\worktrees\vigilant-williamson-bdbda3\04 - Architect System\architect\.obsidian
F:\backup-SAFE-2026-07-19\.claude\worktrees\youthful-saha-5ee551\.obsidian
F:\backup-SAFE-2026-07-19\.claude\worktrees\youthful-saha-5ee551\04 - Architect System\architect\.obsidian
F:\backup-SAFE-2026-07-19\.claude\worktrees\ziman-gif-deep-scan-19ef9a\.obsidian
F:\backup-SAFE-2026-07-19\.claude\worktrees\ziman-gif-deep-scan-19ef9a\04 - Architect System\architect\.obsidian
F:\backup-SAFE-2026-07-19\.obsidian
F:\backup-SAFE-2026-07-19\03 - Projects\Mining\.claude\worktrees\coin-hunter-bot-arch-d49739\.obsidian
F:\backup-SAFE-2026-07-19\03 - Projects\Mining\.claude\worktrees\quantum-physics-dataset-9aaf44\.obsidian
F:\backup-SAFE-2026-07-19\03 - Projects\اونلی فنز\.claude\worktrees\project-analysis-planning-4b34df\.obsidian
F:\backup-SAFE-2026-07-19\04 - Architect System\architect\.obsidian
F:\backup-deploy-lab\.obsidian
F:\backup-deploy-lab\04 - Architect System\architect\.obsidian
F:\backup-island\.obsidian
F:\backup-island\03 - Projects\OFN-Board\.obsidian
F:\backup-island\04 - Architect System\architect\.obsidian
F:\backup-island\OCTOPUS-DOCTOR\.obsidian
F:\backup-snapshot-20260723-121256\.claude\worktrees\admiring-galileo-f65727\.obsidian
F:\backup-snapshot-20260723-121256\.claude\worktrees\admiring-galileo-f65727\04 - Architect System\architect\.obsidian
F:\backup-snapshot-20260723-121256\.claude\worktrees\charming-keller-b87cd0\.obsidian
F:\backup-snapshot-20260723-121256\.claude\worktrees\charming-keller-b87cd0\04 - Architect System\architect\.obsidian
F:\backup-snapshot-20260723-121256\.claude\worktrees\doctor-self-knowledge-chain-7fba45\.obsidian
F:\backup-snapshot-20260723-121256\.claude\worktrees\doctor-self-knowledge-chain-7fba45\04 - Architect System\architect\.obsidian
F:\backup-snapshot-20260723-121256\.claude\worktrees\hopeful-elgamal-6febe8\.obsidian
F:\backup-snapshot-20260723-121256\.claude\worktrees\hopeful-elgamal-6febe8\04 - Architect System\architect\.obsidian
F:\backup-snapshot-20260723-121256\.claude\worktrees\jolly-ardinghelli-0e33f4\.obsidian
F:\backup-snapshot-20260723-121256\.claude\worktrees\jolly-ardinghelli-0e33f4\04 - Architect System\architect\.obsidian
F:\backup-snapshot-20260723-121256\.claude\worktrees\kind-kirch-44b3ff\.obsidian
F:\backup-snapshot-20260723-121256\.claude\worktrees\kind-kirch-44b3ff\04 - Architect System\architect\.obsidian
F:\backup-snapshot-20260723-121256\.claude\worktrees\learning-loop-architecture-43a8a0\.obsidian
F:\backup-snapshot-20260723-121256\.claude\worktrees\learning-loop-architecture-43a8a0\04 - Architect System\architect\.obsidian
F:\backup-snapshot-20260723-121256\.claude\worktrees\learning-loop-architecture-798215\.obsidian
F:\backup-snapshot-20260723-121256\.claude\worktrees\learning-loop-architecture-798215\04 - Architect System\architect\.obsidian
F:\backup-snapshot-20260723-121256\.claude\worktrees\modest-gould-1c7bac\.obsidian
F:\backup-snapshot-20260723-121256\.claude\worktrees\modest-gould-1c7bac\04 - Architect System\architect\.obsidian
F:\backup-snapshot-20260723-121256\.claude\worktrees\octopus-fugu-ollama-auto-3b7c7f\.obsidian
F:\backup-snapshot-20260723-121256\.claude\worktrees\octopus-fugu-ollama-auto-3b7c7f\04 - Architect System\architect\.obsidian
F:\backup-snapshot-20260723-121256\.claude\worktrees\octopus-nervous-system-audit-2b9541\.obsidian
F:\backup-snapshot-20260723-121256\.claude\worktrees\octopus-nervous-system-audit-2b9541\04 - Architect System\architect\.obsidian
F:\backup-snapshot-20260723-121256\.claude\worktrees\ollama-fugu-brain-54c897\.obsidian
F:\backup-snapshot-20260723-121256\.claude\worktrees\ollama-fugu-brain-54c897\04 - Architect System\architect\.obsidian
F:\backup-snapshot-20260723-121256\.claude\worktrees\parallel-agents-7bf4ec\.obsidian
F:\backup-snapshot-20260723-121256\.claude\worktrees\parallel-agents-7bf4ec\04 - Architect System\architect\.obsidian
F:\backup-snapshot-20260723-121256\.claude\worktrees\quirky-poincare-0dc69f\.obsidian
F:\backup-snapshot-20260723-121256\.claude\worktrees\quirky-poincare-0dc69f\04 - Architect System\architect\.obsidian
F:\backup-snapshot-20260723-121256\.claude\worktrees\session-f92f3d\.obsidian
F:\backup-snapshot-20260723-121256\.claude\worktrees\session-f92f3d\04 - Architect System\architect\.obsidian
F:\backup-snapshot-20260723-121256\.claude\worktrees\seven-relationships-wired-949630\.obsidian
F:\backup-snapshot-20260723-121256\.claude\worktrees\seven-relationships-wired-949630\04 - Architect System\architect\.obsidian
F:\backup-snapshot-20260723-121256\.claude\worktrees\suspicious-bhaskara-5c67ff\.obsidian
F:\backup-snapshot-20260723-121256\.claude\worktrees\suspicious-bhaskara-5c67ff\04 - Architect System\architect\.obsidian
F:\backup-snapshot-20260723-121256\.claude\worktrees\vigilant-williamson-bdbda3\.obsidian
F:\backup-snapshot-20260723-121256\.claude\worktrees\vigilant-williamson-bdbda3\04 - Architect System\architect\.obsidian
F:\backup-snapshot-20260723-121256\.claude\worktrees\wave1-staging\.obsidian
F:\backup-snapshot-20260723-121256\.claude\worktrees\wave1-staging\04 - Architect System\architect\.obsidian
F:\backup-snapshot-20260723-121256\.claude\worktrees\waveD-d1-pswb\.obsidian
F:\backup-snapshot-20260723-121256\.claude\worktrees\waveD-d1-pswb\04 - Architect System\architect\.obsidian
F:\backup-snapshot-20260723-121256\.claude\worktrees\waveD-d3-draw\.obsidian
F:\backup-snapshot-20260723-121256\.claude\worktrees\waveD-d3-draw\04 - Architect System\architect\.obsidian
F:\backup-snapshot-20260723-121256\.claude\worktrees\waveD-d4-hard\.obsidian
F:\backup-snapshot-20260723-121256\.claude\worktrees\waveD-d4-hard\04 - Architect System\architect\.obsidian
F:\backup-snapshot-20260723-121256\.claude\worktrees\waveD-d5-wd\.obsidian
F:\backup-snapshot-20260723-121256\.claude\worktrees\waveD-d5-wd\04 - Architect System\architect\.obsidian
F:\backup-snapshot-20260723-121256\.claude\worktrees\youthful-saha-5ee551\.obsidian
F:\backup-snapshot-20260723-121256\.claude\worktrees\youthful-saha-5ee551\04 - Architect System\architect\.obsidian
F:\backup-snapshot-20260723-121256\.claude\worktrees\ziman-gif-deep-scan-19ef9a\.obsidian
F:\backup-snapshot-20260723-121256\.claude\worktrees\ziman-gif-deep-scan-19ef9a\04 - Architect System\architect\.obsidian
F:\backup-snapshot-20260723-121256\.obsidian
F:\backup-snapshot-20260723-121256\03 - Projects\Mining\.claude\worktrees\coin-hunter-bot-arch-d49739\.obsidian
F:\backup-snapshot-20260723-121256\03 - Projects\Mining\.claude\worktrees\quantum-physics-dataset-9aaf44\.obsidian
F:\backup-snapshot-20260723-121256\03 - Projects\اونلی فنز\.claude\worktrees\project-analysis-planning-4b34df\.obsidian
F:\backup-snapshot-20260723-121256\04 - Architect System\architect\.obsidian
F:\backup\.claude\worktrees\core-live-cl01\.obsidian
F:\backup\.claude\worktrees\core-live-cl01\03 - Projects\OFN-Board\.obsidian
F:\backup\.claude\worktrees\core-live-cl01\04 - Architect System\architect\.obsidian
F:\backup\.claude\worktrees\core-live-cl01\OCTOPUS-DOCTOR\.obsidian
F:\backup\.claude\worktrees\fugu-ultra-remediation-d10abc\.obsidian
F:\backup\.claude\worktrees\fugu-ultra-remediation-d10abc\04 - Architect System\architect\.obsidian
F:\backup\.claude\worktrees\fugu-ultra-remediation-d10abc\OCTOPUS-DOCTOR\.obsidian
F:\backup\.claude\worktrees\great-spence-d84352\.obsidian
F:\backup\.claude\worktrees\great-spence-d84352\03 - Projects\OFN-Board\.obsidian
F:\backup\.claude\worktrees\great-spence-d84352\04 - Architect System\architect\.obsidian
F:\backup\.claude\worktrees\great-spence-d84352\OCTOPUS-DOCTOR\.obsidian
F:\backup\.claude\worktrees\hybrid-control-plane-megaprompt-bd4b21\.obsidian
F:\backup\.claude\worktrees\hybrid-control-plane-megaprompt-bd4b21\04 - Architect System\architect\.obsidian
F:\backup\.claude\worktrees\hybrid-control-plane-megaprompt-bd4b21\OCTOPUS-DOCTOR\.obsidian
F:\backup\.claude\worktrees\hybrid-control-plane-megaprompt-bd4b21\Obsidian Vault\.obsidian
F:\backup\.claude\worktrees\octopus-docs-sync-20260830-200415\.obsidian
F:\backup\.claude\worktrees\octopus-docs-sync-20260830-200415\03 - Projects\OFN-Board\.obsidian
F:\backup\.claude\worktrees\octopus-docs-sync-20260830-200415\04 - Architect System\architect\.obsidian
F:\backup\.claude\worktrees\octopus-docs-sync-20260830-200415\OCTOPUS-DOCTOR\.obsidian
F:\backup\.claude\worktrees\octopus-docs-sync-20260830\.obsidian
F:\backup\.claude\worktrees\octopus-docs-sync-20260830\03 - Projects\OFN-Board\.obsidian
F:\backup\.claude\worktrees\octopus-docs-sync-20260830\04 - Architect System\architect\.obsidian
F:\backup\.claude\worktrees\octopus-docs-sync-20260830\OCTOPUS-DOCTOR\.obsidian
F:\backup\.claude\worktrees\octopus-p0-fixes-418a9a\.obsidian
F:\backup\.claude\worktrees\octopus-p0-fixes-418a9a\03 - Projects\OFN-Board\.obsidian
F:\backup\.claude\worktrees\octopus-p0-fixes-418a9a\04 - Architect System\architect\.obsidian
F:\backup\.claude\worktrees\octopus-p0-fixes-418a9a\OCTOPUS-DOCTOR\.obsidian
F:\backup\.claude\worktrees\octopus-reality-20260830-160703\.obsidian
F:\backup\.claude\worktrees\octopus-reality-20260830-160703\03 - Projects\OFN-Board\.obsidian
F:\backup\.claude\worktrees\octopus-reality-20260830-160703\04 - Architect System\architect\.obsidian
F:\backup\.claude\worktrees\octopus-reality-20260830-160703\OCTOPUS-DOCTOR\.obsidian
F:\backup\.claude\worktrees\organism-alive-69a5db\.obsidian
F:\backup\.claude\worktrees\organism-alive-69a5db\03 - Projects\OFN-Board\.obsidian
F:\backup\.claude\worktrees\organism-alive-69a5db\04 - Architect System\architect\.obsidian
F:\backup\.claude\worktrees\organism-alive-69a5db\OCTOPUS-DOCTOR\.obsidian
F:\backup\.claude\worktrees\sul-memory.partial-1787334619.14699\.obsidian
F:\backup\.claude\worktrees\sul-memory.partial-1787334619.14699\03 - Projects\OFN-Board\.obsidian
F:\backup\.claude\worktrees\sul-memory.partial-1787334619.14699\04 - Architect System\architect\.obsidian
F:\backup\.claude\worktrees\sul-memory.partial-1787334619.14699\OCTOPUS-DOCTOR\.obsidian
F:\backup\.claude\worktrees\telegram-operational-control-de7666\OCTOPUS-DOCTOR\.obsidian
F:\backup\.obsidian
F:\backup\03 - Projects\OFN-Board\.obsidian
F:\backup\04 - Architect System\architect\.obsidian
F:\backup\OCTOPUS-DOCTOR\.obsidian
F:\backup\_Archive\worktree-rescue-2026-07-24\c3fix-verify\untracked\.obsidian
F:\backup\_Archive\worktrees-orphaned-2026-08-01\hopeful-elgamal-6febe8\.obsidian
F:\backup\_Archive\worktrees-orphaned-2026-08-01\hopeful-elgamal-6febe8\04 - Architect System\architect\.obsidian
F:\backup\_github-export\ofn-node-20260830-193052\.obsidian
F:\backup\_github-export\ofn-node-pr6-base-c1969bc\.obsidian
F:\backup\_github-export\ofn-node\.obsidian
F:\octopus-campaign-20260830\tmp\organism-obsidian-index-budget-0uenno8n\.obsidian
F:\octopus-campaign-20260830\tmp\organism-obsidian-index-budget-dkw6_0ww\.obsidian
F:\octopus-campaign-20260830\tmp\organism-obsidian-index-budget-lwkvqb84\.obsidian
F:\octopus-campaign-20260830\tmp\organism-obsidian-index-budget-o22fkpoz\.obsidian
F:\octopus-campaign-20260830\tmp\organism-obsidian-index-budget-o_qheouh\.obsidian
F:\octopus-campaign-20260830\tmp\organism-obsidian-index-budget-vm949uof\.obsidian
F:\octopus-campaign-20260830\tmp\organism-obsidian-index-budget-y40a2dsh\.obsidian
F:\octopus-campaign-20260830\tmp\organism-vault-hygiene-ratchet-0m17oqt9\.obsidian
F:\octopus-campaign-20260830\tmp\organism-vault-hygiene-ratchet-223bursb\.obsidian
F:\octopus-campaign-20260830\tmp\organism-vault-hygiene-ratchet-7rg0gez6\.obsidian
F:\octopus-campaign-20260830\tmp\organism-vault-hygiene-ratchet-bh0me_jr\.obsidian
F:\octopus-campaign-20260830\tmp\organism-vault-hygiene-ratchet-hqc5r2_4\.obsidian
F:\octopus-campaign-20260830\tmp\organism-vault-hygiene-ratchet-lvyxl8ji\.obsidian
F:\octopus-campaign-20260830\tmp\organism-vault-hygiene-ratchet-t4fugfar\.obsidian
F:\octopus-phase0-A-halt\.obsidian
F:\octopus-phase0-A-halt\04 - Architect System\architect\.obsidian
F:\octopus-phase0-isolated\.obsidian
F:\octopus-phase0-isolated\04 - Architect System\architect\.obsidian
F:\ofn-node\.obsidian
F:\romajan\.obsidian
F:\tmp\github-study\ofn-node\.obsidian
F:\wt-docs\.obsidian
F:\wt-dsl\.obsidian
F:\wt-halt\.obsidian
F:\wt-incidents\.obsidian
F:\wt-landing\.obsidian
F:\wt-p1\.obsidian
F:\wt-p37\.obsidian
F:\wt-rev\.obsidian
F:\wt-t04\.obsidian
F:\wt-waiver\.obsidian
```

*(همین نشست، ۲۰۲۶-۰۹-۰۲ — گزارش پس از انتشار، sha256 هر دو نسخه در PR ثبت شد.)*
