---
type: reference
status: active
created: 2026-07-03
updated: 2026-07-06
tags: [security, rotation, phase-0]
---


# ROTATION_CHECKLIST


> جایگزین [[04 - Architect System/architect/01-Project/SECRETS-ROTATION-CHECKLIST|چک‌لیست قدیمی G-01]] — این نسخه canonical است.


> **🟢 Security Gate: LIFTED (2026-07-06, verdict صریح آری).** هر ۴ ردیف CRITICAL + Fugu = ROTATED. تک‌منبع وضعیت گیت: §۲ [[04 - Architect System/architect/ARCHITECT_CHARTER|ARCHITECT_CHARTER]]. ردیف‌های HIGH/MEDIUM باز (۱۴ عدد) backlog چرخش‌اند، گیت نیستند و autonomy را قفل نمی‌کنند — مرور در experience-review هفتگی.


**اصل:** هر credential که تا امروز داخل این vault بوده «افشاشده» فرض می‌شود — حتی اگر فایلش الان منتقل شده باشد (کپی‌ها: بکاپ‌ها، chat exportها، سیستم‌های قبلی). چرخش یعنی باطل‌کردن مقدار قدیمی و ساخت مقدار جدید، نه فقط جابه‌جایی فایل.


مقادیر منتقل‌شده: `secrets-export/` در ریشه vault (شامل `hardcoded-secrets.txt` برای ۱۰ مقدار استخراج‌شده از کد). بعد از import به password manager، کل پوشه را از vault خارج و حذف کن.


## جدول چرخش


| # | Credential | Issuer / محل چرخش | جایی که بود | شدت | وضعیت |
|---|---|---|---|---|---|
| 1 | Monero wallet seed | self-custody — کیف پول جدید بساز و موجودی را منتقل کن | `Mining Q/monero wallet.txt` | **CRITICAL** | ROTATED |
| 2 | Bybit API key + secret | bybit.com → API Management → حذف کلید قدیمی | `QuantumAlphaBot/.env` | **CRITICAL** (exchange) | ROTATED |
| 3 | OKX API key + secret + passphrase | okx.com → API → حذف و ساخت مجدد | `QuantumAlphaBot/.env` | **CRITICAL** (exchange) | ROTATED |
| 4 | Anthropic API keys (sk-ant) — چند نسخه | console.anthropic.com → API Keys → Disable قدیمی‌ها | brushline/.env · Robo-data/.env · QuantumAlphaBot/.env · fusion-mvp/.env · کاریابی bot/config.py (hardcoded) · scout_all_in_one.py (hardcoded) | **CRITICAL** | ROTATED |
| 5 | OpenAI key (sk-proj) | platform.openai.com → API Keys → revoke | langar-pro/.env (OPENAI_KEY) · کاریابی bot/config.py (hardcoded) | HIGH | OPEN |
| 6 | Telegram bot tokens (≥۶ ربات) | BotFather → `/revoke` برای هر ربات | brushline · QuantumAlphaBot (TELEGRAM_TOKEN, QUANTUM_BOT_TOKEN) · sentinel · langar · silabi_bot.py (hardcoded) · کاریابی bot/config.py (hardcoded) · setup_main.sh · TELEGRAM_SETUP.md · TODO.md · PROJECT_EXPORT_COMPLETE.md | HIGH | OPEN |
| 7 | GitHub token (ghp_) | github.com → Settings → Developer settings → Tokens → revoke | `Robo-data/.env` (GITHUB_TOKEN) | HIGH | OPEN |
| 8 | Discord webhook | تنظیمات کانال Discord → حذف/ساخت مجدد webhook | `QuantumAlphaBot/.env` | HIGH | OPEN |
| 9 | Brave Search API | پنل Brave Search API → regenerate | `langar-pro/.env` | MEDIUM | OPEN |
| 10 | Serper API | serper.dev → regenerate | `brushline/60_code/.env` | MEDIUM | OPEN |
| 11 | LunarCrush API | lunarcrush.com → account → key جدید | sentinel/.env · QuantumAlphaBot/.env | MEDIUM | OPEN |
| 12 | CryptoQuant API | cryptoquant.com → API → regenerate | sentinel/.env · QuantumAlphaBot/.env | MEDIUM | OPEN |
| 13 | Coinalyze API | coinalyze.net → API | `QuantumAlphaBot/.env` | MEDIUM | OPEN |
| 14 | CoinGecko API | coingecko.com → developer dashboard | `Robo-data/.env` | MEDIUM | OPEN |
| 15 | SoChain API | sochain / chain.so → پنل API | `Robo-data/.env` | MEDIUM | OPEN |
| 16 | Postgres password + DATABASE_URL + Redis | لوکال — پسورد جدید (استقرار نشده) | `langar-pro/.env` | MEDIUM | OPEN |
| 17 | igk `.kernel_key` | بعد از استقرار واقعی igk دوباره generate می‌شود | `fusion-mvp/logs/igk_state/.kernel_key` | MEDIUM | OPEN |
| 18 | SSH / دسترسی نودهای Hcash (۳۶ متغیر: IPها، SSH_USER و…) | تعویض پسورد/کلید SSH روی هر ۶ نود Orange Pi | `Mining-1/Hcash/config.env` | MEDIUM | OPEN |
| 19 | محتوای `05_راهنمای_API_keys.md` (کاریابی) | بازبینی دستی — هر کلیدی داخلش بود در ردیف مربوط چک شود | فایل کامل به secrets-export منتقل شد | HIGH (بازبینی) | OPEN |
| 20 | `ENV.rar` (Desktop ریشه) — آرشیو env ناشناخته | بازکردن توسط مالک → هر مقدار داخلش در ردیف مربوط | `Desktop/ENV.rar` | **HIGH (بازبینی)** | OPEN |
| 21 | `info.rar` کنار کیف پول Hcash — محتوای ناشناخته | بازکردن توسط مالک → بازبینی | `Desktop/Mining/Mining-1/Hcash/info.rar` | **HIGH (بازبینی)** | OPEN |
| 22 | `New Text Document.txt` (AIFarm-book) — الگوی secret در محتوا | بازبینی دستی مالک | `Desktop/AI-sume/AGI-Personal/AIFarm-book/` | MEDIUM (بازبینی) | OPEN |
| 23 | `docker-compose.yml` (infra-control) — احتمال env مقداردار inline | بازبینی دستی → هر مقدار به ردیف مربوط | `Desktop/AI-sume/AGI-Personal/AiFarm-Lead/infra-control/` | MEDIUM (بازبینی) | OPEN |
| 24 | Sakana Fugu API key (Ultra) | console.sakana.ai → API Keys | password manager مالک (هرگز در vault) | HIGH | ROTATED |


> **الحاقیه ingest Stage 0 (2026-07-03):** نسخه‌های دومِ اکثر credentialهای ردیف‌های 1، 4، 5، 6، 17 روی Desktop (سورس‌های ingest) هم وجود دارند — فهرست کامل مسیرها: [[INGEST-EXCLUDED-SECRETS]]. اصل «افشاشده فرض کن» برقرار است.


## غیرcredential ولی حساس


- `langar/langar.db` — داده شخصی حافظه؛ credential نیست، rotate نمی‌شود؛ فقط جای امن نگه‌دار. (سر جایش مانده.)
- `pre-reorg-backup-2026-07-03.zip` — کپی همه secretهای قدیمی؛ به `secrets-export/` منتقل شد → بعد از rotation حذف یا دیسک آفلاین.
- Chat IDs / OWNER_ID / ABN — شناسه‌اند، secret نیستند؛ چرخش لازم ندارد.


## بعد از هر rotation


1. ستون وضعیت همین جدول را به ROTATED تغییر بده (فقط انسان).
2. مقدار جدید فقط در password manager یا `.env` خارج از vault — هرگز در کد، نوت، chat export یا zip.
3. وقتی همه CRITICALها ROTATED شد: Security Gate در ARCHITECT_CHARTER (فاز ۱) با verdict صریح تو برداشته می‌شود.
4. اعتبارسنجی نهایی: `gitleaks detect` روی `_code`
<!-- Stage 0 ingest 2026-07-03: بایت ناقص UTF-8 انتهای فایل حذف شد؛ جمله gitleaks از قبل بریده بود -->