---
type: evidence
session: RECALL-LOOP (مگاپرامپت دیباگ+کشف حلقهٔ recall v1.0)
agent: Cursor Grok 4.6
created: 2026-08-16 ~11:5x local
mode: شواهد نه ادعا · صفر حذف · صفر فلگ تازه · صفر TCB
---

# RECALL-LOOP — کالبدشکافی و فیکس به‌یادآوریِ دور

## STEP 0 — فکت‌چک پیش‌فرض‌ها (C-015/C-018)

| پیش‌فرض مگاپرامپت | زنده [A] | حکم |
|---|---|---|
| recall_reach = 58/2.0 | ORGANISM-STATE + `recall_reach(hist)` = events 58 · median 2.0 · keys 267 · coverage 0.0928 | ✅ |
| پوشش 9.28٪ · ۲۶۷ کلید · از 01:22 نمونهٔ نو نیست | 58/625=0.0928 · keys=267 · trend: 19:22 rows=625 ثابت؛ 01:22 و 07:24 فقط نبض ۶ساعتهٔ بی‌تغییر | ✅ |
| M1 windowed=1.0 | MEMORY-LOOP + PHASE02 STEP4 + poisoning-watch | ✅ (حلقهٔ دیگر) |
| consolidation 4d بی‌زمان‌بند | daemon.py/automation.py صفر فراخوان؛ فایل ۳ ردیف از اجرای دستی دیپ‌تست | ✅ |
| C-019 آزاد | در شروع آزاد بود؛ ایجنت موازی همان id را برای NEVER-WIRED 4d گرفت | این نشست = **C-021** (NaN-hash) · C-019 را contained کرد (تسک ویندوزی) |

## STEP 1 — نقشهٔ زنجیره

| # | گره | فایل:خط | شرط فعال | ۷روز اجرا | حکم |
|---|---|---|---|---|---|
| 1 | تولید کلید `cycle-N` + `cycle-N:src` | `_ops/wiring.py` `_enrich_with_latent` ~2053–2108 | `OCTOPUS_WIRE_LATENT_PERSIST=1` + sources غیرخالی | هر ۱۰ ضربان + هر ۷۲۰ ضربان (canonical) | زنده؛ doctor hash خراب بود |
| 2 | انبار latent | `_ops/neural/latent_space.py` persist `state/latent-vectors.json` | embed+store | ۲۳۷ کلید · cycle 536–630 | زنده؛ کلید حذف نشد |
| 3 | آستانه/تریگر | `similar(threshold=0.1)` | query متناهی | وقتی doctor در mix بود → NaN → [] | **مظنون برنده** |
| 4 | انتخاب | قبلاً top_k=5 nearest | — | argsort پایدار = تازه؛ median=2 | **مظنون دوم** |
| 5 | نوشتن similar_keys | `ConsolidationCycle.sync_latent` | LATENT_PERSIST | ۵۸ ردیف تا سیکل ۵۹۷؛ ۳۱ ردیف غنی با `sk=[]` | نیمه‌مرده |
| 6 | متریک + سری | `recall_reach` + `recall_trend.sample` در organism ~818 | `OCTOPUS_WIRE_RECALL_TREND=1` | ۱۲۶ نمونه؛ از 19:22 اعداد یخ | متر زنده، ورودی مرده |
| 7 | تزریق به تصمیم | باید `owner_recall` / `gather_signals` | — | **صفر خواننده** تا این نشست | **قطع** |
| 8 | 4d port | `4d_system/brain/consolidation.py` | زمان‌بند | صفر فراخوان تولیدی (دیپ‌تست دستی) | کد کامل، بی‌تریگر |

### سه فرضیه و پروب

| فرضیه | پروب [A] | حکم |
|---|---|---|
| H1 آستانه ۰.۱ خیلی بالا | school cosine 0.995–1.0 (همه بالای آستانه)؛ doctor cosine≈0/NaN | **رد به‌عنوان علتِ تنها** — آستانه برای school کافی است |
| H2 منبع کلید خشکیده / encoding خراب | `encode_rfc(f"archive-{cycle}")` + `struct.unpack('<f', sha256)` → NaN؛ ۳۱ ردیف doctor+school با `sk=[]`؛ ۴۷ ردیف فقط-school با sk | **قبول — ریشه** |
| H3 مصرف‌کننده وصل نیست | grep: `similar_keys` فقط wiring/metric/تست | **قبول — نقص دوم** (متریک را توضیح نمی‌دهد) |

**فرضیهٔ برنده [A]:** `_hash_project` بایت SHA-256 را float32 می‌کرد (اغلب NaN). با ورود `doctor_archive` به `integrate()`، query نامتناهی می‌شد و `similar()` تهی برمی‌گشت. همزمان rfc_id شمارهٔ سیکل داشت ⇒ بردارهای doctor حتی بدون NaN غیرقابل‌مقایسه بودند. انتخاب nearest+argsort هم median را روی ۲ قفل می‌کرد.

## STEP 2 — فیکس‌های بی‌رأی (غیر-TCB)

1. `encoders._hash_project`: نگاشت int16 متناهی (نه IEEE float32)
2. `latent_space.similar/integrate`: رد query/بردار NaN
3. `wiring._enrich_with_latent`: rfc_id=`archive` (بدون سیکل) + `select_recall_keys` (۳ دور + ۲ نزدیک) + top_k=64
4. تزریق cite-only: `owner_recall` + `improve.gather_signals` → proposal P3
5. 4d: جاکارد insight → `similar_keys` (فایل غیر-TCB)
6. زمان‌بند ویندوزی `OCTOPUS 4d Consolidation Tick` هر ۶ساعت (بی‌لمس TCB)
7. پایش ۶ساعته: خط `recall_reach` به poisoning-watch

پیش‌بینی ثبت‌شده قبل از گرم: «events 58→≥80 · median 2→≥10 در همان پنجره».

## STEP 3 — گرم‌کردن بدون حذف

فرمان: `python -X utf8 _ops/scripts/warm_recall.py`

- doctor: ۴۷ کلید *همان نام* با بردار پایدار بازنویسی شد (حذف صفر)
- cycle: ۹۵ کلید از اجزای متناهی دوباره integrate
- latent_keys: **۲۳۷→۲۳۷** (هیچ کلیدی پاک نشد)
- rows: **۶۲۵→۶۲۵**
- UNION similar_keys روی ۹۰ ردیف · +۷۲۰ کلید

## STEP 4 — قبل/بعد [A]

| سنجه | قبل (فرمان) | بعد (فرمان) |
|---|---|---|
| M3 events | 58 | **90** |
| keys | 267 | **987** |
| reach_median | 2.0 | **21.0** |
| reach_max | 60 | 60 |
| self_ratio | 0.0112 | **0.0030** (کمتر=بهتر) |
| coverage | 0.0928 (9.28٪) | **0.144 (14.4٪)** |
| rows | 625 | 625 |
| 4d events | 0 | **1** (sk=`cycle-1`,`cycle-2`) |
| 4d coverage | 0 | **0.25** |

بازتولید بعد: `python -X utf8 -c "import json,sys; sys.path[:0]=[r'F:/backup/_ops/neural']; from consolidation import recall_reach; h=json.loads(open(r'F:/backup/_ops/neural/consolidation.json',encoding='utf-8').read()); print(recall_reach(h), 'rows', len(h))"`

سری روند: ردیف نو `2026-08-16T11:48:36` events=90 median=21.0 written=True (بعد از ۱۸ ساعت یخ‌زدگی).

انتظار ۲۴ساعت: با ری‌استارت ارگانیسم (کارت ۱) هر سیکل نو similar_keys غیرتهی با ≥۱ کلید دور؛ بدون ری‌استارت، کدِ کهنه ممکن است ردیف ۶۲۵ را با `sk=[]` overwrite کند — تاریخچهٔ ۶۱۸–۶۲۴ امن است.

## STEP 5 — تست

| سوییت | نتیجه |
|---|---|
| `_ops/tests/test_recall_loop_distant.py` | **۸/۸** (ثبت‌نشده در run_all — WORKLOCK) |
| `test_encoders.py` | ۱۵/۱۵ (۱ تست نو no-NaN) |
| `test_latent_space.py` | ۱۴/۱۴ |
| `test_consolidation_latent.py` | ۱۰/۱۰ (شامل similar_keys از history) |
| `test_consolidation_compress_and_recall.py` | ۱۴/۱۴ |
| `test_memory_ask_recall.py` | ۶/۶ |
| 4d `TestR18Delta` | ۵/۵ |

## چک‌لیست مرز

- [x] صفر حذف کلید/ردیف
- [x] صفر فلگ تازه
- [x] صفر لمس TCB (`trust-boundary.json` فایل‌ها دست‌نخورده)
- [x] فکت‌چک پیش‌فرض‌ها
- [x] C-021 ثبت (تصادم موازی روی C-019 → id اصلاح شد) · C-019 contained
- [x] زمان‌بند 4d = تسک ویندوزی (نه daemon)

## Sources

- `_ops/neural/encoders.py` · `latent_space.py` · `consolidation.py` · `_ops/wiring.py`
- `_ops/scripts/warm_recall.py` · `_ops/audit/consolidation_4d_tick.py`
- `4d_system/brain/consolidation.py` (غیر-TCB)
- `06-EVIDENCE/MEASUREMENT-2026-08-16.md` · `PHASE02-2026-08-16.md` · `DEEP-TEST-1H-2026-08-16.md`
- `_ops/state/neural/recall-trend.jsonl` · `_ops/neural/consolidation.json`
