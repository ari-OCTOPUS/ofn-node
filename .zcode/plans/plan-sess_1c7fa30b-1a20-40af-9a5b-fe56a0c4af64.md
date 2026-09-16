# 🐛 پلنِ دیباگ و یکپارچه‌سازیِ Accounting — ۲۰۲۶-۰۷-۱۸ (جلسهٔ ۲)

> سه agent موازی کل سیستم رو اسکن کردن. یافته‌های واقعی (تأییدشده) و کاذب (رد‌شده) جدا شدن. این پلن فقط روی مشکلاتِ واقعی تمرکز داره.

---

## 🔍 نتیجهٔ ممیزی (سه agent)

### یافته‌های تأییدشده‌ی واقعی (🔴 + 🟡)

| # | مشکل | شدت | مدرک |
|---|---|---|---|
| **B1** | **review-session stale**: ۳۰ txn_id در `order` لیست دیگه در store نیستن (store از ۵۲۸ به ۸۱۴ رشد کرد ولی session قدیمی موند). وقتی `/review` به این موقعیت‌ها برسه، خطا یا skip نامناسب. | 🔴 | `review-session.json` — ۳۰ hex/numeric ID غایب |
| **B2** | **منیو button stale**: دکمهٔ منو هنوز می‌گه «💰 دارایی‌ها/حساب» ولی به `_finance_text` (که «وضعِ من» برمی‌گردونه) وصل می‌شه. | 🟡 | `approval_channel.py:1001` |
| **B3** | **دکمهٔ keyboard expert پنهان نیست**: هیچ راهی برای کاربرِ عادی برای رسیدن به `_finance_text_expert` وجود نداره. اگه مالک (تو) نسخهٔ کامل بخوای، باید کدت رو عوض کنی. | 🟡 | عدم وجود `/finance_expert` یا callback |
| **B4** | **`OCTOPUS_SYNTH_EVENT_DRIVEN=1` duplicate** در flags.cmd خط ۱۱۶ و ۱۳۱. | 🟡 | `OCTOPUS-flags.cmd:116,131` |
| **B5** | **`OCTOPUS_WIRE_MINING=1` در دو جا**: `.env:20` و `flags.cmd:64`. همون مقدار ولی maintenance risk. | 🟡 | `.env:20`, `flags.cmd:64` |
| **B6** | **`TG_CENTER_BOT_TOKEN` در flags.cmd**: token واقعی در flags.cmd خط ۱۳۳ (gitignore شده ولی شکننده — اگه اون خط پاک شه، leak). | 🟡 | `flags.cmd:133` |
| **B7** | **`ORGANISM-STATE.accounting` sidecar نه در `.gitignore`**: file ساخته نمیشه فعلاً (چون flag بعد از استارت اضافه شد)، ولی وقتی ساخته شه، tracked نخواهد بود و noise/خطر احتمالی. | 🟡 | `.gitignore` — الگوی `ORGANISM-STATE.*` نیست |
| **B8** | **`chrono.db-wal` / `chrono.db-shm` نه در `.gitignore`**: فایل‌های binary که هر tick تغییر می‌کنن. الان به‌عنوان modified نشون داده می‌شن. | 🟡 | `.gitignore` — `*.db-wal`, `*.db-shm` نیست |
| **B9** | **شکافِ تستِ COA validity**: هیچ تستی وجود نداره که account codeهای `journal_bridge.map_txn` رو در برابر COA چک کنه. اگه در آینده کسی account code رو عوض کنه، شکست silent. | 🟡 | `test_journal_bridge.py` |
| **B10** | **شکافِ تستِ hash unification**: هیچ تستی نیست که `_content_hash == txn_store._hash` رو تأیید کنه. اگه یکی از دو تابع drift کنه، regression silent. | 🟡 | `test_accountant.py` یا جدید |
| **B11** | **`_EXPENSE_BY_OWNER_DEFAULT` اکنون فقط fallback**: وقتی config غایبه استفاده می‌شه. ولی نام‌های واقعیِ طرف‌حساب هنوز در source code هستن (به‌عنوان default). این هنوز PII محسوب می‌شه. | 🟡 | `journal_bridge.py:48` |

### یافته‌های کاذب (رد شدند)

| # | ادعا | رد |
|---|---|---|
| ❌ D3 | «COA base accountها حذف شدن» | **اشتباه.** `coa()` در `ledger_core.py:91` merge می‌کنه: `out = dict(DEFAULT_COA); out.update(overrides)`. baseها از DEFAULT_COA میان و هنوز هستن. تستِ session قبلی ۳۲ حساب رو تأیید کرد. |
| ❌ «organsim not running» | **اشتباه.** agent سوم تأیید کرد ports 8771/8772/8773 همگی LISTENING. |
| ❌ «writeback queue missing = bug» | **درست ولی نه bug.** writeback فقط در اولین `/sync` بعد از restart اجرا می‌شه. flag هنوز live نشده. |

---

## 🎯 مأموریت این پلن

> **یکپارچه‌سازی و دیباگ:** رفعِ ۱۱ یافتهٔ تأییدشده، اضافه‌کردنِ تست‌های گمشده، و restart organism تا تغییرات زنده بشن. همه‌چیز برگشت‌پذیر و پشتِ pathspec-scoped commit.

---

## فاز ۱ — رفعِ data staleness (🔴 بحرانی)

**۱.۱ reset review-session** — session فعلی stale (۳۰ ID غایب). دو راه:
- **(الف) reset کامل**: حذفِ `review-session.json` → دفعهٔ بعد `/review`، session تازه از storeِ فعلی (۸۱۴ تا) می‌سازه.
- **(ب) filter	order**: حذفِ IDهای غایب از `order` لیست، حفظِ `done`/`idx`.

**پیشنهاد: (الف) reset کامل** — چون `done=0` و `idx=0` (هیچ پیشرفتی نبوده)، session قابل‌حفظ نیست. snapshot به `_Archive`، بعد حذف.

**۱.۲ verify journal-proposals** — agent سوم تأیید کرد ۱۶ پیشنهاد همگی valid (txn_id موجود، balanced، account codes در COA). هیچ کاری لازم نیست — فقط در گزارش ثبت شه.

**تحویل:** session تازه، proposals معتبر.

---

## فاز ۲ — رفعِ UX seam‌ها (🟡)

**۲.۱ منیو button** — خط ۱۰۰۱: «💰 دارایی‌ها/حساب» → «📊 وضعِ من» (تطابق با header جدید).

**۲.۲ راهِ رسیدن به expert view** — اضافه‌کردنِ `/finance!` (یا `?expert`) که `_finance_text_expert` رو برمی‌گردونه. این به تو (مالک) اجازه می‌ده نسخهٔ کامل رو ببینی بدونِ تغییرِ کد. فقط در handle_command یک branch کوچک.

**۲.۳ دکمهٔ برگشت از expert به ساده** — در `_finance_text_expert` یک inline keyboard button «📊 نسخهٔ ساده» اضافه شه.

**تحویل:** منیو button درست، expert view قابل‌دسترس.

---

## فاز ۳ — رفعِ flag hygiene (🟡)

**۳.۱ حذفِ duplicate `OCTOPUS_SYNTH_EVENT_DRIVEN`** — خط ۱۳۱ رو پاک کنم (۱۱۶ بمونه).

**۳.۲ حذفِ `OCTOPUS_WIRE_MINING` از `.env`** — فقط در flags.cmd بمونه (منبعِ واحد). ولی صبر — `.env` loader شاید قبل از flags.cmd لود شه. بررسی: ترتیب لود در organism.py. اگه `.env` اول لود شه و flags.cmd بعد، flags.cmd برنده‌ست (آخرین `set`). پس حذف از `.env` امنه.

**۳.۳ انتقالِ `TG_CENTER_BOT_TOKEN` و `TG_CENTER_CHAT_ID` به `.env`** — این‌ها secret هستن، باید در `.env` باشن نه flags.cmd. flags.cmd فقط non-secret toggle‌ها. بعد از انتقال، از flags.cmd پاک کنم.

**تحویل:** flagهای تمیز، secretها در جایِ درست.

---

## فاز ۴ — رفعِ git hygiene (🟡)

**۴.۱ افزودن به `.gitignore`:**
```
_ops/state/ORGANISM-STATE.accounting
_ops/state/ORGANISM-STATE.*
*.db-wal
*.db-shm
```
(الگوی `ORGANISM-STATE.*` همه sidecarها رو پوشش می‌ده، نه فقط accounting.)

**۴.۲ بررسیِ فایل‌های tracked که باید gitignored باشن** — `git ls-files` بگیرم، هر فایلِ state که نباید tracked باشه رو `git rm --cached`.

**تحویل:** tree تمیز، خطرِ نشتیِ PII صفر.

---

## فاز ۵ — تست‌های گمشده (🟡)

**۵.۱ test_coa_validity** — تستِ جدید در `test_journal_bridge.py`: assert همهٔ account codeهای `map_txn` (1000/2200/4000/5000/5100/5200/5300/6000) در `coa(profile)` موجودن. اگه در آینده کسی code عوض کنه، تست fail.

**۵.۲ test_hash_unification** — تستِ جدید در `test_accountant.py` (یا فایل جدید): assert `_content_hash(t) == txn_store._hash(date, cents, desc, account)` برای چند input. اگه drift کنن، fail.

**۵.۳ test_acct_sync_dispatch** — تستِ جدید: `acct:sync` callback از طریق `dispatch_callback` → `_cmd_acct_sync`. الان فقط `/sync` مستقیم تست شده.

**۵.۴ test_no_jargon_in_simple_finance** — تستِ加固: `_finance_text()` نباید هیچ‌کدام از اصطلاحاتِ ممنوع رو داشته باشه (Dr/Cr/ATO/خالصِ بانکی/سنتِ سازگار/دفترِ داخلی). بعضی هستن ولی کامل‌تر کنم.

**تحویل:** regression guard برای هر سه نوع تغییر.

---

## فاز ۶ — رفعِ PII default (🟡)

**۶.۱ `_EXPENSE_BY_OWNER_DEFAULT`** — نام‌های واقعی (rent/sume/maliheh/behzad) در source. دو راه:
- **(الف)** keyها رو به entity_id-based تغییر بدم: `{"party:abbas-rent": "5200", ...}` — ولی این شکل‌گیری داده رو پیچیده می‌کنه.
- **(پیشنهاد)** **(ب)** default رو به empty `{}` تغییر بدم. config file (gitignored) منبعِ واحد. اگه config غایبه، `_expense_by_owner()` empty برمی‌گردونه و `_expense_account` به category/desc hint یا 6000 برمی‌گرده. این همون رفتارِ صادقانه‌ست — اگه نگاشت نیست، متفرقه. ولی این یعنی اگه config پاک شه، ۴ owner از قبل نگاشت‌شده به 6000 می‌رن (رفتار متفاوت). باید با تأییدِ تو باشه.

**پیشنهاد: (ب) ولی با هشدار** — empty default، چون config file واقعاً هست و از قبل بررسی شده. اگه config روزی پاک شه، log warning بده.

**تحویل:** صفر PII در source code.

---

## فاز ۷ — restart و verification (🔴 حیاتی)

**۷.۱ backup نهایی** — snapshot همهٔ state فعلی به `_Archive/state-2026-07-18-pre-restart/`.

**۷.۲ اجرای تست‌های کامل** — همهٔ ۱۶+ فایل تست سبز بمونن بعد از تغییرات.

**۷.۳ restart organism** — ایجادِ `STOP-ORGANISM` + `RESTART-REQUESTED`، بعد RUN-ORGANISM.bat رو اجرا می‌کنم (یا تو دستی). بعد از restart:
- flagهای جدید live می‌شن
- `acct_beat` اولین بار در epoch ۱ اجرا می‌شه (نه فوری — بعد از ۲۴۰ beat)
- `/sync` دستی → اولین writeback (auto-backfill ۲۱ confirmed)

**۷.۴ verification بعد از restart:**
- `ORGANISM-STATE.accounting` ساخته شه
- `telegram-poll.json` ts به‌روز
- heartbeat جدید
- `/sync` در تلگرام (اگه بتونی تست کنی)

**تحویل:** organism زنده با همهٔ تغییرات، accounting beat فعال.

---

## فاز ۸ — commit و state docs (🟢)

**۸.۱ commit با pathspec** — فقط فایل‌هایی که تغییر دادم:
- `.gitignore`
- `_ops/budget/approval_channel.py` (UX seam‌ها)
- `_ops/OCTOPUS-flags.cmd` (flag hygiene — ولی gitignore شده، پس نه)
- `.env` (flag hygiene — ولی gitignore شده، پس نه)
- `_ops/legs/journal_bridge.py` (PII default)
- `_ops/tests/test_journal_bridge.py` (COA validity test)
- `_ops/tests/test_accountant.py` یا فایل جدید (hash test)
- `03 - Projects/Accounting/PROJECT.md` (Active Context)

نکته: `flags.cmd` و `.env` gitignored هستن، پس تغییراتشون commit نمی‌شه — این درسته.

**۸.۲ به‌روزرسانی PROJECT.md** — entry برای این جلسهٔ دیباگ.

**تحویل:** commit تمیز با pathspec، docs به‌روز.

---

## ترتیبِ اجرا (چک‌لیست)

```
[ ] فاز ۱: snapshot + reset review-session
[ ] فاز ۲: منیو button + /finance! expert + دکمهٔ برگشت
[ ] فاز ۳: حذف duplicate flags + انتقال TG_CENTER به .env
[ ] فاز ۴: gitignore additions + git rm --cached بررسی
[ ] فاز ۵: ۴ تستِ جدید (COA/hash/dispatch/no-jargon)
[ ] فاز ۶: empty PII default + warning log
[ ] فاز ۷: backup + تست کامل + restart organism + verify
[ ] فاز ۸: commit با pathspec + PROJECT.md
```

## نقاطِ توقف

- **قبل از فاز ۳.۳:** انتقالِ `TG_CENTER_BOT_TOKEN` به `.env` — اگه `.env` loader ترتیبِ خاصی داره، شاید نشکنه. ولی می‌تونم بدون ریسک انجام بدم چون token فقط انتقال پیدا می‌کنه.
- **قبل از فاز ۶.۱:** empty default ممکنه رفتار رو تغییر بده اگه config پاک شه. ولی config هست و بررسی شده. اگه خواستی، این فاز رو skip کنیم.
- **قبل از فاز ۷.۳:** restart organism نیاز به تأییدِ تو داره — چون organism فعلی live و در حال کاره. اگه الان restart کنیم، کارهای در حال انجام متوقف می‌شن.

## معیارِ موفقیت

- review-session تازه و سازگار با store (۸۱۴ تا).
- منیو button با header جدید تطابق داره.
- `/finance!` به نسخهٔ expert می‌رسه.
- صفر duplicate flag، صفر secret در flags.cmd.
- ۴ تستِ جدید regression guard اضافه شده.
- صفر PII در source code (defaultها هم).
- organism restart شده با flagهای جدید live.
- همهٔ تست‌ها سبز، commit تمیز.

## ضدالگوها

1. **فاز ۵ رو skip نکنم** — تست‌های گمشده دقیقاً چیزایی هستن که اجازه دادن باگِ دو-هش و stale session کشف نشن.
2. **`.env` یا flags.cmd رو در commit نذارم** — هر دو gitignored هستن.
3. **restart بدونِ snapshot نکنم** — همیشه قبل از تغییراتِ بزرگ، `_Archive`.
4. **PII default رو حذف نکنم بدونِ بررسیِ config** — اگه config پاک شه، رفتار عوض می‌شه.
5. **از فاز ۷.۳ (restart) بدونِ تأییدِ تو نگذرم** — organism live هست.