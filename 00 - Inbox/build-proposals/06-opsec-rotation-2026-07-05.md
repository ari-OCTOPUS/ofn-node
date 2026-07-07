---
type: research
status: draft
tags: [research, opsec, rotation, credential-lifecycle, security-gate, build-loop, propose-only]
created: 2026-07-05
updated: 2026-07-05
sources: "[[04 - Architect System/MYCELIAL-MASTER-SPEC|MYCELIAL-MASTER-SPEC]], [[BUILD-BACKLOG]], [[ROTATION_CHECKLIST]], [[00 - Inbox/AUTONOMOUS-RUN-2026-07-05|AUTONOMOUS-RUN]], [[_memory/EXPERIENCE-LEDGER|ledger]]"
---

# digestِ تحقیق — opsec / چرخشِ اعتبارنامه best-practices (۲۰۲۶) + پیشنهادِ بازکردنِ گلوگاه

> **این چیست؟** خروجیِ آیتمِ ۶ صفِ حلقهٔ خودکارِ `build-planner-loop` (فقط-پیشنهاد). یک digestِ منبع‌دارِ ۲۰۲۶ از best-practiceهایِ opsec و **چرخشِ اعتبارنامه** — چون گلوگاهِ فعلیِ کلِ سیستم همین است: تا یک ردیفِ CRITICAL در [[ROTATION_CHECKLIST]] باز است، §Security Gate بسته و autonomy مؤثرِ همه = read-only ([[04 - Architect System/MYCELIAL-MASTER-SPEC|spec]] §۰.۳). بعد نگاشتِ یافته‌ها به spec، یک خطِ **Cross-domain**، و **یک پیشنهادِ عملیِ propose-only** برای بازکردنِ گلوگاه. **هیچ‌چیز اعمال نشد؛ ROTATION_CHECKLIST و charter و spec دست‌نخورده؛ چرخشِ واقعی کارِ آری است (Non-Goal §۱).**
>
> **Problem/Goal/Constraints/Risks:** Problem = گیتِ چرخش بالاترین‌اهرمِ باز است و کلِ build-spine را propose-only نگه داشته؛ Goal = تبدیلِ «چرخش» از یک ردیفِ مبهمِ OPEN/DONE به یک فرایندِ ترتیب‌دارِ منبع‌دار + سخت‌سازیِ رو‌به‌جلو تا شعاعِ انفجارِ نشتِ بعدی کم شود؛ Constraints = propose-only، بدونِ خواندن/echoِ هیچ مقدارِ محرمانه، چرخش دستِ انسان؛ Risk = ثبتِ ناخواستهٔ مقدار → مهار با «فقط اشاره به ردیف، نه مقدار» + اسکنِ محرمانه‌هایِ فایلِ خروجی.

---

## ۱. یافته‌های کلیدی (۵ محور، منبع‌دار)

### محور ۱ — چرخهٔ عمرِ چرخش و ترتیبِ استانداردِ واکنش
- **playbookِ OWASP برای نشت (۴ گامِ ترتیب‌دار):** (۱) **Revoke** فوری (بی‌اعتبارسازی سرِ سرویس) · (۲) **Rotate** جایگزین (ترجیحاً خودکار) · (۳) **Delete** از همهٔ سیستم‌ها و تاریخچه · (۴) **Log** الگوهایِ دسترسیِ پیش از افشا. نکتهٔ حیاتی: **پاک‌سازی = containment، نه remediation.** [1][2]
- **دنبالهٔ امنِ چرخش (ضدِ outage):** مقدارِ نو را بساز → مقابلِ هدف validate کن → تدریجی rollout → بعد قدیمی را disable کن؛ پرش از validate یا cutoverِ یک‌باره = علتِ اصلیِ قطعیِ ناشی از چرخش. [1]
- **شکافِ میدانی:** ۶۴٪ اعتبارنامه‌هایِ نشت‌شده‌وهنوز-معتبرِ ۲۰۲۲ تا ژانویهٔ ۲۰۲۶ **هنوز فعال** بودند؛ الگویِ غالبِ شکست **فرایندی است نه فنی** (sprawl، نبودِ سیاستِ چرخش، نبودِ workflowِ revocation). [1]
- **کلاس‌بندیِ چرخهٔ عمر:** به‌جای یک قاعدهٔ چرخشِ واحد، کلاس‌های جدا (break-glass، کلیدهایِ امضایِ تنظیم‌شده، رازِ دستگاه‌های embedded، grantهایِ OAuthِ بیرونی). چرخشِ سقفِ ۹۰-روزه = الزامِ رایجِ انطباق (ISO/IEC 27001:2022، NIS2). [1]

### محور ۲ — «حذفِ فایل ≠ چرخش» (تأییدِ بیرونیِ درسِ خودِ vault)
- هر رازِ نشت‌شده **بلافاصله compromised** فرض می‌شود؛ حذفِ کد / commitِ نو / بازساختِ repo جلوی سوءاستفاده را **نمی‌گیرد**، چون تاریخچه، forkها و باتِ اسکنر (ثانیه‌ای) باقی می‌مانند. اقدامِ درست: **اول Revoke/disable از داشبوردِ provider**، بعد rotate، و پاک‌سازیِ تاریخچه آخر (= containment). [2]
- ⟶ این عیناً درسِ ثبت‌شدهٔ [[_memory/EXPERIENCE-LEDGER|ledger]] (ردیف ۴۹/۵۰) است: «حذفِ ۳ فایلِ اعتبارنامهٔ محیطی توسطِ آری ≠ rotation؛ اگر حسابی واقعی بوده باید سرِ سرویس revoke شود». حالا با OWASP/Truffle **بیرونی‌تأیید** شد — یعنی گیت با «حذف» بسته نمی‌ماند، فقط با revoke+rotate. [1][2]

### محور ۳ — امنیتِ کلیدِ صرافی (اندامِ Crypto)
- **سطحِ دسترسی:** کلیدِ **فقط-خواندنی (read-only)** نه معامله می‌کند نه برداشت — امن‌ترین برای portfolio-tracker. برای بات، **مجوزِ برداشت را کاملاً غیرفعال** کن و فقط scopeِ لازم را بده. [3]
- **IP allowlist:** بیشترِ صرافی‌هایِ بزرگ کلید را به IPهایِ مشخص محدود می‌کنند؛ کلیدِ دزدیده‌شده از شبکهٔ دیگر بی‌مصرف است. ~۷۰٪ صرافی‌ها IP-security دارند. [3]
- **زمینهٔ ریسک:** حمله‌هایِ کلیدِ صرافی بین دسامبر ۲۰۲۴–ژانویهٔ ۲۰۲۵ **>US$65M** خسارت زد؛ چرخشِ فصلی توصیه شده. [3]
- **تنشِ طراحیِ گره‌خورده به spec:** §۳ برایِ Crypto «bounded-auto SELL» می‌خواهد — ولی کلیدِ read-only نمی‌تواند SELL کند. پس کلیدِ درست = **معاملهٔ محدود (trade-scoped)، بدونِ مجوزِ برداشت، IP-allowlisted** — نه read-only، نه full-access. (این یک پالایشِ مشخصِ §۳/§۶ است.)

### محور ۴ — اعتبارنامهٔ کوتاه‌عمر / scoped / Zero Standing Privilege
- least-privilege + **کوتاه‌عمر/dynamic** (via OIDC یا موتورِ رازِ پویا) شعاعِ انفجار را به‌شدت کم می‌کند؛ **ZSP + مجوزِ زمانِ اجرا (runtime authz)** جای allowlistِ ساکن را می‌گیرد. اعتبارنامهٔ کوتاه‌عمر پیش از آنکه سوءاستفاده شود منقضی است. [4]
- برایِ **هویت‌هایِ غیرانسانی (NHI)/ایجنت‌ها:** حساب‌های ماشینیِ scoped + اعتبارنامهٔ کوتاه‌عمر + vaultِ اختصاصیِ ایجنت. [4]
- **نگاشتِ به آیندهٔ vault:** الگویِ فعلی = اعتبارنامهٔ محیطیِ لوکال (حالا حذف‌شده)؛ best-practiceِ ۲۰۲۶ = vaultِ متمرکز + کوتاه‌عمر + auditِ کامل. ربطِ مستقیم به §۱۰ verdict #2 (git-init: رازها هرگز در تاریخچه) و §۶ (طراحیِ ابزار/اعتبارنامه). [4]

### محور ۵ — عبارتِ بازیابیِ compromised → «sweep» (اندامِ Mining / کیفِ پول)
- اگر عبارتِ بازیابی افشا شد، **زمان حیاتی است**: یک کیفِ نو با عبارتِ **جدید** بساز و همهٔ دارایی را به آدرسِ نو **sweep** کن (خودِ sweep = معادلِ چرخشِ کلید برای کیفِ پول). عبارت/PIN/رمزِ قبلی را بازاستفاده نکن. [5]
- مراقبِ **sweeper-scriptِ** روی حسابِ آلوده باش (به آدرسِ آلوده هزینهٔ gas نریز)؛ برایِ مبالغِ بزرگ hardware + نگه‌داریِ offline؛ بررسیِ HaveIBeenPwned / فعال‌سازیِ ۲FA / چرخشِ رمزهایِ مرتبط. [5]

---

## ۲. نگاشت به ستون (تأیید / چالش) — grounded، نه تزئینی

| یافته | بخشِ spec | حکم |
|---|---|---|
| Revoke→Rotate→Delete→Log؛ Delete = containment نه fix | §۵ چرخهٔ delete · §۱۰ verdict #1 | ✅ **تأیید + شفاف‌سازی** — vault فقط گامِ Delete (ردیف ۴۹) را زده؛ Revoke/Rotate/verify معوق‌اند |
| ۶۴٪ نشت‌ها هنوز فعال؛ شکست فرایندی نه فنی | §۰.۳ Security Gate | ✅ تأیید — چرا گیت با «حذفِ فایل» بسته نمی‌ماند؛ گیت = وضعیتِ فرایند، نه فایل |
| کلیدِ trade-scoped + بدونِ برداشت + IP-allowlist | §۳ اندامِ Crypto · §۶ | ⚠️ **پالایش** — «bounded-auto SELL» کلیدِ read-only را رد می‌کند؛ spec باید scopeِ دقیق را بگوید |
| کوتاه‌عمر / scoped / ZSP + NHI vault | §۶ Tool/credential · §۱۰ #۲ | 🔶 مسیرِ رو‌به‌جلو — بعد از rotation، الگویِ اعتبارنامهٔ محیطی → vaultِ کوتاه‌عمر |
| کلاسِ چرخهٔ عمر (break-glass / امضا / OAuth) | [[ROTATION_CHECKLIST]] | ⚠️ **گپ** — ردیف‌ها یک‌کلاسه‌اند؛ کلیدِ صرافی ≠ عبارتِ بازیابی ≠ توکنِ بات (چرخشِ متفاوت) |
| sweep = چرخشِ کیفِ پول | §۳ اندامِ Mining | ✅ تأیید — «چرخشِ عبارت‌بازیابی» = sweep به آدرسِ نو |

---

## ۳. Cross-domain

> **گلوگاهِ چرخش یک اندامِ افقیِ واحد است که هم‌زمان چند node را قفل کرده:** Lead (چرخشِ ۵ کلید 💰)، Crypto (کلیدِ صرافی)، Mining (عبارتِ بازیابی / sweep)، و architect (git-init پشتِ همین گیت، چون تاریخچه نباید راز داشته باشد). **یک sprintِ چرخشِ ترتیب‌دار هر چهار node را باز می‌کند و §Security Gate را lift می‌کند → کلِ M0..M8 از read-only آزاد می‌شود.** این همان «یک رشته، چند node»یِ *Armillaria* [J]؛ و مکملِ P-05 دیجستِ [[00 - Inbox/build-proposals/05-ai-agent-eng-2026-2026-07-05|۰۵]] است — هر دو به یک اصل خدمت می‌کنند: **کم‌ترین شعاعِ انفجار** (P-05 مرزِ اعتمادِ حافظه؛ P-06 مرزِ اعتمادِ اعتبارنامه).

---

## ۴. پیشنهادِ عملیِ propose-only (P-06) — «runbookِ چرخشِ ترتیب‌دارِ OWASP + سخت‌سازیِ کم‌شعاع»

**چرا این یکی:** گلوگاهِ چرخش تنها گیتی است که کلِ سیستم را propose-only نگه داشته (§۰.۳ / §۱۰#۱)؛ بازکردنش بالاترین ROI را دارد. کم‌هزینه (سند/چک‌لیست)، برگشت‌پذیر، بدونِ اجرا. **این پیشنهاد است — اعمال نشد؛ ROTATION_CHECKLIST / charter / spec دست‌نخورده؛ اجرا کارِ آری.**

**بخشِ الف — بازکردنِ گیت (اقدامِ انسانیِ آری، ترتیبِ OWASP).** برای هر ردیفِ CRITICALِ باز، به‌جای وضعیتِ دوتاییِ «حذف شد؟»، چهار گامِ ترتیب‌دار: **Revoke سرِ سرویس → Rotate جایگزین → Delete/verify (تاریخچه/فایل) → Log**. تأکید: حذفِ اعتبارنامهٔ محیطی در جلسهٔ ۱۳ ([[_memory/EXPERIENCE-LEDGER|ledger]] ۴۹) فقط گامِ ۳ بود؛ گیت تا **Revoke + Rotate + verify-at-service** برای کلیدِ صرافی (Crypto)، ۵ کلید (Lead) و sweepِ کیفِ پول (Mining) بسته می‌ماند. [1][2][5]

**بخشِ ب — سخت‌سازیِ رو‌به‌جلو (بعد از چرخش، تا نشتِ بعدی کم‌شعاع شود).** اعتبارنامه‌هایِ نو را least-privilege صادر کن: کلیدِ صرافی = **trade-scoped، بدونِ برداشت، IP-allowlisted** (گره به «bounded-auto SELL» §۳)؛ توکنِ بات = scoped + چرخشِ فصلی؛ کیفِ پول = sweep به آدرسِ نو، hardware/offline، هرگز داخلِ vault. جاییکه پشتیبانی شد، کوتاه‌عمر/ZSP. [3][4][5]

**diffهایِ ثانویهٔ کاندیدا (برای verdict؛ این اجرا اعمال/بسته نشد):**
- **[[ROTATION_CHECKLIST]] → ماشینِ حالتِ per-row:** ستون‌های `Revoked?/Rotated?/Verified-at-service?/Logged?` به‌جای وضعیتِ دوتاییِ OPEN/DONE (چون «حذف» گیت را نمی‌بندد). — ویرایشِ checklist کارِ انسان.
- **§۳/§۶ spec:** ذکرِ صریحِ scopeِ کلیدِ Crypto (trade-not-withdraw + IP-allowlist) به‌جای «کلید» مبهم.
- **§۵/§۱۰ spec:** گیت را از باینری به **۴-گامیِ OWASP** ارتقا بده (هم‌راستا با §۷، نسخه → v0.2).

---

## ۵. Trade-off پیشنهادِ P-06 (نمرهٔ ۱–۱۰)

| بعد | نمره | توضیح |
|---|---|---|
| Cost | ۹ | فقط سند/چک‌لیست؛ صفر هزینهٔ API افزوده |
| Complexity | ۴ | کم — ترتیبِ ۴-گامی + ۳ قاعدهٔ سخت‌سازیِ اعتبارنامه |
| Scalability | ۸ | کلاس‌بندیِ چرخهٔ عمر با رشدِ اندام‌ها مقیاس می‌گیرد |
| Maintainability | ۹ | سند-محور، هم‌راستا با SDDِ همین vault |
| Security | ۱۰ | مستقیماً بالاترین‌اهرمِ باز (گیتِ چرخش) را هدف می‌گیرد |
| Time-to-Impl | ۷ | چرخش دستِ آری است؛ خودِ runbook کوتاه، ولی اجرا وابسته به سرویس‌هاست |

**ROI: بالا** — کم‌ترین هزینه، بازکنندهٔ کلِ build-spine. هم‌راستا با «در شک read-only» (P8) و Non-Goal §۱ (چرخش کارِ انسان).

---

## ۶. سؤالِ باز برای verdictِ آری
- ماشینِ حالتِ per-row (Revoked/Rotated/Verified/Logged) به [[ROTATION_CHECKLIST]] افزوده شود؟ (ویرایشِ checklist = دستِ انسان)
- بعد از rotation، یک vaultِ رازِ لوکال (OS-keychain / فایلِ رمزنگاریِ `age`) جایگزینِ الگویِ اعتبارنامهٔ محیطی شود؟ — تصمیمِ §۶/معماری = verdict. (نکتهٔ lock-in: OS-keychain بدونِ vendor؛ ابزارهایِ managed مثلِ Vault/Akeyless قابلیتِ بیشتر ولی وابستگی/هزینه دارند.)
- diffِ گیتِ باینری→۴-گامیِ OWASP روی §۵/§۱۰ اعمال شود (نسخه → v0.2 طبقِ §۷)، یا فعلاً فقط به‌عنوانِ ریسکِ ثبت‌شده بماند؟

---

## Sources
- [1] [Secrets Management Best Practices (2026 Guide) — JumpServer](https://www.jumpserver.com/blog/secret-management-best-practices-2026) · [Secrets rotation lifecycle — Passwork](https://passwork.pro/blog/secrets-rotation-lifecycle/) · [Secrets Management Cheat Sheet — OWASP](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [2] [Deleting leaked keys isn't a solution — Truffle Security](https://trufflesecurity.com/blog/remediate-leaked-api-keys-with-key-rotation) · [Remediating a leaked secret — GitHub Docs](https://docs.github.com/en/code-security/tutorials/remediate-leaked-secrets/remediating-a-leaked-secret)
- [3] [Ultimate Guide to API Access for Crypto Exchange Accounts (2026) — CoinLedger](https://coinledger.io/blog/the-ultimate-guide-to-api-access-for-your-crypto-exchange-accounts) · [API Security Best Practices — Coinbase](https://docs.cdp.coinbase.com/get-started/authentication/security-best-practices)
- [4] [Top Secrets Management Tools 2026 — GitGuardian](https://blog.gitguardian.com/top-secrets-management-tools/) · [Secrets Management Cheat Sheet — OWASP](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html) · [Secret Management for AI Agents — Fastio](https://fast.io/resources/best-secret-management-tools-ai-agents/)
- [5] [If your wallet may be compromised, sweep it — Vault12](https://vault12.com/learn/crypto-security-basics/what-is-a-wallet-passphrase/if-your-wallet-may-be-compromised-sweep-it) · [What to do if your project/wallet is compromised — Ledger](https://www.ledger.com/academy/basic-basics/launch-a-crypto-project-securely/what-to-do-if-your-crypto-project-gets-hacked)

> **پایان.** فقط-پیشنهاد. اتصالِ اجرا = آیتمِ ۶ صفِ [[00 - Inbox/AUTONOMOUS-RUN-2026-07-05|AUTONOMOUS-RUN]]. طبقِ §۷/§۱۰، چرخشِ واقعی و اعمالِ diffها منتظرِ verdict/اقدامِ آری است.
