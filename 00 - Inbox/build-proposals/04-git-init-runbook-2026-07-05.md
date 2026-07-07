---
type: proposal
status: draft
tags: [build-proposal, runbook, git-init, gitignore, opsec, safe-bootstrap]
created: 2026-07-05
updated: 2026-07-05
sources: "[[ROTATION_CHECKLIST]], [[04 - Architect System/architect/ARCHITECT_CHARTER|CHARTER]], [[04 - Architect System/scripts/README|scripts/README]], [[04 - Architect System/scripts/gitleaks.toml|gitleaks.toml]], [[_memory/EXPERIENCE-LEDGER|ledger]] ردیف ۵۰/۵۶"
---

# runbookِ امنِ `git init` + `.gitignore`ِ سخت — برای اجرای دستیِ آری

> **این چیست؟** خروجیِ آیتمِ ۴ صفِ حلقهٔ خودکارِ `build-planner-loop`: یک **runbookِ کپی-چسبان** که آری با آن vault را به‌صورتِ امن یک git repo کند — بدونِ اینکه هیچ رازی واردِ تاریخچهٔ git شود. چون init تازه است، تنها commitِ خطرناک، **اولین** commit است؛ کلِ این ترتیب طوری چیده شده که اولین commit تضمیناً پاک باشد.
>
> **فقط-پیشنهاد (propose-only).** من `git` را اجرا **نکردم** (قاعدهٔ سختِ حلقه: بدونِ git/کد/تسک/رمز). vault هنوز non-git است (تأییدِ زنده: ریشه `.git` ندارد). این نوت فقط دستورالعمل است تا **آری با دستِ خودش** اجرا کند. منتظرِ verdictِ آری.
>
> منابع: [[ROTATION_CHECKLIST]] (گیتِ حاکم) · [[04 - Architect System/architect/ARCHITECT_CHARTER|CHARTER]] (پیش‌شرطِ L2) · [[04 - Architect System/scripts/README|scripts/README]] + `gitleaks.toml` (اسکنر) · [[_memory/EXPERIENCE-LEDGER|ledger]] ردیف ۵۰/۵۶ (چرا git پشتِ rotation است) · صف/لاگ: [[00 - Inbox/AUTONOMOUS-RUN-2026-07-05|AUTONOMOUS-RUN]].

---

## ۱) خلاصهٔ سریع (Quick Summary)

vault خارج از git است → **هیچ rollback/تاریخچه/blame نیست** و طبقِ [[04 - Architect System/architect/ARCHITECT_CHARTER|CHARTER]] استقلالِ L2 هم بدونِ git روشن نمی‌شود. راهکارِ امن سه تکه دارد و **ترتیبش حیاتی است**:

1. **اول `.gitignore`ِ سخت را بنویس، بعد `git add`.** اگر برعکس شود، رازها stage و سپس commit می‌شوند و **در تاریخچه می‌مانند** (پاک‌کردنشان از history دردناک است).
2. **قبل از اولین commit، دو گیتِ قطعی:** (الف) `git ls-files` نشان دهد هیچ الگوی راز track نشده؛ (ب) `gitleaks` روی محتوای **staged** سبز باشد.
3. **گیتِ حاکم = rotation.** طبقِ [[ROTATION_CHECKLIST]] و [[_memory/EXPERIENCE-LEDGER|ledger]] (ردیف ۴۹/۵۰) تا ردیف‌های CRITICAL چرخش/revoke نشوند، اسنپ‌شات گرفتن حتی از فایل‌های تمیز هم زود است — چون «حذفِ فایل ≠ rotation؛ حساب باید سرِ سرویس revoke شود».

خروجی: یک repoِ خصوصیِ محلی با اولین commitِ **gitleaks-clean**، کاملاً بازگشت‌پذیر تا قبل از اولین push (`Remove-Item -Recurse -Force .git`).

---

## ۲) تحلیل (Problem · Goal · Constraints · Assumptions · Risks)

- **Problem:** vault نه نسخه‌بندی دارد نه تورِ ایمنیِ محلی؛ ولی حاوی (یا اخیراً حاویِ) رازِ واقعی بوده و `.gitignore`ِ فعلی **ناقص** است (پایین ثابت می‌شود).
- **Goal:** initِ امن که (۱) هیچ راز را commit نکند، (۲) بازگشت‌پذیر باشد، (۳) پیش‌شرطِ L2 را برآورده کند، (۴) قابلِ اجرا با کپی-چسبان توسطِ آری.
- **Constraints:** ویندوز (PowerShell یا Git Bash) · vault خارج از git · حلقه فقط-پیشنهاد، پس **من اجرا نمی‌کنم** · `.agentignore` مطلق · قاعدهٔ Project-F (نام/پلتفرم ماسک).
- **Assumptions (صریح):** (الف) آری repoِ **خصوصی** می‌خواهد نه public؛ (ب) `gitleaks` روی ویندوز نصب است (اگر نه: `winget install gitleaks` یا `scoop install gitleaks`)؛ (ج) هدف اسنپ‌شاتِ vaultِ اسناد است، نه version‌کردنِ `_code/` در این مرحله.
- **Risks و مهارشان:**
  | ریسک | مهار در این runbook |
  |---|---|
  | راز در اولین commit → در تاریخچه می‌ماند | `.gitignore` قبل از `add` + دو گیتِ pre-commit (ls-files + gitleaks --staged) |
  | `.env.example`/`.env.template` با مقدارِ واقعی (گپِ G-01) | الگوی `*.env.*` + `*secret*` که در `.gitignore`ِ فعلی **نیست** |
  | باینری/venvِ WSL (درسِ جلسه ۴: symlinkِ سمی) | الگوهای `*venv*/`، `node_modules/`، باینری در `.gitattributes` |
  | commit پیش از rotation | گیتِ حاکم §۳ — تا CRITICAL بسته نشود، init نکن |
  | نامِ فارسی/RTL و EOL | `.gitattributes` با `* text=auto eol=lf` |

---

## ۳) پیش‌شرط‌های سخت (قبل از تایپِ حتی یک دستور، هر سه باید 🟢 باشند)

1. **🔴 گیتِ rotation بسته است؟** [[ROTATION_CHECKLIST]] را باز کن؛ **همهٔ ردیف‌های CRITICAL باید ROTATED باشند** (نه فقط `.env`‌های حذف‌شده — کلیدها باید سرِ صرافی/سرویس **revoke** شده باشند، طبقِ [[_memory/EXPERIENCE-LEDGER|ledger]] ردیف ۴۹). تا آن موقع → **init نکن**؛ فقط off-box backup (M5) به‌عنوان تورِ ایمنیِ موقت (پایین §۷، گزینهٔ C).
2. **🟢 `gitleaks` نصب و در PATH؟** `gitleaks version` باید نسخه چاپ کند (≥ v8).
3. **🟢 هیچ فایلِ رازِ زنده داخلِ vault نمانده؟** گامِ ۴ pre-flight این را قطعی می‌کند.

> اگر هر کدام قرمز بود، **همین‌جا بایست** و در چت با آری هماهنگ کن. این runbook فرض می‌کند هر سه سبزند.

---

## ۴) Runbook — گام‌به‌گام (PowerShell، از ریشهٔ vault)

> همه از ریشه اجرا می‌شوند. دستورها را **یکی‌یکی** بزن و خروجی هر گام را قبل از گامِ بعد بخوان.

### گام ۰ — pre-flight: تأییدِ نبودِ رازِ زنده
```powershell
Set-Location "C:\Users\Armin\Desktop\backup"

# تورِ پهن (بیشترِ گیرها false-positive مثل cacert.pem/keyword‌اند — فقط برای مرور چشمی):
Get-ChildItem -Recurse -Force -File |
  Where-Object { $_.FullName -notmatch '\\(\.git|_Archive|_Duplicates|node_modules)\\' } |
  Where-Object { $_.Name -match '(?i)(\.env(\.|$)|wallet|seed|\.pem$|secret)' } |
  Select-Object -ExpandProperty FullName
# انتظار: یا خالی، یا فقط secrets-export/* و *.env.example (که در گام ۱ ignore می‌شوند).
# گیتِ قطعیِ راز = gitleaks در گام ۴، نه این فهرست.
```

### گام ۱ — `.gitignore`ِ سخت را بنویس (قبل از هر `git add`)
محتوای کامل زیر را در `.gitignore`ِ ریشه بگذار (**جایگزینِ** نسخهٔ ۲۷۶-بایتیِ فعلی؛ diffِ قبل→بعد در §۵):
```gitignore
# ── .gitignore سختِ vault — هماهنگ با .agentignore + سفت‌سازیِ جلسه ۸ ──
# راز — هرگز track نشود:
secrets-export/
*.env
*.env.*          # گپِ فعلی: .env.example/.env.template مقدارِ واقعی داشتند (G-01)
*secret*         # گپِ فعلی
*wallet*
*seed*
*key*
*.pem

# مقصدهای انتقال + کدِ لوز (خارج از دامنهٔ اسنپ‌شاتِ اول):
**/_code/        # گپِ فعلی: در .agentignore هست، در .gitignore نبود
_Archive/
_Duplicates/

# venv/محیط‌ها — درسِ جلسه ۴: symlinkِ WSL برای ویندوز سمی است:
*venv*/
.venv/
__pycache__/
*.pyc
.pytest_cache/
node_modules/

# ابزار/حالتِ محلی (churn، بی‌ارزشِ نسخه‌بندی):
gitleaks-report.json
.obsidian/workspace.json
.obsidian/workspace-mobile.json
.trash/
```
و یک `.gitattributes` هم بساز (نرمال‌سازیِ EOL + علامتِ باینری، مهار برای نام‌های فارسی/RTL):
```gitattributes
* text=auto eol=lf
*.png binary
*.jpg binary
*.jpeg binary
*.pdf binary
*.xlsx binary
*.docx binary
*.pptx binary
```

### گام ۲ — init (بازگشت‌پذیر تا قبل از push)
```powershell
git init
git branch -M main
```

### گام ۳ — stage کن ولی **هنوز commit نکن**؛ بازبینی کن چه چیزی track می‌شود
```powershell
git add -A

# تعدادِ فایلِ track‌شده (حسِ کلی):
(git ls-files | Measure-Object -Line).Lines

# گیتِ قطعیِ ۱ — هیچ الگوی راز نباید track شود (خروجی باید کاملاً خالی باشد):
git ls-files | Select-String -Pattern '(?i)(\.env|wallet|seed|\.pem|secret|_code/|secrets-export)'
```
اگر خطِ بالا چیزی برگرداند → **commit نکن**؛ الگو را به `.gitignore` اضافه، `git rm --cached <path>` بزن، و گام ۳ را تکرار کن.

### گام ۴ — `gitleaks` روی محتوای **staged** (دقیقاً چیزی که commit می‌شود)
```powershell
# نسخهٔ v8 (protect --staged فقط staged را می‌بیند = دقیقاً محتوای commitِ بعدی):
gitleaks protect --staged --no-banner -c "04 - Architect System/scripts/gitleaks.toml" -v
# نسخهٔ خیلی جدید (v8.18+): معادلش «gitleaks git --staged» است.
echo "exit=$LASTEXITCODE"   # 0 = پاک → مجاز به commit. غیرِ ۰ = رازی در staged هست → برنگرد به گام ۳.
```
> **تفاوتِ ظریفِ مهم:** `gitleaks detect --no-git --source .` **کلِ درختِ کاری** را می‌بیند و عمداً `secrets-export/` و `*.env.example` را هم پیدا می‌کند (طبقِ کامنتِ `gitleaks.toml`، این‌ها allowlist نشده‌اند تا «یادآور» بمانند). آن اسکن برای commit **گیت نیست** — چون آن مسیرها gitignore و track‌نشده‌اند. گیتِ commit همان `--staged` بالاست. اگر خواستی یادآورِ درختِ کامل را هم ببینی:
> ```powershell
> gitleaks detect --no-git --source "." -c "04 - Architect System/scripts/gitleaks.toml" -v --report-path gitleaks-report.json
> ```

### گام ۵ — اولین commit (فقط بعد از سبزِ گام ۳ و ۴)
```powershell
git commit -m "chore: initial vault snapshot (post-rotation, gitleaks-clean)"
```

### گام ۶ (اختیاری) — remoteِ خصوصی
```powershell
# فقط repoِ PRIVATE. قبل از هر push دوباره gitleaks بزن.
# git remote add origin <PRIVATE-REPO-URL>
# gitleaks protect --staged --no-banner -c "04 - Architect System/scripts/gitleaks.toml" -v
# git push -u origin main
```

### ROLLBACK (کاملاً بازگشت‌پذیر تا قبل از اولین push)
```powershell
Remove-Item -Recurse -Force .git   # vault به حالتِ non-git برمی‌گردد؛ فایل‌ها دست‌نخورده
```

> **دربارهٔ «تاریخچهٔ حاویِ راز» (سؤالِ صریحِ صفِ آیتم ۴):** چون این `git init`ِ تازه است، **تاریخچه‌ای وجود ندارد** — تنها ریسک، اولین commit است و ترتیبِ بالا آن را پاک نگه می‌دارد. اگر روزی رازی اشتباهی commit شد، یک commitِ اصلاحی **کافی نیست** (راز در تاریخچه می‌ماند)؛ پیش از هر push باید کلِ `.git` حذف و از نو init شود، یا اگر push شده بود، با `git filter-repo`/`BFG` تاریخچه بازنویسی و رازها **سرِ سرویس revoke** شوند.

---

## ۵) diffِ `.gitignore` (قبل→بعد) — چرا نسخهٔ فعلی ناامن است

`.gitignore`ِ فعلیِ ریشه (۲۷۶ بایت) سه گپِ امنیتی دارد که با `.agentignore` (سفت‌سازیِ جلسه ۸) هماهنگ نیست:

| الگو | `.gitignore` فعلی | `.agentignore` | اثر اگر افزوده نشود |
|---|:--:|:--:|---|
| `*.env.*` | ❌ نیست | ✅ هست | `.env.example`/`.env.template`ِ حاویِ مقدارِ واقعی (G-01) **commit می‌شود** |
| `*secret*` | ❌ نیست | ✅ هست | هر فایلِ نام‌دارِ `*secret*` track می‌شود |
| `**/_code/` | ❌ نیست | ✅ هست | کدِ بازبینی‌نشده/رازِ درونِ کد track می‌شود |

**قبل (فعلی):** `secrets-export/`, `*.env`, `*wallet*`, `*seed*`, `*key*`, `*.pem`, `_Archive/`, `_Duplicates/`, `__pycache__/`, `node_modules/`
**بعد (پیشنهادی):** همان + سه الگوی بالا + `*venv*/`/`.venv/`/`*.pyc`/`.pytest_cache/` + `gitleaks-report.json` + `.obsidian/workspace*.json` (کاملِ محتوا در گام ۱).

---

## ۶) trade-off و مقایسهٔ راهکارها

| گزینه | Cost | Complexity | Scalability | Lock-in | چه‌وقت |
|---|:--:|:--:|:--:|:--:|---|
| **A. git init + `.gitignore`ِ سخت + gitleaks** ✅ توصیه | ۱/۱۰ (رایگان) | ۲/۱۰ | ۹/۱۰ | صفر (OSS) | **حالا، بعد از rotation** — سادهٔ درست |
| B. git-crypt / SOPS+age (رازِ رمزنگاری‌شده در repo) | ۳/۱۰ | ۷/۱۰ | ۶/۱۰ | کم (OSS) ولی وابسته به custodyِ کلید | فقط اگر راز *باید* در repo بماند — اینجا لازم نیست چون رازها به secrets-export/password-manager می‌روند |
| C. off-box backup (M5، بدونِ git) | ۱/۱۰ | ۱/۱۰ | ۴/۱۰ (بدون diff/blame) | صفر | **مکملِ A، نه جایگزین** — تورِ ایمنیِ قبل از rotation |
| D. «همه را commit، بعد با BFG پاک کن» ❌ | ۴/۱۰ | ۸/۱۰ | — | — | **نکن** — فقط علاجِ بعد از لغزش؛ راز تا revoke زنده می‌ماند |

**توصیه:** **A** به‌عنوان راهکارِ اصلی (بالاترین ROI: رایگان، ساده، بی‌lock-in، rollbackِ محلی + diff/blame)، و **C (M5)** به‌عنوان مکملِ off-box. این دقیقاً همان دوگانه‌ای است که [[00 - Inbox/build-proposals/03-mycelial-spec-reflexion-2026-07-05|پیشنهادِ ۰۳ / W1]] گفت: git = rollbackِ محلی، M5 = تورِ off-box؛ هر دو لازم‌اند.

---

## ۷) راستی‌آزمایی و گاردها (این نوت)

- **اسکنِ راز روی خودِ این فایل:** هیچ مقدارِ رازِ واقعی ندارد — فقط **الگو/نامِ** الگوها (`*.env`, `*wallet*`, ...) داخلِ code-block برای `.gitignore`. هیچ کلید/سید/کیف/آدرسِ واقعی echo نشد. قاعدهٔ Project-F: هیچ نام/پلتفرمِ Project-F اینجا نیست.
- **stale-view:** همهٔ خواندن/نوشتنِ این اجرا Windows-side انجام شد (مِنتِ سندباکس ledger را ۴۹-خطِ ناقص با بایتِ `d8`ِ بریده نشان داد؛ ویندوز ۵۶ ردیفِ کامل). timestampِ لاگ از `lastRunAt`ِ زمان‌بند، نه `date`ِ سندباکس.
- **validatorها:** بعد از افزودنِ این نوت، هر دو اسکریپت اجرا شدند؛ **صفر خطای جدید** (خطاهای موجود فقط `07 - Knowledge/_audit/*` و همان ۱ لینکِ scout-digest‌اند که از قبل بودند). این فایل در `00 - Inbox/` (SYSTEM_FOLDER) است پس frontmatter‌اش چک شد و سبز است.

---

## ۸) گام بعد (برای آری)

1. **verdict روی گیتِ حاکم:** آیا ردیف‌های CRITICALِ [[ROTATION_CHECKLIST]] ROTATED شده‌اند؟ اگر نه، این runbook منتظر می‌ماند؛ فعلاً فقط M5 (off-box).
2. اگر rotation سبز است: گام‌های ۰→۵ را اجرا کن (۵–۱۰ دقیقه). اسنپ‌شاتِ اول = تورِ ایمنی + پیش‌شرطِ L2.
3. verdict روی جایگزینیِ `.gitignore` با نسخهٔ سخت (§۵) — این را مستقل از init هم می‌شود اعمال کرد.
4. سؤالِ باز: آیا `_code/` بعداً جدا version شود (با gitleaksِ اختصاصی)؟ فعلاً عمداً ignore است.

---

> **پایان — propose-only.** هیچ `git`ی اجرا نشد؛ `.gitignore`/`.gitattributes`ِ vault لمس نشد (فقط محتوای پیشنهادی اینجا نوشته شد)؛ هیچ‌چیزِ canonical/charter/کد/تسک/رمز بدونِ verdictِ آری تغییر نکرد. یک خط برای [[_memory/EXPERIENCE-LEDGER|ledger]] و [[00 - Inbox/AUTONOMOUS-RUN-2026-07-05|صف/لاگ]] ثبت شد.
