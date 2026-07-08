---
type: design
status: implemented (Phase 2, 2026-07-08)
version: v1
tags: [scripts, doctor, architecture, stale-view]
created: 2026-07-05
updated: 2026-07-08
related: "[[EXPERIENCE-LEDGER]] · [[LIVING-BRAIN-BLUEPRINT]] · [[HANDOFF]] · [[AGENT_REGISTRY]]"
implemented_in: "_ops/doctor/doctor.py (stable_read + Doctor class) · _ops/tests/test_doctor.py (27 tests)"
---

# بلوپرینت «دکتر مغز» v1 — نقشهٔ معماری + حل ریشه‌ای stale-view

> **دامنه:** فقط طراحی. این سند **کد را تغییر نمی‌دهد**؛ خروجی جلسهٔ ۵ ژوئیه = بلوپرینت اول، اجرا در گام بعد با verdict آری.
> **هدف (verdict آری، همین جلسه):** (۱) نقشه و مستند معماری دکتر · (۲) حل ریشه‌ای کلاس stale-view.
> **قید حاکم:** دکتر = صفر نوشتن، صفر LLM، propose-only در اجرای زمان‌بندی؛ اعمال فقط تعاملی با verdict. هر تعدیل گزارش = `ledger_ref`.

---

## ۱. خلاصهٔ سریع

دکتر مغز (`04 - Architect System/scripts/dashboard_doctor.py`، ۱۷۸ خط) موتور عیب‌یاب **قطعی** سلامت vault است: چک می‌کند، نمره می‌دهد، JSON می‌ریزد؛ تابلوی تمرکز و داشبورد و حلقهٔ خودبهبودی از خروجی‌اش تغذیه می‌شوند. یک نقصِ ریشه‌ای دارد: چون از **mount نوع FUSE** می‌خواند، بعد از ویرایش out-of-band سمت ویندوز گاهی **نمای کهنه** می‌بیند (tail بریده، size منجمد) و آن را به‌اشتباه `utf8-corrupt`/`index-drift` گزارش می‌کند. مهارِ فعلی (`VERIFY_RULES`: «این چک‌ها همیشه مشکوک‌اند») یک heuristic درشت است که هم دستی/انسانی است هم شکننده — یک‌بار خرابی واقعی را «تمیز» علامت زد (ledger row-47).

این بلوپرینت پیشنهاد می‌کند مهارِ درشت با یک **دروازهٔ خواندنِ پایدار (stable-read gate)** جایگزین شود که در نقطهٔ دسترسی به فایل، stale-view را **قطعی و اندازه‌گیری‌شده** از خرابی واقعی جدا می‌کند.

## ۲. تحلیل

**مسئله.** stale-view یک FP سیستماتیک است که نمرهٔ خام را می‌کوبد و به توجه انسانی نیاز پیدا می‌کند، درحالی‌که ریشه‌اش کش فایل‌سیستم است نه محتوا.

**ریشهٔ فنی (اثبات‌شده این جلسه).** mount vault از نوع `fuse` است (`findmnt`: `fuse … default_permissions,allow_other`). FUSE صفاتِ فایل (size/mtime) و صفحاتِ داده را با timeout کش می‌کند. وقتی ایجنت فایلی را **out-of-band سمت ویندوز** ویرایش می‌کند، تا انقضای کش یا remount، لایهٔ FUSE می‌تواند snapshot کهنه بدهد: دادهٔ بریده (page-cache صفحات قدیمی)، size/mtime منجمد (attr-cache). چک‌های بایتی (`utf8-corrupt`) و چک‌های مشتق‌از‌محتوا (`index-drift` که محتوای `INDEX.md` را grep می‌کند) روی این phantom شلیک می‌کنند.

**شاهدهای زندهٔ ledger:**

- row-27 — کلاس stale-view: بعد از ویرایش ویندوزی، اول index-drift بعد utf8-corrupt (دُم‌بریده، mtime منجمد).
- row-37 — همین روی **خودِ اسکریپتِ** تازه‌ویرایش‌شده هم زد (size منجمد ۶۴۸۷، اجرا شکست) → قاعده: فایلِ همین‌جا-ویندوز-ویرایش‌شده را از همان mount اجرا/verify نکن.
- row-38 — ۶ لینک `index-drift` کریپتو سمت ویندوز حاضر بودند ولی grep سندباکس ۰ داد → mount کهنه، نه drift واقعی.
- row-40 — **کلیدی:** raw دکتر ۲۳→۶۶ فقط با remount؛ «stale-viewها خودترمیم شدند چون سرکوب دائمی نشده بودند» → **stale-view گذراست؛ خرابی واقعی پایدار است.**
- row-47 — annotation «verify ویندوزی: تمیز» **نادرست** بود؛ خواندن ویندوزی بعدی نویسهٔ جایگزین (U+FFFD) نشان داد → خرابی واقعی پابرجا. درس: verify باید صریحاً دنبال U+FFFD/متن بریده بگردد، نه فقط «باز شدن موفق».
- row-36 — heuristic بایتی (offset دُم‌بریده vs وسط‌فایل) رد شد چون خرابی می‌تواند وسط‌فایل باشد → verify-at-source جایگزین شد.
- row-46 — ساعت سندباکس ~UTC است ولی برچسب AEST می‌زند (تأیید این جلسه: `date -u` داد `01:58Z`) → `generated` دکتر که از `date.today()` می‌آید نزدیک نیمه‌شب می‌تواند یک‌روز پرت باشد.

**قیدها.** بدون root در سندباکس؛ دکتر باید خودبسنده و قطعی بماند (صفر LLM)؛ اوراکل نهاییِ محتوا = سمت ویندوز؛ تغییر خروجی روی سه مصرف‌کننده اثر می‌گذارد → سازگاری عقب‌رو لازم است.

**فرض‌های صریح.**
- F1: `posix_fadvise(POSIX_FADV_DONTNEED)`، `O_DIRECT`، fresh-fd همه در پایتونِ سندباکس موجودند (تأییدشده این جلسه).
- F2: FUSE با re-open و انقضای attr-timeout کش را می‌بازد (سازگار با خودترمیمیِ row-40) — **باید در فاز اجرا تجربی سنجیده شود** (page-cache DONTNEED الزاماً attr-cache را باطل نمی‌کند).
- F3: خرابی واقعی روی چند خواندنِ fresh **پایدار** می‌ماند؛ stale-view نمی‌ماند.

**ریسک‌ها.** R1: اگر re-open کش را نبازد، probe همیشه «unstable» بدهد → همه‌چیز stale علامت بخورد و خرابی واقعی پنهان شود (کاهش: سقف retry + fallback به needs_source_verify، نه سرکوب). R2: نویز نمره اگر آستانهٔ پایداری بد کالیبره شود. R3: کندی I/O از خواندن چندباره (کاهش: probe فقط روی فایل‌های **پرچم‌خورده**، نه کل walk).

## ۳. معماری فعلی دکتر (نقشه)

```
                    ┌───────────────────────────────────────────┐
  ورودی‌ها          │  vault *.md  (os.walk، SKIP_DIRS/-venv)     │
                    │  01 - Dashboard/SYSTEM-DASHBOARD.html       │
                    └───────────────┬───────────────────────────┘
                                    │   ← mount FUSE (اوراکلِ محتوا = ویندوز)
                    ┌───────────────▼───────────────────────────┐
  هستهٔ قطعی        │  چک‌ها → findings[]:                        │
  (صفر LLM/نوشتن)   │   kit-missing · index-drift · utf8-corrupt  │
                    │   stale-project · bad-date · kit-unbound    │
                    │   dup-basename · html-{no-hash,secret,      │
                    │   dead-target,missing} · html-secret        │
                    └───────────────┬───────────────────────────┘
                    ┌───────────────▼───────────────────────────┐
  لایهٔ گزارش       │  SUPPRESS_RULES (by-design + ledger_ref)    │
  (Option B)        │  VERIFY_RULES (utf8/index → needs_verify)   │
                    │  raw_score · effective_score · counts       │
                    │  → JSON روی stdout · exit(0/1 @ effective≥70)│
                    └───────────────┬───────────────────────────┘
        ┌───────────────────────────┼────────────────────────────┐
        ▼                           ▼                            ▼
  brain-focus-board(3h)     system-dashboard(6h)          حلقهٔ خودبهبودی
  تک‌منبع سرکوب v10         (تابلوی HTML)                  findings → پیشنهاد → verdict
        └───────────────► [[EXPERIENCE-LEDGER]] (هر قاعدهٔ سرکوب/verify یک ledger_ref) ◄──┘

  حاکمیت: صفر نوشتن · صفر LLM · propose-only(زمان‌بندی) · اعمال(تعاملی+verdict) · هر تعدیل = ledger_ref
```

**اجزای فعلی و مسئولیت:**

| لایه | مسئولیت | فایل/محل |
|---|---|---|
| ورودی | پیمایش md با `SKIP_DIRS`؛ خواندن داشبورد HTML | `dashboard_doctor.py` §walk |
| هستهٔ چک | ۱۱ چک قطعی → `findings[]` با severity | همان، بدنهٔ اصلی |
| نمره‌دهی | `raw_score` (همه) / `effective_score` (پس از suppress + وزن verify) | `_score`, `sev_w` |
| گزارش | JSON: raw/effective/counts/suppressed/needs_source_verify/findings | خروجی stdout |
| مصرف | تابلوی تمرکز، داشبورد سیستم، ledger، حلقهٔ بهبود | تسک‌های [[AGENT_REGISTRY]] |

**نقصِ معماری فعلی:** لایهٔ `VERIFY_RULES` یک تصمیم **کلاس-محور** است («هر utf8-corrupt و index-drift مشکوک است») نه **نمونه-محور**. یعنی نمی‌تواند stale-view را از خرابی واقعی تفکیک کند و کار را به یک قدمِ «verify ویندوزی» دستی/انسانی حواله می‌دهد که row-47 نشان داد خطاپذیر است.

## ۴. راه‌حل ریشه‌ای — دروازهٔ خواندنِ پایدار (stable-read gate)

**ایده:** stale-view را در **نقطهٔ خواندن** و به‌صورت **قطعیِ اندازه‌گیری‌شده** تشخیص بده، نه بعداً با heuristic کلاس‌محور. یک تابع `stable_read(path)` جای هر `open(...).read()` در دکتر می‌نشیند و برای هر فایل تعیین می‌کند نمای mount «settled» است یا نه.

```python
# طرح (شبه‌کد؛ پیاده‌سازی در فاز اجرا با verdict)
def stable_read(path, retries=3, backoff=0.25):
    """(text, verdict) — verdict ∈ {stable, stale, corrupt}."""
    prev = None
    for i in range(retries):
        st = os.stat(path)                       # attr تازه (fresh lookup)
        fd = os.open(path, os.O_RDONLY)          # fd تازه → lookup تازهٔ FUSE
        raw = os.read_all(fd)
        os.posix_fadvise(fd, 0, 0, os.POSIX_FADV_DONTNEED)  # صفحات را بینداز
        os.close(fd)
        short = len(raw) != st.st_size           # short-read = نمای ناسازگار
        changed = prev is not None and raw != prev
        prev = raw
        if short or changed:                     # هنوز در حال settle
            time.sleep(backoff * (i + 1)); continue
        # نمای پایدار است → حالا دربارهٔ محتوا قضاوت کن
        try:
            return raw.decode("utf-8"), "stable"
        except UnicodeDecodeError:
            return None, "corrupt"               # پایدار و خراب = واقعی (CRITICAL)
    return None, "stale"                          # پایدار نشد = محیطی (self-heal)
```

**قاعدهٔ طبقه‌بندی (جایگزین `VERIFY_RULES`):**

| نتیجه probe | کلاس | وزن نمره | گیت | مصرف |
|---|---|---|---|---|
| `stable` | عادی | طبق severity | — | چک عادی اجرا می‌شود |
| `corrupt` (پایدار و decode-fail یا U+FFFD) | **خرابی واقعی** | CRITICAL کامل | بله | اقدام مالک (Obsidian re-save) |
| `stale` (پایدار نشد) | **محیطی** | ۰ (auto) | خیر | خودترمیم انتظار می‌رود (row-40) |

**چه چیزی درست می‌شود:**

1. تفکیک **نمونه-محور و قطعی**: هر فایل جدا سنجیده می‌شود، نه یک برچسبِ کلاسیِ درشت.
2. **row-47 بسته می‌شود**: خرابیِ پایدار دیگر «تمیز» علامت نمی‌خورد — چون `corrupt` فقط وقتی صادر می‌شود که نما **settled** باشد و باز هم decode بشکند.
3. **حذف toilِ انسانی**: قدمِ «verify ویندوزی» دستی در حالت عادی لازم نیست؛ probe خودش قطعی است.
4. **ساده‌سازی نمره‌دهی**: لایهٔ `VERIFY_RULES` جمع می‌شود در دروازهٔ خواندن. می‌ماند `raw` (همهٔ findings) و `effective` (پس از `SUPPRESS_RULES` by-design). `stale-view` صرفاً یک finding محیطیِ وزن-صفرِ خودتوضیح است.
5. **کارایی**: probe فقط روی فایل‌هایی که چک بایتی/محتوایی پرچم زد اجرا می‌شود، نه کل ۴۰۰+ نوت.

**کمربندِ دوم (residual) — اجباری برای چک بایتی، نه اختیاری:** یک قلابِ confirm ویندوزی با **شاهد ساختاریافته** (byte-offset، U+FFFD حاضر؟، read_len vs stat_size). هر verdictِ `corrupt` **قبل از** صعود به CRITICAL باید سمت ویندوز تأیید شود. این همان پیشنهاد L1 در row-47 است: «مسیر ثبت نتیجهٔ verify در خودِ دکتر».

> **⚠️ یافتهٔ زندهٔ راستی‌آزمایی (۲۰۲۶-۰۷-۰۵، حین همین کار):** `stable_read` **لازم است ولی کافی نیست**. هنگام نوشتنِ پرامپت اهداف، mount یک **snapshotِ کهنهٔ خودسازگار** داد: `read == stat == 16091` و روی ۵ خواندنِ fresh کاملاً پایدار، ولی محتوا وسطِ جمله بریده بود (فایلِ واقعیِ ویندوز ~۱۸KB و سالم). یعنی هم short-read و هم double-read **از کنارش رد شدند** و probe اشتباهاً «stable → corrupt واقعی» می‌داد = **FP بحرانی**. تنها اوراکلِ درست، خواندنِ سمت ویندوز بود. **نتیجه برای طراحی:** برای این کلاس، signalهای درون‌سندباکس (size منجمد در مقدارِ torn) گمراه‌کننده‌اند؛ پس (۱) کمربندِ ویندوزی برای هر verdictِ `corrupt` اجباری است، و (۲) دکتر باید size را با یک اوراکلِ مستقل (مثلاً stat سمت ویندوز یا انتظار تا settle پس از آخرین نوشتن) کراس‌چک کند، نه فقط خودسازگاریِ درون‌سندباکس. این row-36/row-47 را تجربی تأیید می‌کند: verify-at-source هستهٔ راه‌حل است، نه حاشیه.

**تعمیر جانبی (row-46):** `generated` را از `date.today()` سندباکس (UTC، برچسب‌غلط) نگیر؛ از host/زمان‌بند بگیر یا ادعای tz را حذف کن.

## ۵. ترید‌آف‌ها (امتیاز ۱–۱۰؛ بالاتر = بهتر/کم‌ریسک‌تر)

| گزینه | Cost | Complexity | Scalability | Maintainability | جمع‌بندی |
|---|---|---|---|---|---|
| **A. stable-read gate (پیشنهادی)** | ۸ (چند ده خط) | ۶ (probe منطق ظریف) | ۹ (فقط فایل پرچم‌خورده) | ۹ (یک نقطهٔ تصمیم، قطعی) | **توصیه‌شده — بالاترین ROI** |
| B. وضع فعلی (VERIFY_RULES کلاس‌محور) | ۹ | ۹ | ۷ | ۴ (کلاس‌محور، دستی، row-47) | نگه‌داری بالا، خطاپذیر |
| C. اجرای دکتر سمت ویندوز | ۴ (runner ویندوزی لازم) | ۵ | ۸ | ۶ | stale را کامل حذف می‌کند ولی وابستگی محیطی نو |
| D. two-phase agent-confirm همیشه | ۵ | ۴ (LLM در حلقه) | ۵ | ۵ | نه قطعی، به ایجنت وابسته |

**چرا A:** قطعیت را حفظ می‌کند (برخلاف D)، وابستگی محیطی نو نمی‌سازد (برخلاف C)، و نگه‌داری/دقت را نسبت به B جهش می‌دهد. تنها ریسکِ واقعی F2 است (آیا re-open کش FUSE را می‌بازد) که با یک تست تجربیِ ۱۰-دقیقه‌ای در فاز اجرا قطعی می‌شود.

## ۶. گام‌های بعد (اجرا — پس از verdict آری)

1. **تست feasibility (پیش‌نیاز، ۱۰ دقیقه):** فایلی را سمت ویندوز ویرایش کن، بلافاصله در سندباکس `stat` vs `read_len` و double-read را بسنج؛ تأیید کن که `stale` قابل‌تشخیص است و پس از انقضا `stable` می‌شود (اعتبارسنجی F2/F3). اگر re-open کش را نبازد → افزودن انتظارِ attr-timeout یا fallback.
2. **پیاده‌سازی `stable_read`** + جایگزینی نقاط خواندنِ دکتر؛ افزودن کلاس finding `stale-view` (وزن ۰).
3. **حذف `VERIFY_RULES`**، نگه‌داشتن `SUPPRESS_RULES` (by-design). به‌روزرسانی `README.md` اسکریپت‌ها.
4. **تست واحد** برای `stable_read` (سه سناریو: stable/stale/corrupt با fixture).
5. **اجرای زندهٔ هر دو validator** (`validate_frontmatter.py` + `find_broken_links.py`) و مقایسهٔ raw/effective قبل/بعد.
6. **ثبت در [[EXPERIENCE-LEDGER]]** (kind=tune، با ledger_ref) و به‌روزرسانی [[HANDOFF]].

> تصمیمِ باز برای آری: (الف) آیا کمربندِ دومِ §۴ (confirm ویندوزی residual) را می‌خواهی یا فقط دروازهٔ درون‌سندباکس کافی است؟ (ب) بعد از این، سراغ «گسترش پوشش چک‌ها» (لینک cross-project / گیت rotation) برویم یا «بازطراحی ماژولار کد»؟
