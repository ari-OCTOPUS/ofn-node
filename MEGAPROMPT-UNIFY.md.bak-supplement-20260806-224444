---
tags: [ofn, megaprompt, unify, merge, agent]
aliases: [مگاپرامپت ادغام, Unify Megaprompt, Fugu Core]
updated: 2026-08-06
---

# مگاپرامپت نهایی — ادغام دو ایجنت و ساخت یک مولتی‌ایجنت واحد با حافظهٔ سه‌لایه

> **برای عامل بعدی.** این سند self-contained است؛ بدون دیدن گفتگویی که آن را
> ساخت، قابل اجراست. هر ادعا یک رکورد مستقل پشت سرش دارد (CLAUDE §۸-ب). هر
> عددی که در این سند هست باید قبل از پذیرش با یک `assert` در `tests/` بررسی
> شود (CLAUDE §۸-الف).

**پیوندها:** [[INDEX]] · [[HANDOFF]] · [[DECISIONS]] · [[CLAUDE]] · [[MEGAPROMPT]]

---

## ۰) قانون اساسی — این مگاپرامپت

تو یک مهندس فول‌استک هستی که روی یک اورنج‌پای ۵ پرو (ARM64، ۴ گیگ رم، DietPi)
کار می‌کند. دو پروژهٔ مستقل وجود دارد که هر دو برای یک نفر («آری/سبا») یک
دستیار فارسی تلگرامی می‌سازند:

```
/home/ari/ofn                ← Octopus Field Node · مولتی‌تنانت · ۱۵۰۱ تست
/home/ari/hypno-fugu-mini    ← مینی‌اپ خودهیپنوتیزمی · تک‌کاربر · ۵ تست
```

هدف: **ارتقای hypno با قابلیت‌های OFN**، ساخت یک **حافظهٔ ماندگار سه‌لایهٔ
واحد**، و **اشتراک‌گذاری مغز+RAG+auth** میان دو سرویس — بدون از دست رفتن هیچ
دیتای زنده، بدون شکستن هیچ سرویس، بدون تکرار.

**سه اصل غیرقابل‌مذاکره:**

1. **هیچ دیتایی از دست نمی‌رود.** قبل از هر مهاجرت، WAL را checkpoint کن و هر
   سه فایل `.sqlite`/`.sqlite-wal`/`.sqlite-shm` را با هم کپی کن (CLAUDE §۷).
2. **هیچ سرویسی نمی‌شکند.** `ofn.service` و `hypno-fugu-mini.service` هر دو
   باید `active` بمانند. هر تغییر، restart + smoke check + pytest دارد.
3. **عددها تست‌اند نه جمله.** هر عددی (سهم کوئتا، capacity، timeout) قبل از
   پذیرش باید با `assert` در `tests/` بررسی شود.

زبان UI، پیام‌ها و متن‌های داخل اپ **فارسی، ساده، گرم، غیرفنی** است
([[DECISIONS|D-22]]). کلمات ممنوع در UI: RAG، model، token، API، schema،
payload، inference، dataset، database، backend.

---

## ۱) وضعیت امروز — حقیقت روی زمین

این اعداد را با کوئری زنده تأیید کن، نه با این سند:

```
pytest OFN          python3 -m pytest --co -q   →  ۱۵۰۱ تست جمع‌آوری‌شده
pytest hypno        ۵ تست در tests/test_core.py
DB OFN assistant    assistant_chat_turns=۹ · assistant_chunks=۲۶ (نه ۲/۱۹)
DB hypno            research_docs=۱۲۴ · messages=۲۹ · memories=۰
services            ofn.service active · hypno-fugu-mini.service active
ports               ۸۷۹۱(ziman) ۸۷۹۲(lead) ۸۷۹۳(studio/saba) ۸۷۹۴(owner) ۸۸۹۵(hypno)
```

> ⚠️ `hypno.sqlite-wal` حدود ۴.۱ مگابایت است در حالی که فایل اصلی ۸۴۷ کیلوبایت.
> یعنی اکثر نوشته‌های اخیر در WAL نشسته‌اند. قبل از هر کپی،
> `PRAGMA wal_checkpoint(TRUNCATE)` بزن.

---

## ۲) معماری هدف — سه لایهٔ حافظه + مغز مشترک

```
┌─────────────────────────────────────────────────────────────┐
│                    fugu_core  (پکیج مشترک جدید)               │
│  ~/shared/fugu_core/  · pip install -e · صفر وابستگی بیرونی    │
│                                                              │
│  auth/      verify_init_data · issue_session · verify_session │
│             ReplayGuard · (بدون TenantScope)                  │
│  brain/     RemoteBrain (دو آرگومانی، BrainReply) · CallBudget │
│  scrub/     scrub (برای الگوهایی که می‌گیرد)                   │
│  memory/    لایهٔ سه‌گانهٔ حافظه (پایین‌تر)                     │
│  rag/       FTS5 chunker + retrieve (از hypno برداشت شود)     │
└─────────────────────────────────────────────────────────────┘
         ▲                              ▲
         │                              │
┌────────┴──────────┐          ┌────────┴──────────────┐
│   ofn  (OFN)       │          │  hypno  (Hypno)        │
│  مولتی‌تنانت        │          │  تک‌تنانت синтетик       │
│  TenantScope دارد  │          │  TenantScope ساختگی    │
│  worker async       │          │  sync + CallBudget     │
└────────────────────┘          └────────────────────────┘
```

### لایهٔ سه‌گانهٔ حافظه — تعریف دقیق

هر سه لایه در یک DB جدید `memory.sqlite` می‌نشینند (نه در `assistant.sqlite` و
نه در `hypno.sqlite` موجود — این‌ها دست‌نخورده می‌مانند):

| لایه | نام جدول | چیست | از کجا می‌آید |
|---|---|---|---|
| **۱ اپیزودی** | `memory_turns` | هر تبادل چت (user/assistant + sources + ts + tenant) | OFN `assistant_chat_turns` + hypno `messages` |
| **۲ معنایی** | `memory_facts` | فکت/ترجیح پایدار کاربر دربارهٔ خودش | hypno `memories` + OFN `facts` (subject.predicate) |
| **۳ پیکره** | `memory_corpus` + `memory_fts` | دانش RAG با **FTS5** | hypno `research_docs` + OFN `assistant_chunks` + `saba_rag_seed.txt` |

هر ردیف یک `tenant` (مقدار: `studio`/`lead`/`ziman`/`hypno`/`shared`) و یک
`source` (مقدار: `chat`/`seed`/`brain`/`user`) دارد. این چیزی است که
«هوشمندی» واقعی می‌آورد: مغز قبل از جواب، هر سه لایه را برای *همان کاربر*
می‌خواند.

**قانون جداسازی:** هرگز ردیف‌های یک tenant از لایه‌های ۱/۲ نباید به tenant
دیگری نشت کند (همان قاعده [[DECISIONS|D-21]]). لایهٔ ۳ (corpus) می‌تواند
`shared` باشد.

---

## ۳) نقاط کور بحرانی — قبل از شروع، این‌ها را حل کن

این‌ها چیزهایی است که یک اجرای سرسری را می‌شکنند. ترتیب بر اساس شدت.

### 🔴 B-۱ · کوئتا مجموعش ۱.۰ است — جا برای hypno نیست

`shares` در `ofn/kernel/quota.py:96-98` باید ≤ ۱.۰ باشد. امروز:
`ziman=۰.۴۰ + lead=۰.۴۰ + studio=۰.۲۰ = ۱.۰۰`. افزودن hypno بدون
جدا کردن مجدد، `FailClosedError` می‌اندازد.

**اقدام:** سهم‌ها را دوباره بزن. پیشنهاد: `ziman=۰.۳۶ · lead=۰.۳۶ · studio=۰.۱۸ · hypno=۰.۱۰`.
عدد نهایی باید با `assert sum(shares.values()) <= 1.0` در تست قفل شود. علاوه بر
سهم، به hypno یک `CallBudget` جدا بده (`ofn/kernel/callbudget.py`)، و آن را به
`Rung.REMOTE` (fugu تند) پین کن — هرگز `REMOTE_DEEP` (fugu-ultra، دقیقه‌ها).

### 🔴 B-۲ · `panel_note` یک brain call پنهان در همهٔ write pathهای hypno است

`hypno/run.py:49-54`: هر فراخوانی `memory`/`research`/`import`/`obsidian_export`
یک `self.brain.answer(...)` همگام برای تولید «خلاصهٔ پنل» می‌زند. یعنی یک
نشست hypno به راحتی ۵+ brain call دارد، و ذخیرهٔ یک حافظه روی شبکه بلوکه
می‌شود.

**اقدام:** `panel_note` را از write pathها بردار. آن را به یک کار پس‌زمینه
(مثل `assistant_update` در OFN) یا یک endpoint جدا (`POST /api/panel/note`)
منتقل کن که درخواست ذخیره را بلوکه نکند. این هم کوئتا را کم می‌کند و هم
UX را.

### 🔴 B-۳ · consent در دو پروژه مفاهیم کاملاً متفاوتی دارد

- **OFN consent:** یک *سند* امضاشده توسط *فردی که در محتوا هست*، برای انتشار
  در *پلتفرم نام‌برده*. ماژول `kernel/consent.py` برای «آیا این عکس الان روی
  پلتفرم X منتشر شود» ساخته شده.
- **Hypno consent:** یک بولین «الان در جای امنم و آمادهٔ خودهیپنوتیزمی هستم».

این‌ها **یک چیز نیستند**. forcing یکی روی دیگری غلط است.

**اقدام:** دو store جدا نگه دار. پرچم hypno را از `consent` به
`safety_acknowledged` تغییر نام بده تا تصادم کلمه حل شود. hypno هرگز
`ConsentStore`/`kernel/consent.py` را import نکند.

### 🔴 B-۴ · scrub برای PII فارسی بی‌فایده است

`ofn/kernel/scrub.py:32-53` ایمیل، کلید `sk-`، کارت اعتباری، **تلفن AU (+۶۱/۰)**،
**شماره مالیاتی AU ABN/TFN**، IP را می‌گیرد. کاربر hypno یک نفر در ایران است که
خودهیپنوتیزمی فارسی می‌نویسد. scrub صفر PII فارسی (نام، آدرس، خاطرهٔ تروما)
می‌گیرد — و `scrub.py:15-21` خودش اعتراف می‌کند «نام را نمی‌تواند بگیرد».

**اقدام:** نگو «scrub OFN را روی hypno اعمال کن». بگو: (الف) scrub را برای
الگوهایی که *می‌گیرد* (ایمیل، کلید API که کاربر ممکن است بچسباند) روی hypno
اعمال کن — ارزان و درست؛ (ب) صراحتاً بنویس که scrub نام/آدرس فارسی را نمی‌گیرد،
پس فراخوانی مغز ریموت hypno روایت شخصی کاربر را به ارائه‌دهنده فاش می‌کند — این
یک افشای رضایت‌شده است که کاربر باید در جریان safety/consent بپذیرد؛ (ج) حفاظت
واقعی گیت clinical است — `hypno/kernel/safety.py:classify` سطح RED (crisis/
coerce) را *قبل* از مغز رد می‌کند (`run.py:76-77`). آن گیت مطلق بماند.

### 🔴 B-۵ · دو ارائه‌دهنده/بیس‌URL متفاوت

- OFN: `https://api.sakana.ai/v1`، مدل‌های `fugu` + `fugu-ultra`.
- Hypno: `https://api.openai.com/v1`، مدل `fugu`.

اگر مغز واقعاً مشترک شود، باید **همان ارائه‌دهنده، همان کلید، همان base URL**
باشد.

**اقدام:** در `fugu_core/brain/` یک `RemoteBrain` واحد بساز. متغیر محیطی
مشترک: `FUGU_API_KEY`، `FUGU_BASE_URL`، `FUGU_MODEL_FAST=fugu`،
`FUGU_MODEL_DEEP=fugu-ultra`. کدام ارائه‌دهنده برنده است؟ **در این مگاپرامپت
تصمیم نگیر — از مالک بپرس** (نقطهٔ باز O-۵ زیر).

### 🟠 B-۶ · auth: hypno پنجرهٔ replay ۲۴ ساعته دارد و session secret ندارد

`hypno/adapters/telegram.py:31` با `max_age=86400` (۲۴ ساعت) اعتبارسنجی می‌کند.
OFN `DEFAULT_MAX_AGE_S = 600` است (`auth.py:42`). یعنی یک blob initData در hypno
۲۴ ساعت قابل replay است. علاوه بر این، hypno `session_secret` ندارد
(`config.py:8-18`) و `ReplayGuard` ندارد.

**اقدام:** `fugu_core/auth/` را بساز که شامل `verify_init_data` (با max_age=۶۰۰
پیش‌فرض)، `issue_session`/`verify_session` (با `session_secret`)، و `ReplayGuard`
باشد. به hypno یک `FUGU_SESSION_SECRET` بده. تفاوت: OFN توکن را با
`tenant.user_id` امضا می‌کند؛ hypno تک‌تنانت است، پس از tenant ساختگی `hypno`
استفاده کن.

### 🟠 B-۷ · مکان کد مشترک — نه در ofn، نه در hypno، یک پکیج سوم

OFN به `TenantScope`/`PackSpec` سخت‌کوپل است (`kernel/tenancy.py`). Import کردن
`ofn.kernel.*` در hypno، تمام ماشین تنانت را می‌کشد. تصادم نام هم هست: هر دو
`Config`، `Brain`، `Decision`، `App` دارند با معانی متفاوت.

**اقدام:** پکیج جدید `~/shared/fugu_core/` بساز. فقط primitive‌های واقعاً
مشترک: auth، brain، scrub، memory، rag. **هرگز `TenantScope` را وارد نکن** — آن
در OFN می‌ماند و hypno یک wrapper تک‌تنانت می‌سازد. یک `pyproject.toml` به
`~/shared/` بده و با `pip install -e` در هر دو سرویس نصبش کن (یک برد، پس
editable کافی است).

### 🟠 B-۸ · worker/async: hypno نیازی به worker کامل ندارد، اما الگوی sync+gated را نیاز دارد

قاعدهٔ سخت OFN: HTTP نباید router را import کند (`http_api.py:5`، با تست
`test_http_api.py:82`). hypno این را در `run.py:83` نقض می‌کند. **ولی** OFN خودش
یک مسیر sync دارد (`node.py:1424 router.ask` پشت `CallBudget.allows`) برای
owner.

**اقدام:** hypno worker کامل نمی‌خواهد. سه چیز می‌خواهد: (۱) `RemoteBrain` دو
آرگومانی را بپذیرد (prompt از بیرون ساخته شود، نه داخل مغز)؛ (۲) هر فراخوانی
پشت `CallBudget.allows` + `NodeQuota.check` باشد (الگوی اثبات‌شدهٔ
`node.py:1410-1427`)؛ (۳) `interactive=True` و `max_rung=Rung.REMOTE`. worker فقط
برای کارهای غیرواقع‌بازرسی (تجمیع شبانهٔ حافظه) محفوظ بماند.

### 🟡 B-۹ · بک‌آپ: hypno در حال حاضر بک‌آپ ندارد

`ofn/backup_job.py:21` از `cfg.db_paths` می‌خواند. `hypno.sqlite` در این لیست
نیست. اگر `memory.sqlite` بحرانی شود، باید بک‌آپ گرفته شود.

**اقدام:** `memory.sqlite` را به `Config.db_paths` در OFN اضافه کن تا
`ofn-backup.timer` آن را پوشش دهد (تمیزترین). pruning، integrity check و
verification رایگان می‌آیند.

### 🟡 B-۱۰ · سال ۲۰۲۶: یک ثابت بوت تاریخی هست

`ofn/adapters/boot.py:68`: `MIN_PLAUSIBLE_EPOCH = 1_767_225_600  # 2026-01-01`.
این یک گیت یکپارچگی بوت است — هر چیزی قبل از ۲۰۲۶-۰۱-۰۱ «قطعا غلط» است.
**باید سالانه bump شود** یا نسبی شود.

**اقلام دیگر:** `marketing_run.py:22,36` هفتهٔ ISO `2026-W33` در docstring
(زیبایی‌شناختی). `trend_sources.py:21,92` کامنت «gated as of 2026». هیچ
`datetime.now().year == 2026` در منطق نیست.

**اقدام:** `MIN_PLAUSTIBLE_EPOCH` را به کفِ سال جاری تبدیل کن:
`int(time.mktime(time.strptime(f"{time.gmtime().tm_year}-01-01", "%Y-%m-%d")))`.
هیچ ثابت ۲۰۲۶ جدیدی در کد ادغام‌شده اضافه نکن.

### 🟡 B-۱۱ · tenancy: hypno یک pack синтتیک می‌خواهد

هر store OFN یک `TenantScope` می‌گیرد و `scope.key(...)` می‌زند. برای استفادهٔ
ledger/quote در hypno، باید یک `TenantScope` بسازی، که یک `TenantId` می‌خواهد،
که یک `PackSpec` با `quota_share` می‌خواهد.

**اقدام:** یک `packs/hypno.yaml` بساز: `tenant: hypno`، `quota_share: ۰.۱۰`،
`required_facts: []`، `gates: [safety]`. این به hypno اجازه می‌دهد در
`TenantRegistry` ثبت شود و scope بگیرد. **هرگز `TenantScope` را از stores
نکن** — ضمانت ایزولاسیون OFN را می‌شکند ([[DECISIONS|D-21]]).

### 🟡 B-۱۲ · OFN از قبل یک دستیار دارد — نام‌گذاری تصادم

`StudioAssistantStore` (`studio_assistant.py:29`) دستیار RAG مولتی‌تنانت سبا
است با ۹ turn و ۲۶ chunk واقعی. معماری‌اش متفاوت است: محلی در زمان چت، مغز
ریموت فقط شبانه. hypno مغز ریموت در هر چت می‌زند.

**اقدام:** در این مگاپرامپت تصمیم بگیر (نه باز بگذار): **hypno tenant
جدید** در `memory.sqlite` می‌شود، نه tenant چهارم `assistant.sqlite`. دو
معماری متفاوت‌اند؛ ادغام datastore آن‌ها ریسک دارد. لایهٔ corpus مشترک می‌تواند
از هر دو تغذیه شود، ولی turnها/factها tenant-scoped می‌مانند.

---

## ۴) نقاط باز — از مالک (آری) قبل از اجرا بپرس

| شناسه | پرسش | چرا مهم است |
|---|---|---|
| **O-۵** | کدام ارائه‌دهندهٔ مغز ریموت؟ Sakana یا OpenAI-compatible؟ (هر دو فعلا کار می‌کنند ولی کلید/URL متفاوت) | کل کد مغز مشترک به این وابسته است |
| **O-۶** | آیا hypno باید به‌جای سرویس جدا، tenant چهارم OFN شود (یک پروسه)؟ یا سرویس جدا با پکیج مشترک بماند؟ | این مگاپرامپت «سرویس جدا + پکیج مشترک» را فرض می‌کند، ولی مالک باید تأیید کند |
| **O-۷** | سهم کوئتا: `ziman=۰.۳۶ lead=۰.۳۶ studio=۰.۱۸ hypno=۰.۱۰` پذیرفته است؟ | مجموع باید ≤۱.۰؛ هر تغییر روی بقیه اثر دارد |
| **O-۸** | افشای روایت شخصی به ارائه‌دهندهٔ مغز پذیرفته است (با امتناع scrub فارسی)؟ | بدون این، مغز ریموت hypno کار نمی‌کند |

---

## ۵) فازبندی اجرا — هر فاز مستقل و قابل‌واگرد است

### فاز ۰ · بک‌آپ و آماده‌سازی (بدون تغییر کد)
- [ ] `wal_checkpoint(TRUNCATE)` روی هر دو DB.
- [ ] بک‌آپ کامل `~/.local/share/ofn/` و `~/.local/share/hypno-fugu-mini/`.
- [ ] `git init` در `/home/ari/hypno-fugu-mini` (الان git-track نیست — BS-12h).
- [ ] تأیید اعداد §۱ با کوئری زنده.
- [ ] از مالک O-۵ تا O-۸ را بپرس.

### فاز ۱ · پکیج مشترک `fugu_core`
- [ ] `~/shared/fugu_core/` با `pyproject.toml`.
- [ ] `fugu_core/auth/` — `verify_init_data` (max_age=۶۰۰)، `issue_session`/
      `verify_session`، `ReplayGuard`. استخراج از `ofn/kernel/auth.py` **بدون**
      `TenantScope`.
- [ ] `fugu_core/brain/` — `RemoteBrain` دو آرگومانی (task, prompt)→`BrainReply`.
      استخراج از `ofn/adapters/remote_brain.py`.
- [ ] `fugu_core/scrub/` — کپی `ofn/kernel/scrub.py`.
- [ ] `fugu_core/rag/` — FTS5 chunker + retrieve. استخراج از
      `hypno/adapters/rag.py` + `store.py` search.
- [ ] `pip install -e ~/shared` در محیط هر دو سرویس.
- [ ] تست: هر تابع استخراج‌شده رفتار قدیمی را حفظ کند (red-green).

### فاز ۲ · حافظهٔ سه‌لایه `memory.sqlite`
- [ ] اسکیمای §۲ (memory_turns، memory_facts، memory_corpus + memory_fts).
- [ ] مهاجرت از hypno: `research_docs`→`memory_corpus`(tenant=hypno)؛
      `messages`→`memory_turns`؛ `memories`→`memory_facts`.
- [ ] مهاجرت از OFN: `assistant_chunks`→`memory_corpus`(tenant=studio)؛
      `assistant_chat_turns`→`memory_turns`. **`assistant.sqlite` دست‌نخورده
      بماند** — کپی کن.
- [ ] یک تابع `recall(tenant, user, query)` که هر سه لایه را می‌خواند.
- [ ] تست: یک فکت در hypno، یک turn در studio، یک chunk در corpus — `recall`
      هر سه را برای tenant درست برمی‌گرداند و برای tenant غلط نشت نمی‌کند.

### فاز ۳ · ارتقای hypno
- [ ] `packs/hypno.yaml` (BS-11).
- [ ] `Config` hypno را بازنویسی تا `fugu_core` را compose کند.
- [ ] auth: `fugu_core.auth` + `FUGU_SESSION_SECRET`.
- [ ] مغز: `Brain` دو آرگومانی از `fugu_core.brain`؛ prompt-build بیرون؛ scrub
      قبل از remote؛ گیت `CallBudget` + quota.
- [ ] consent: `consent`→`safety_acknowledged` (BS-3).
- [ ] `panel_note`: از write pathها بردار (BS-2).
- [ ] مغز sync + gated (BS-8).
- [ ] بک‌آپ: `memory.sqlite` به `Config.db_paths` (BS-9).
- [ ] ۶ تست جدید (BS-10): auth freshness، quota، scrub-before-remote،
      concurrent-store، schema-migration، **consent-gate-before-brain**
      (مهم‌ترین: `chat` هرگز به `brain.answer` نمی‌رسد وقتی `classify().allow
      is False`).

### فاز ۴ · اتصال OFN به حافظهٔ مشترک
- [ ] `StudioAssistantStore.answer_local` بتواند از `memory_corpus` هم بخواند.
- [ ] `assistant_update.py` به‌جای/علاوه بر `assistant_chunks` در `memory_corpus`
      (tenant=studio) بنویسد.
- [ ] تست: رفتار پنل سبا تغییر نکرده (`/sabaapp` همچنان ۲۰۰).

### فاز ۵ · نقاط کور لید نقاشی (همزمان با فوکوس کاربر)
[[HANDOFF]] بخش «لید نقاشی» را ببین. این‌ها مستقل از ادغام‌اند ولی در همان
پنجره انجام شوند:
- [ ] B-۱ لید: `lead_priority()` مرده را در `create_lead`/`update_lead` وصل کن
      (یا حذفش کن). [[DECISIONS|D-23]].
- [ ] B-۳ لید: UI/API پارتنر لیست/جستجو/تغییر وضعیت بگیرد.
- [ ] B-۲ لید (بعد از راز): outbox لید ساخته شود. [[DECISIONS|D-24]].

### فاز ۶ · تأیید نهایی
- [ ] `python3 -m pytest` در OFN — باید همچنان سبز باشد (هیچ تستی نشکند).
- [ ] `python3 -m pytest` در hypno — باید رشد کرده باشد (۶+ تست جدید).
- [ ] `python3 -m pytest` در `~/shared/` — تست‌های fugu_core.
- [ ] `sudo systemctl restart ofn.service hypno-fugu-mini.service`.
- [ ] smoke: `curl http://127.0.0.1:8793/sabaapp` و `curl http://127.0.0.1:8895/health`.
- [ ] یک مکالمهٔ واقعی در hypno — مغز پاسخ می‌دهد و حافظه ثبت می‌شود.
- [ ] به‌روزرسانی [[HANDOFF]]، [[INDEX]]، [[DECISIONS]]، این مگاپرامپت.

---

## ۶) ممنوعیت‌ها

- ❌ `assistant.sqlite` یا `hypno.sqlite` موجود را بازنویسی نکن — کپی کن.
- ❌ WAL را بدون checkpoint کپی نکن.
- ❌ `TenantScope` را از stores OFN نکن — ایزولاسیون را می‌شکند.
- ❌ `consent` OFN را روی hypno اعمال نکن — مفاهیم متفاوت‌اند.
- ❌ بگو «scrub فارسی را حل می‌کند» — نمی‌کند. صراحتاً افشا را بنویس.
- ❌ `panel_note` را در write path نگه دار.
- ❌ سهم کوئتا را بدون `assert sum ≤ 1.0` تغییر بده.
- ❌ hypno را به `REMOTE_DEEP` ببر — UX دقیقه‌ای سفید.
- ❌ هیچ ثابت ۲۰۲۶ جدیدی اضافه نکن.
- ❌ `innerHTML` با دادهٔ کاربر/API. کلمهٔ RAG در UI ([[DECISIONS|D-22]]).

---

## ۷) گزارش نهایی که باید بدهی

وقتی همه چیز تست و verify شد، گزارش فارسی بده که دقیقاً این‌ها را بگو:

۱. کدام فایل‌های جدید ساخته شدند (`~/shared/fugu_core/*`، `memory.sqlite`،
   `packs/hypno.yaml`).
۲. کدام فایل‌های موجود تغییر کردند (با خط شماره).
۳. حافظهٔ سه‌لایه ساخته شد یا نه — هر لایه، تعداد ردیف migrant، tenantها.
۴. مغز مشترک ساخته شد یا نه — همان ارائه‌دهنده/کلید؟ (O-۵).
۵. auth مشترک ساخته شد یا نه — max_age، ReplayGuard، session_secret.
۶. consent دو مفهوم جدا ماند یا نه — `safety_acknowledged`.
۷. `panel_note` از write pathها رفت یا نه.
۸. scrub با افشای صریح اعمال شد یا نه.
۹. کوئتا دوباره زده شد یا نه — اعداد، `assert sum ≤ ۱.۰`.
۱۰. بک‌آپ `memory.sqlite` وصل شد یا نه.
۱۱. سال ۲۰۲۶相对 شد یا نه (`MIN_PLAUSTIBLE_EPOCH`).
۱۲. هیچ دیتایی از دست رفت یا نه — جدول قبل/بعد تعداد ردیف.
۱۳. هیچ سرویسی شکست یا نه — `is-active` هر دو.
۱۴. تست‌ها: OFN، hypno، fugu_core — تعداد سبز.
۱۵. نقاط کور لید نقاشی (فاز ۵) — کدام انجام شد.
۱۶. نقاط باز باقی‌مانده (O-۵ تا O-۸ اگر مالک جواب نداده).
۱۷. مسیرهای زنده: `/sabaapp`، `/health` hypno، پورت‌ها.
۱۸. مسیرهای کد: `~/shared/fugu_core/`، `memory.sqlite`.

**گزارش نباید ادعا کند کاری انجام شده مگر واقعاً تست و verify شده باشد.**
هر ادعا یک رکورد مستقل (CLAUDE §۸-ب).
