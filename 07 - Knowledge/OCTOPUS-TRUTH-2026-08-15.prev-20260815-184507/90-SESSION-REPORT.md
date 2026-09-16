# گزارش نشست — رصدخانهٔ اینترنت فقط‌خواندنی

**تاریخ:** ۱۵ اوت ۲۰۲۶ · **مالک:** آرمین · **شاخه:** `claude/second-brain-governor-v02-2a6e36`
**Commit های این نشست:** `dc5839d` (فاز اول) · `d964f5f` (gitignore)

---

## ۱. یک‌جمله‌ای

از «برنامه روی کاغذ» به «کد اجراشده روی ماشین مالک با دادهٔ واقعی و ۹۳ تست سبز»
رسیدیم — و در همین مسیر چهار جای مهم یاد گرفتیم که **ادعای پیشین غلط بود**.

---

## ۲. آنچه ساخته و اجرا شد

| مؤلفه | فایل | حجم | وضعیت |
|---|---|---|---|
| تک‌درگاه خروج | `_ops/observatory/impl/gateway.py` | ۱۹٬۴۴۹ B | ✅ روی لپ‌تاپ |
| ارزیاب RFC 9309 | `impl/robots.py` | ۸٬۶۳۶ B | ✅ |
| زنجیرهٔ hash | `impl/audit.py` | ۲٬۲۲۹ B | ✅ |
| انبار شاهد + بودجه + rate limit | `impl/evidence_store.py` | ۱۴٬۴۴۴ B | ✅ |
| راستی‌آزمای مستقل انبار زنده | `scripts/verify_live_store.py` | ۱۹٬۱۴۵ B | آمادهٔ اجرا |

### تست‌ها — اجرای واقعی روی ماشین مالک

```
python -m pytest _ops\observatory\tests\ -q
93 passed in 1.57s
```

| مجموعه | تعداد | چه چیزی را می‌گیرد |
|---|---|---|
| `test_gateway.py` | ۳۰ | ۱۱ تست منفی اجباری، ۱۰ دروازه، معناشناسی RFC 9309 |
| `test_structural.py` | ۷ | invariant S1 — فقط `gateway.py` مجاز است شبکه import کند |
| `test_evidence_store.py` | ۲۵ | تعیّن replay، dedup، تشخیص دست‌کاری، بودجهٔ پایدار، rate limit |
| `red_team/test_red_team.py` | ۳۱ | ۲۰ الگوی تزریق پرامپت + boundary + poisoning + فرار از بودجه + kill switch |

### تست جهش‌یافتگی (mutation testing)

هفت جهش عمدی در gateway کاشته شد و **هر هفت** توسط تست‌ها کشته شد:
حذف گیت متد، حذف گیت scheme، تبدیل تطبیق دقیق دامنه به تطبیق پسوندی، برداشتن
سقف حجم، خاموش‌کردن kill-switch، برداشتن سقف بودجه، رفتار با 5xx مثل 4xx.

روی راستی‌آزمای جدید هم شش جهش کاشته شد و **۶ از ۶** کشته شد:
دست‌کاری بایت بدنه، شکستن پیوند `prev_hash`، جعل `hash`، تزریق هدر `Set-Cookie`،
عبور از سقف بودجه، ایجاد شکاف در `seq`.

---

## ۳. چهار چیزی که فهمیدیم ادعای پیشین غلط بوده

این بخش مهم‌ترین بخش گزارش است. اصل خانه: **شواهد نه ادعا**.

### ۳-الف. معناشناسی RFC 9309 در نسخهٔ اول غلط بود

نسخهٔ اول ارزیاب robots همهٔ پاسخ‌های غیر ۲۰۰/۴۰۴ را «نامعلوم» می‌گرفت.
[RFC 9309 §2.3.1](https://www.rfc-editor.org/rfc/rfc9309.html) این‌طور نیست:

- **4xx** = «unavailable» → crawler **MAY** access all
- **5xx** = «unreachable» → crawler **MUST** assume complete disallow

این تصحیح دو نتیجهٔ عملی داشت: ردیف E (`data.api.abs.gov.au` که robots را با
۴۰۳ CloudFront برمی‌گرداند) **نجات یافت**، و BOM **رد شد**.

### ۳-ب. تعداد تست‌های OCTOPUS ۱۷۱ است نه ۲۰۷

ادعای ۲۰۷ تست در اسناد بود. اجرای واقعی روی `F:\backup` عدد **۱۷۱** داد.
`BACKUP-README` درست می‌گفت و اسناد دیگر غلط. علت: `app/NBB-CP` در commit
`ea69126` حذف شده بود. coherence واقعی `0.95` و beat `36563` است، نه
`0.958` و `36436`.

### ۳-پ. ADR-041 در vault مالک وجود نداشت

ترتیب ADR ها از ۰۴۰ به ۰۴۲ می‌پرید. سندی که فرض می‌کردیم موجود است، نبود.

### ۳-ت. انبار شاهد **دو بار** ساخته شده بود

این را در همین نشست کشف کردیم و نزدیک بود تکرار همان الگویی شود که سه نسخهٔ
موازی NBB-CP را ساخت.

---

## ۴. تصمیم معماری: دو انبار شاهد → یک حقیقت

بازرسی دیتابیس‌های زندهٔ روی لپ‌تاپ نشان داد runner انبار خودش را دارد:

**`evidence.db`** (۲۳۷٬۵۶۸ B) — سه جدول:

| جدول | ستون‌های کلیدی | ردیف |
|---|---|---|
| `evidence_chain` | `seq, evidence_id, url, method, occurred_at, recorded_at, status_code, response_headers, body_hash, body_size, body_bytes BLOB, prev_hash, hash` | ۱ |
| `domain_budget` | `domain, max_requests, spent_requests, epoch` | ۲ |
| `store_meta` | `key, value` | **۰** ← خالی |

**`predictions.db`** (۲۴٬۵۷۶ B) — `prediction_events(seq, event_type, prediction_id, payload, prev_hash, hash)`، ۱ ردیف.

### حکم: improve, don't rewrite

انبار SQLite بهتر از حد انتظار بود — خودش hash-chain دارد، بایت خام را BLOB
ذخیره می‌کند، و genesis-anchored است (`prev_hash` ردیف صفر = ۶۴ صفر). پس:

- **SQLite انبار عملیاتی می‌ماند.** یک لحظه هم متوقف نمی‌شود.
- انبار فایل‌محور من می‌شود **پیاده‌سازی مرجع** + مجموعهٔ تستی که SQLite باید از
  آن عبور کند.
- پل: `scripts/verify_live_store.py` — راستی‌آزمای **فقط‌خواندنی** که ۱۳ ضمانت
  را روی دادهٔ زنده می‌سنجد.

### یک نکتهٔ طراحی که عمداً این‌طور شد

فرمول hash انبار زنده را **نمی‌دانیم**. پس حدس نزدیم. راستی‌آزما ۱۵ فرمول
کاندید را امتحان می‌کند و می‌گوید کدام یکی hash ذخیره‌شده را بازتولید می‌کند.
اگر هیچ‌کدام نکرد، خود این یک یافتهٔ **CRITICAL** است: «زنجیره مستقل قابل تأیید
نیست.» این تفاوت بین «تست که پاس می‌شود» و «تست که چیزی را ثابت می‌کند» است.

راستی‌آزما هر دیتابیس را با `mode=ro` باز می‌کند. **هیچ چیز نمی‌نویسد.**

---

## ۵. اولین اجرای زندهٔ رصدخانه — و هشداری که باید بماند

| قلم | مقدار |
|---|---|
| منبع | `earthquake.usgs.gov/.../all_day.geojson` |
| حجم بدنه | ۲۰۲٬۸۹۳ بایت |
| رویداد | ۲۸۴ زمین‌لرزه، ۱۴ مورد با بزرگی ≥ ۵٫۰ |
| `body_hash` | `1049b925…c911112` |
| `prev_hash` | ۶۴ صفر (genesis) |
| شناسهٔ پیش‌بینی | `pred-20260815053527` |
| بودجه | `earthquake.usgs.gov 1/100` |

### هشدار ۱ — بی‌مزیتی پیش‌بینی

```
OCTOPUS      = 0.80
Persistence  = 0.80
```

این دو **یکی‌اند**. یعنی استراتژی پیش‌بینی فعلی هیچ اضافه‌ای روی baseline ندارد.

معیار موفقیت از پیش قطعی شده بود:

\[ \text{Brier}(\text{octopus}) < \text{Brier}(\text{persistence}),\quad p < 0.05,\quad n \geq 20 \]

اگر پس از رسیدن به \(n\) کافی همین بماند، این یک **شکست** است و با هشدار صریح
ثبت می‌شود — دقیقاً مثل «not superior to novelty» در ADR-037. توهم را زودتر
می‌کشیم بهتر است.

### هشدار ۲ — USGS در allowlist امضاشده نیست

allowlist v1 پنج دامنه دارد و `earthquake.usgs.gov` جزو آن‌ها نیست:

| ID | دامنه | مبنا |
|---|---|---|
| A | `www.rba.gov.au` | robots allow ([RBA robots.txt](https://www.rba.gov.au/robots.txt)) |
| B | `www.abs.gov.au` | robots allow |
| C | `blockchain.info` | مسیر `/q/` باز + ToS ([blockchain API](https://api.blockchain.info/)) |
| D | `api.frankfurter.dev` | بدون robots + ToS صریح ([frankfurter.dev](https://frankfurter.dev/)) |
| E | `data.api.abs.gov.au` | robots 403 = RFC 9309 §2.3.1.3 unavailable + [راهنمای ABS Data API](https://www.abs.gov.au/about/data-services/application-programming-interfaces-apis/data-api-user-guide) |

**رد شده با شاهد:** `www.bom.gov.au` (`Disallow: /fwo/` + دو گروه تکراری
`User-agent: *`) · `api.coingecko.com` (`Disallow: /api/v3`) · `nemweb.com.au`
(کل دامنه) · `www.aemo.com.au` (`/aemo/apps/api/report`).

تصمیم مالک: USGS پذیرش موقت با `needs_formal_allowlist: true`.

### هشدار ۳ و ۴ — دو ناسازگاری پیکربندی

- کد آستانه را `n ≥ 60` می‌گیرد، ولی سند `n ≥ 20` می‌گوید.
- تسک زمان‌بندی‌شده ۱۴ روز است، ولی پنجرهٔ مصوب بعد از حذف BOM به ۳۰ روز رسید.

هر دو هنوز **باز**اند.

---

## ۶. تصمیمات مالک که قفل شد

| شناسه | حکم | جزئیات |
|---|---|---|
| **NBB-V1** | **A** | NBB-CP حاکم بالای شش پا. حق `stop` یک پا، حق رد proposal، حق **پیشنهاد** بودجه ولی نه اجرا. تناقض با Architect: عملیاتی → NBB-CP، معماری → Architect |
| **ADR-037** | **A** | موتور فرضیه پذیرفته، adapter خاموش، `CORTEX_HYPOTHESIS=0`، `evidence_level: C` |
| **USGS** | پذیرش موقت | `needs_formal_allowlist: true` |
| **deceptive_grid.py** | بازگردانی | ویرایش commit‌نشده که ۳۶۴ خط و `falsified_assists_at` را حذف کرده بود |

ثبت‌شده در `PHASE-1-DECISIONS.md` و commit `dc5839d`.

---

## ۷. بهداشت مخزن

دو دیتابیس زنده و یک فایل موقت اشتباهاً وارد git شده بودند. در `d964f5f`
از ایندکس بیرون رفتند و به `.gitignore` اضافه شدند:

```
_ops/observatory/data/*.db
_ops/observatory/data/*.db-*
__pycache__/
.pytest_cache/
setup_files.py
```

دلیل: دیتابیس زنده با هر اجرای ساعتی رشد می‌کند و conflict می‌سازد. شاهد در
انبار می‌ماند، نه در git.

---

## ۸. درس‌های عملیاتی PowerShell

اینها با شکست واقعی یاد گرفته شدند، نه با حدس:

| چیز | نتیجه |
|---|---|
| heredoc `<<` | پشتیبانی نمی‌شود |
| `python -c "…"` طولانی | «command line is too long» |
| نام فایل فارسی | خرابی encoding |
| کوتیشن تودرتوی `\"` در `-c` | `SyntaxError: unterminated string literal` |
| اسکریپت بدون امضا | نیاز به `-ExecutionPolicy Bypass` |
| `sites.pplx.app` با `urllib` | HTTP 403 — نیاز به احراز مرورگر |
| صفحهٔ artifact پرپلکسیتی | کد در iframe تودرتو است؛ `document.body.innerText` پوستهٔ بیرونی را می‌گیرد نه کد را |

**الگوی کارآمد:** `@'…'@ | Set-Content -Path x.py -Encoding UTF8` سپس `python x.py`
یا برای فایل بزرگ: gzip + base64 + `[IO.File]::WriteAllBytes`.

**تلهٔ مسیر:** اولین بار `install_all_full.py` از `C:\Users\Armin` اجرا شد و ۱۰
فایل در جای غلط نشستند. اجرای نصب‌کننده باید **همیشه** از ریشهٔ مخزن باشد.

---

## ۹. وضعیت چک‌لیست ۲۰۰ آیتمی

| وضعیت | قبل | بعد |
|---|---|---|
| ✅ انجام شده | ۶۹ | **۷۷** |
| ⬜ باز | ۸۹ | ۸۵ |
| 🔒 مسدود | ۲۲ | ۲۱ |
| 🌑 نساخته شده | ۲۰ | ۱۷ |

آیتم‌هایی که بسته شدند: ۶ (NBB-V1)، ۱۶ (رأی ADR-037)، ۴۹ (انبار شاهد L2)،
۵۰ (تعیّن replay)، ۵۱ (بودجهٔ پایدار)، ۵۲ (rate limit per-domain)،
۱۴۱ (اسکلت pytest)، ۱۴۲ (red-team harness).

---

## ۱۰. کارِ باز — به ترتیب اولویت

| # | کار | چرا |
|---|---|---|
| ۱ | اجرای `verify_live_store.py` روی دیتابیس زنده | تا وقتی زنجیرهٔ زنده مستقل تأیید نشده، شاهد قابل قضاوت نیست |
| ۲ | ثبت رسمی USGS در allowlist با شاهد robots | الان خارج از فهرست امضاشده fetch می‌شود |
| ۳ | یکسان‌سازی آستانه: کد `n ≥ 60` ↔ سند `n ≥ 20` | عدد در سند جمله نیست، باید با کد بخورد |
| ۴ | پنجرهٔ تسک ۱۴ → ۳۰ روز | پنجرهٔ مصوب بعد از حذف BOM ۳۰ روز شد |
| ۵ | پر کردن `store_meta` با `schema_version` | جدول خالی است؛ مهاجرت آینده بی‌لنگر می‌شود |
| ۶ | جدا کردن استراتژی OCTOPUS از persistence | با تساوی ۰٫۸۰=۰٫۸۰ آزمون بی‌معناست |
| ۷ | نوشتن ADR-041 در vault مالک (`F:\backup`) | در ترتیب ۰۴۰→۰۴۲ گم است |
| ۸ | مرحلهٔ ۳: adapter و رویداد `observation.v1` | گام بعدی برنامهٔ ۹ مرحله‌ای |

### همچنان مسدود (نیاز به اقدام بیرونی)

`secret_rotation` · `partner_precondition` · `miner_isolation` · D1 (حسابرسی مستقل) · D7 (تولید) · `OWNER_KEY`

---

## ۱۱. مرزهایی که در تمام نشست نگه داشته شد

- هیچ flag ی از `OCTOPUS_WIRE_*` یا `OFN_WIRE_*` روشن نشد
- `OBSERVATORY=1` بدون تأیید فعال نشد
- هیچ رازی خوانده یا چاپ نشد
- هیچ فایلی حذف نشد — فقط بایگانی و `git rm --cached`
- راستی‌آزما با `mode=ro` باز می‌کند؛ نوشتن ساختاراً ناممکن است
- کلید کشتن دست‌نخورده: `echo KILL > _ops\observatory\data\kill.switch`

---

*همهٔ اعداد این گزارش از اجرای واقعی کد آمده‌اند، نه از سند. جایی که سند و کد
اختلاف داشتند، کد ثبت شد و اختلاف به‌عنوان یافته گزارش شد.*
