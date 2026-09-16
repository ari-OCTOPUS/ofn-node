# nbb-cp-kre — Knowledge Reality module

ماژولِ **read-only** برای NBB Control Plane. کاری که می‌کند:
vault را می‌خواند → گرافِ واقعیِ `[[wikilink]]` را می‌سازد → چند نمایشِ ریاضی را روی
**link prediction با یال‌های پنهان‌شده** به رقابت می‌گذارد → و لینک‌هایی که vault شما
گم کرده را رتبه‌بندی می‌کند.

> **`F:\backup` هرگز نوشته نمی‌شود.** این یک قول نیست، یک گاردِ کد است
> (`kernel/guard.py`) که با تست ثابت شده. هر تلاش برای نوشتن زیر ریشهٔ vault
> استثنا پرتاب می‌کند، حتی از مسیرِ `..`.

---

## نصب (یک‌بار)

```bat
cd /d F:\kre-out\nbb-cp-kre
python -m pip install -e .[ui,dev]
```

## اجرا

**مینی‌اپ (توصیه‌شده):** روی `run_dashboard.bat` دابل‌کلیک کن.

**خط فرمان:**

```bat
:: فقط اسکن — چند ثانیه
python -m nbb_cp_kre.cli scan --vault "F:\backup" --out "F:\kre-out"

:: نگاهِ سریع (فقط representationهای سریع)
python -m nbb_cp_kre.cli run --vault "F:\backup" --out "F:\kre-out" --quick

:: کاملِ کامل
python -m nbb_cp_kre.cli run --vault "F:\backup" --out "F:\kre-out" --seeds 5 --top-k 40
```

### زمانِ تقریبی (اندازه‌گیری‌شده روی ۲٬۵۰۰ نوت / ۶٬۷۰۰ لینک)

| حالت | زمان |
|------|------|
| `scan` | < ۱ ثانیه |
| `run --quick` | **۵۰ ثانیه** |
| `run` (کامل، شامل force layout و Isomap) | **۷ دقیقه** |

اگر vault بزرگ‌تر بود، `--quick` را اول بزن. representationهای کُند بالای سقفِ
گره **skip می‌شوند و دلیلش در گزارش نوشته می‌شود** — هیچ سقفِ خاموشی وجود ندارد.

---

## چه چیزی را درست می‌کند

اسکنِ متادیتای اختاپوس در `2026-07-31` سقفِ ۵۰٬۰۰۰ فایلی‌اش را **کاملاً داخل
`.claude` مصرف کرده بود**: ۴۹٬۹۳۹ فایل از `.claude` + ۶۱ فایل ریشه، و صفر فایل از
`00 - Inbox`, `07 - Knowledge`, `Obsidian Vault`, `OCTOPUS*`, `app` … . آن
«۱۶٬۱۶۲ فایل `.md`» نوت نبود؛ ۱۶٬۱۱۷ تای آن مارک‌داونِ پلاگین بود.

| مشکل | اصلاح در این ماژول |
|------|--------------------|
| `.claude` در excludes نبود | `DEFAULT_EXCLUDES` شامل `.claude`, `.zcode`, `.cursor`, `.kimi-*`, `.obsidian`, `_worktrees`, … |
| پیمایش عمق-اول ⇒ یک پوشه کل بودجه را می‌خورد | پیمایشِ **breadth-first**؛ اگر سقفی هم بخورد، نمونه در کل vault پخش است |
| سقف خاموش بود | `cap_hit` + هشدارِ صریح در گزارش و داشبورد |
| «تسلطِ یک پوشه» تشخیص داده نمی‌شد | اگر >۸۰٪ نوت‌ها در یک پوشه باشند، هشدار می‌دهد |

---

## معماری (مطابق قراردادِ nbb_cp)

```
src/nbb_cp_kre/
├── kernel/            stdlib خالص — بدون numpy/networkx/streamlit
│   ├── guard.py       ReadOnlyGuard  ← تنها مسیرِ نوشتن در کل پکیج
│   └── types.py       Note, LinkGraph, BakeoffReport, LinkProposal, QuarantinedText
├── adapters/          هر چیزی که با دنیا سروکار دارد
│   ├── vault/scanner.py      اینونتوریِ read-only
│   ├── vault/linkgraph.py    resolutionِ دقیقِ Obsidian
│   └── kre/{representations,bakeoff,missing_links}.py   numpy/scipy/networkx اینجا
├── app/pipeline.py    تنها choke-point اجرا
├── ui/streamlit_app.py داشبوردِ read-only
└── cli.py
```

جهتِ وابستگی `kernel ← adapters ← app ← ui` — همان قاعدهٔ `CLAUDE.md`.

### نگاشت به invariantها

| INV | چگونه رعایت شده |
|-----|------------------|
| INV-2 (کارِ برگشت‌ناپذیر ⇒ verdict انسانی) | خروجی فقط `LinkProposal` با `status=proposed`؛ هیچ نوتی ویرایش نمی‌شود |
| INV-4 (یک choke-point) | همهٔ نوشتن‌ها از `ReadOnlyGuard.open_write` رد می‌شوند |
| INV-9 (متنِ عبورکننده از مرزِ اعتماد = داده، نه دستور) | بدنهٔ هر نوت در `QuarantinedText` بسته می‌شود؛ `str()` محتوا را برنمی‌گرداند |
| INV-11 (سیستم قانون خودش را تغییر نمی‌دهد) | این ماژول هیچ invariant/gate/policy را نمی‌خواند و نمی‌نویسد |
| INV-12 (fail closed) | out_dir داخل vault، ریشهٔ ناموجود، mode اشتباه ⇒ استثنا، نه هشدار |

---

## روش‌شناسی — چرا این اعداد circular نیستند

۲۰٪ یال‌ها پنهان می‌شوند. هر representation **فقط** از گراف باقی‌مانده ساخته می‌شود،
بعد باید یال‌های پنهان را از یال‌های جعلی تشخیص دهد (AUC / Average Precision).
ground truth از خودِ داده می‌آید، نه از مدلی که قضاوت می‌شود.

نمونه‌های منفی از **non-edgeهای گرافِ کامل** انتخاب می‌شوند، پس یک یالِ پنهان هرگز
به‌عنوان منفی برنمی‌گردد. و یک `random_control` همیشه در مسابقه هست: اگر به
AUC ≈ ۰٫۵۰ نرسید، split نشت کرده و گزارش خودش می‌گوید **نتایج باطل است**.

---

## تست

```bat
python -m pytest -q
```

۱۶ تست، شامل:

* گارد: نوشتن داخل vault، ریشهٔ vault، و مسیرِ `..` — همه رد می‌شوند
* اسکنر: `.claude`/`node_modules`/`.obsidian` واقعاً کنار می‌روند؛ سقف بلند اعلام می‌شود
* resolution: مسیرِ کامل، مسیرِ نسبی، basenameِ یکتا، و **دو `INDEX.md` که نباید ادغام شوند**
* بلوکِ کد و inline code نباید لینک تولید کنند
* split: هیچ یالِ مثبتی به‌عنوان منفی برنمی‌گردد
* control روی AUC ≈ ۰٫۵ می‌نشیند و برنده حداقل ۰٫۱۰ از آن جلو می‌زند
* end-to-end: **mtime تمام فایل‌های vault قبل و بعد یکسان است**

---

## خروجی‌ها (همه در `F:\kre-out`)

| فایل | محتوا |
|------|-------|
| `latest.json` | چیزی که داشبورد می‌خواند |
| `scan_<stamp>.json` | اینونتوری + exclusionها + هشدارها |
| `graph_<stamp>.json` | گره‌ها، یال‌ها، لینک‌های شکسته، ابهام‌ها |
| `bakeoff_<stamp>.json` | جدول کاملِ رقابت + کنترل |
| `proposals_<stamp>.json` | لینک‌های گم‌شده (فقط پیشنهاد) |
| `verdicts.json` | تأیید/ردِ تو — باز هم **بیرون از vault** |

---

## محدودیت‌های صادقانه

1. هنوز فقط **ساختار** استفاده می‌شود، نه معنا. بخشِ سلسله‌مراتبیِ vault با هیچ روشِ
   ساختاری قابل کشف نیست (در بنچمارک قبلی AUC≈۰٫۵۲ بود). اسکلتِ
   `adapters/embed/` برای embeddingِ محلی (Ollama) آماده است ولی هنوز پر نشده.
2. `--quick` سه representationِ کُند را حذف می‌کند؛ ممکن است برندهٔ واقعی همان‌ها باشند.
3. رتبه‌بندیِ پیشنهادها با cosine similarity در صدرِ جدول اشباع می‌شود؛ tie-break با
   Adamic–Adar انجام می‌شود و مقدارش در `evidence` ذخیره است.
4. اعداد روی vault مصنوعیِ ۲٬۵۰۰ نوتی اعتبارسنجی شده‌اند، نه هنوز روی vault واقعی.
