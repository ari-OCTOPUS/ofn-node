---
tags: [ofn, megaprompt, edge, agent, glm, supplement, done]
aliases: [مگاپرامپت لبه عمیق, Edge Deep Megaprompt, GLM Edge]
updated: 2026-08-07
status: انجام‌شده ✅
---

# مگاپرامپت تکمیلی — پرورش عمیق مدل لبهٔ سیستم در hypno

> **✅ انجام شد (۱۴۰۵/۰۶/۱۵).** هر چهار کار پایین اجرا شد: مغز، endpoint،
> حافظهٔ روزانه، و سیستم‌پرامپت GLM. hypno ۶۲ تست سبز. این سند حالا یک
> رکورد تاریخی است، نه یک دستورکار باز. برای وضعیت زنده به [[HANDOFF]]
> بخش «پرورش عمیق مدل لبهٔ سیستم» برو.
>
> **(اصلِ قبل از اجرا — برای عامل بعدی):** این سند self-contained است. آنچه
> ایجنت موازی نیمه‌کاره رها کرد را کامل می‌کرد: کد مدل `edge.py` هست و در RAG
> پیدا می‌شود، ولی **به مغز وصل نیست، endpoint تعاملی ندارد، و حافظهٔ روزانه‌ای
> برای قانون سه‌روزه ذخیره نمی‌کرد.** این مگاپرامپت آن سه شکاف را بست.

**پیوندها:** [[MEGAPROMPT-UNIFY]] (ادغام کل) · [[INDEX]] · [[HANDOFF]] ·
[[DECISIONS|D-22]] (متن فنی ممنوع در UI)

---

## ۰) قانون اساسی

تو یک مهندس فول‌استک هستی که روی `/home/ari/hypno-fugu-mini` کار می‌کنی
(اورنج‌پای ۵ پرو، ARM64، ۴ گیگ رم). زبان UI و پیام‌ها **فارسی، ساده، گرم،
غیرفنی** است. کلمات ممنوع در UI: RAG، model، token، API، schema، payload،
inference، dataset، database، backend ([[DECISIONS|D-22]]).

**سه اصل غیرقابل‌مذاکره:**
1. **هیچ دیتایی از دست نمی‌رود** — قبل از تغییر اسکیما، WAL را checkpoint کن.
2. **سرویس نشکند** — `hypno-fugu-mini.service` باید `active` بماند. هر تغییر،
   restart + `/health` 200 + pytest دارد.
3. **کد خالص stdlib** — `edge.py` از قبل خالص است؛ توابع جدید هم بدون I/O.

---

## ۱) وضعیت امروز — حقیقت روی زمین

تأیید کن با کوئری زنده، نه با این سند:

```
pytest hypno            python3 -m pytest -q   →  ۴۳ تست سبز
DB hypno research_docs  ۱۳۲ (۱۲۴ قدیم + ۸ لبه)
services                hypno-fugu-mini.service active
edge.py                 ۳۲۴ خط · ۱۹ تابع · خالص stdlib · در kernel/edge.py
edge_chunks در RAG       پیدا می‌شوند (مسیر مستقیم در run.py:edge_chunks)
```

**سه شکاف که این مگاپرامپت می‌بندد:**
1. `edge.py` به مغز وصل نیست — `brain.py` از توابع لبه استفاده نمی‌کند.
2. endpoint تعاملی نیست — کاربر نمی‌تواند نمره بدهد و نتیجه بگیرد.
3. حافظهٔ روزانه نیست — قانون سه‌روزه `three_red_days` چیزی برای خواندن ندارد.

---

## ۲) معماری هدف

```
┌──────────────────────────────────────────────────────────┐
│  کاربر (تلگرام / curl)                                    │
│    «امشب تا ۳ کدنویسی کنم؟»  ·  POST /api/edge/daily {B,C,X}│
└───────────────┬──────────────────────────┬───────────────┘
                │                          │
        ┌───────▼────────┐         ┌──────▼────────┐
        │  brain.answer  │         │ /api/edge/*   │
        │  + edge مدل    │         │  endpoints    │
        │  در پرامپت     │         │  (جدید)       │
        └───────┬────────┘         └──────┬────────┘
                │                          │
        ┌───────▼────────────────────────▼────────┐
        │         kernel/edge.py (موجود)            │
        │  decision_source · daily_verdict ·        │
        │  three_red_days · les · decomposition     │
        └────────────────────┬─────────────────────┘
                             │
                ┌────────────▼────────────┐
                │  store.edge_daily_log   │
                │  (جدول جدید edge_daily)  │
                │  برای قانون سه‌روزه      │
                └─────────────────────────┘
```

---

## ۳) کارها — هر کدام قابل‌اجرا و قابل‌واگرد

### کار ۱ · مغز را به مدل وصل کن (`brain.py`)

الان `brain.py` یک سیستم‌پرامپت یک‌خطی دارد و از `edge.py` خبر ندارد. وقتی
`App.chat` یک موضوع لبه تشخیص می‌دهد (`is_edge_topic`، که از قبل هست)، مغز
باید:
- اگر کاربر نمره‌های ۰-۱۰ داده (مثل «خواب ۳، فلو ۸، هوس ۷»)، آن‌ها را با
  `edge.decision_source` یا `edge.daily_verdict` محاسبه کند و نتیجهٔ فارسی
  را در جواب بیاورد.
- اگر کاربر فقط دربارهٔ موضوع لبه حرف می‌زند، chunks لبه (که از قبل در
  citations هست) را در پرامپت مغز بگنجاند و از مغز بخواهد با زبان مدل جواب
  دهد.

**تغییرات `hypno/adapters/brain.py`:**

```python
import json, urllib.request, re
from hypno.kernel.safety import script, mode_prompt
from hypno.kernel import edge

# کمکی: آیا پیام نمره‌های ۰-۱۰ دارد؟ (مثل "خواب ۳ فلو ۸ هوس 7")
_SCORE_RE = re.compile(r'(خواب|فلو|هوس|مصرف|پرخوری|بدن|فروش|کدنویسی|اسکرول|'
                       r'استرس|حلقه|پول|sleep|flow|craving|weed|stress|'
                       r'body|sales|code|scroll|money|loop)\s*[:=]?\s*(\d{1,2})',
                       re.IGNORECASE)

def _extract_scores(text):
    """نمره‌های ۰-۱۰ را از متن کاربر بکش. خروجی dict یا None."""
    out = {}
    for m in _SCORE_RE.finditer(text or ''):
        key = m.group(1).lower()
        val = int(m.group(2))
        if 0 <= val <= 10:
            out[key] = val
    return out if len(out) >= 2 else None
```

سپس در `Brain.answer` (و `rules` برای حالت آفلاین)، وقتی `_extract_scores`
نمره پیدا کرد، `edge.decision_source` یا `edge.daily_verdict` را صدا بزن و
نتیجهٔ فارسی (`r.verdict`) را به جواب اضافه کن.

سیستم‌پرامپت را هم گسترش بده تا مغز بداند مدل لبه وجود دارد و وقتی موضوع
مرتبط است، با زبان آن (سه قطب: بدن/خود/ابرموجود) جواب دهد — **به فارسی
ساده، بدون کلمهٔ فنی**.

### کار ۲ · endpointهای تعاملی لبه (`run.py`)

سه endpoint جدید اضافه کن (همراه با تست):

```
POST /api/edge/decision
  body: {V,P,K,D,H,E,F,M,U,C,sleep_debt,stress}  (همه ۰-۱۰، اختیاری)
  → {ok, ai, si, bi, a_self, a_super, a_body, verdict, healthy}
  محاسبه با edge.decision_source.

POST /api/edge/daily
  body: {B,C,X}  (۰-۱۰)
  → {ok, verdict, advice, streak}
  محاسبه با edge.daily_verdict + three_red_days (از روی حافظه).

GET /api/edge/history
  → {ok, days: [...]}  (آخرین ۱۴ روز log روزانه، برای نمودار/بازتاب)
```

این endpointها باید مثل بقیهٔ `/api/*` از `self.user(b)` برای شناسایی کاربر
استفاده کنند (dev_user وقتی کلید بات نیست). پاسخ همگی فارسی ساده است.

### کار ۳ · حافظهٔ روزانه (`store.py` + جدول جدید)

یک جدول جدید `edge_daily` به اسکیما اضافه کن (با `CREATE TABLE IF NOT
EXISTS`، idempotent):

```sql
CREATE TABLE IF NOT EXISTS edge_daily(
  id INTEGER PRIMARY KEY,
  user_id TEXT NOT NULL,
  day TEXT NOT NULL,           -- YYYY-MM-DD (UTC)
  b REAL, c REAL, x REAL,      -- نمره‌های ۰-۱۰
  verdict TEXT,                 -- سبز/زرد/قرمز
  created_at INT NOT NULL,
  UNIQUE(user_id, day)
);
```

به `Store` این متدها را اضافه کن:
- `log_edge_daily(user, day, b, c, x, verdict)` — upsert (یک ردیف در روز).
- `edge_history(user, limit=14)` — آخرین N روز به ترتیب قدیم‌به‌جدید.

**مهم:** اسکیما با `IF NOT EXISTS` و `executescript` در `Store.__init__`
(مثل بقیهٔ جدول‌ها) — هیچ مهاجرت مخرب. WAL را قبل از تست checkpoint کن.

### کار ۴ · سیستم‌پرامپت GLM طراحی کن

مغز ریموت (وقتی `cfg.api_key` هست) باید یک سیستم‌پرامپت قوی داشته باشد که
مدل را به استفادهٔ درست از مدل لبه هدایت کند. این پرامپت را در یک ثابت
بگذار (`EDGE_SYSTEM_PROMPT` در `brain.py` یا یک فایل جدا `prompts.py`):

```
تو دستیار فارسیِ خودهیپنوتیزمی و خودمدیریتِ آری هستی. دو بال داری:

۱. خودهیپنوتیزمی: امن، علمی، رضایت‌محور، قابل‌قطع. درمان/کنترل ذهن ادعا نکن.
   جلسات کوتاه، چشم‌باز، با خروج مشخص.

۲. مدل لبهٔ سیستم: تصمیم‌های آری از سه منبع می‌آیند — بدن (خواب/هوس/خستگی)،
   خود بازتابی (ارزش/برنامه/پایداری)، ابرموجود (بازار/ترند/فشار). وقتی
   کاربر دربارهٔ تصمیم/خواب/فروش/فلو/مصرف حرف می‌زند، با این سه قطب فکر کن.

قوانین:
- اگر کاربر نمره داد (مثل «خواب ۳»)، نتیجه را با عدد بگو: «سهم بدنت در این
  تصمیم بیشتر بود»، نه «BI=0.61». عدد فنی در UI ممنوع.
- هیچ‌وقت نگویی «RAG»، «model»، «token»، «API»، «schema»، «payload».
- اگر نشانهٔ بحران (آسیب به خود، ناامیدی شدید) دیدی، فوراً به کمک واقعی
  ارجاع بده و جلسه را شروع نکن.
- منبع‌هایی که در بافت آمده‌اند را طبیعی ذکر کن، نه با کلمهٔ فنی.
```

وقتی `is_edge_topic` درست است، این سیستم‌پرامپت استفاده شود؛ در غیر این‌صورت
سیستم‌پرامپت کوتاه فعلی.

---

## ۴) تست‌ها (`tests/test_edge.py` را گسترش بده)

این تست‌های جدید را اضافه کن (هر کدام red-green):

```python
class EdgeBrainWiringTests(unittest.TestCase):
    def test_extract_scores_from_persian(self):
        from hypno.adapters.brain import _extract_scores
        s = _extract_scores('خواب ۳، فلو ۸، هوس ۷')
        self.assertEqual(s['خواب'], 3)
        self.assertEqual(s['فلو'], 8)

    def test_extract_scores_returns_none_when_too_few(self):
        from hypno.adapters.brain import _extract_scores
        self.assertIsNone(_extract_scores('سلام امروز چطورمی؟'))

    def test_chat_with_scores_returns_verdict_in_reply(self):
        # وقتی کاربر نمره می‌دهد، جواب شامل تفسیر فارسی است
        app = App(_test_cfg())
        r = app.chat({'text': 'خواب ۳ فلو ۸ هوس ۷ مصرف ۶', 'mode': 'calm',
                      'consent': True, '_auth': ''})
        self.assertIn('بدن', r['reply'] + r.get('verdict', ''))


class EdgeEndpointTests(unittest.TestCase):
    def test_decision_endpoint(self):
        app = App(_test_cfg())
        r = app.edge_decision({'V':8,'P':3,'K':2,'D':4,'H':3,'E':9,'F':6,
                               'M':3,'U':7,'C':3,'sleep_debt':8,'stress':5,
                               '_auth':''})
        self.assertTrue(r['ok'])
        self.assertGreater(r['a_super'], r['a_self'])  # late-night → super

    def test_daily_endpoint_logs_and_streaks(self):
        app = App(_test_cfg())
        r1 = app.edge_daily({'B':3,'C':2,'X':8,'_auth':''})
        self.assertEqual(r1['verdict'], 'زرد')
        # سه روز قرمز پشت‌سرهم → قرمز
        for _ in range(2):
            app.edge_daily({'B':3,'C':2,'X':8,'_auth':''})
        r3 = app.edge_daily({'B':3,'C':2,'X':8,'_auth':''})
        # streak باید ≥ ۳ شده باشد

    def test_history_endpoint(self):
        app = App(_test_cfg())
        app.edge_daily({'B':7,'C':6,'X':3,'_auth':''})
        h = app.edge_history({'_auth':''})
        self.assertTrue(h['ok'])
        self.assertGreater(len(h['days']), 0)


class EdgeMemoryTests(unittest.TestCase):
    def test_daily_log_is_upsert_per_day(self):
        # دو بار در همان روز → یک ردیف (نه دو)
        ...
```

`_test_cfg()` یک `Config` با `tempfile` می‌سازد (الگوی موجود در `test_core.py`).

---

## ۵) ممنوعیت‌ها

- ❌ `edge.py` را بازنویسی نکن — فقط به مغز و endpoint وصلش.
- ❌ متن فنی در پاسخ کاربر (RAG/model/token/...). عدد مدل → جملهٔ فارسی.
- ❌ جدول موجود را drop نکن — فقط `CREATE TABLE IF NOT EXISTS edge_daily`.
- ❌ WAL را بدون checkpoint تغییر بده.
- ❌ endpoint بدون `self.user(b)` (شناسایی کاربر).
- ❌ مغز را در write path بلوکه کن (قاعدهٔ B-۲ مگاپرامپت اصلی).
- ❌ بحران را نادیده بگیر — `classify().allow is False` همیشه قبل از مغز.

---

## ۶) ترتیب اجرا (هر مرحله قابل‌واگرد)

```
۰. backup: cp edge.py brain.py run.py store.py test_edge.py → *.bak-deep-<ts>
   wal_checkpoint(TRUNCATE).
۱. store.py: جدول edge_daily + log_edge_daily + edge_history.
۲. brain.py: _extract_scores + وصل edge.decision_source/daily_verdict +
   EDGE_SYSTEM_PROMPT.
۳. run.py: edge_decision / edge_daily / edge_history + route‌ها.
۴. test_edge.py: تست‌های جدید (کار ۴).
۵. py_compile + pytest -q → باید سبز بماند (۴۳ + جدید).
۶. restart + /health 200 + تست curl زنده.
۷. گزارش فارسی (§۷) + به‌روزرسانی [[HANDOFF]].
```

---

## ۷) گزارش نهایی که باید بدهی

وقتی همه چیز تست شد، گزارش فارسی بده که دقیقاً این‌ها را بگو:

۱. کدام فایل‌ها تغییر کردند (با خط شماره).
۲. مغز به مدل وصل شد یا نه — `_extract_scores` + `decision_source` در `rules`
   و `remote`.
۳. سیستم‌پرامپت GLM ساخته شد یا نه — متن آن.
۴. سه endpoint ساخته شد یا نه — مسیرها + نمونه پاسخ.
۵. حافظهٔ روزانه ساخته شد یا نه — اسکیما + upsert + قانون سه‌روزه.
۶. هیچ دیتایی از دست رفت یا نه — شمارش قبل/بعد.
۷. سرویس شکست یا نه — `is-active` + `/health`.
۸. تست‌ها: تعداد سبز (۴۳ + جدید).
۹. نمونهٔ زنده: یک `curl POST /api/edge/decision` با نمره‌های «کدنویسی تا ۳
   صبح» → پاسخ.
۱۰. مسیرهای زنده: `/health`، `/api/edge/*`.

**هر ادعا یک رکورد مستقل. هیچ‌چیز ادعا نشود مگر تست‌شده.**

---

## ۸) مسیرها برای عامل بعدی

```
پروژه:      /home/ari/hypno-fugu-mini
کد مدل:     hypno/kernel/edge.py        (۳۲۴ خط، ۱۹ تابع، خالص stdlib)
متن RAG:    hypno/adapters/edge_seed.py  (۸ chunk، idempotent)
چت/endpoint: hypno/run.py                (App.chat + edge_chunks + is_edge_topic)
مغز:        hypno/adapters/brain.py      (این مگاپرامپت آن را گسترش می‌دهد)
ذخیره:      hypno/adapters/store.py      (این مگاپرامپت جدول edge_daily می‌افزاید)
تست:        tests/test_edge.py           (۳۸ تست، این مگاپرامپت می‌افزاید)
DB:         ~/.local/share/hypno-fugu-mini/hypno.sqlite
سرویس:      hypno-fugu-mini.service (port 8895)
والت:       /home/ari/ofn (ابسیدین) — این سند + MEGAPROMPT-UNIFY + HANDOFF
```

این مکمل [[MEGAPROMPT-UNIFY]] است، نه جایگزینش. فازبندی ادغام کل هنوز معتبر
است؛ این مگاپرامپت فقط «پرورش عمیق مدل لبه» را کامل می‌کند.
