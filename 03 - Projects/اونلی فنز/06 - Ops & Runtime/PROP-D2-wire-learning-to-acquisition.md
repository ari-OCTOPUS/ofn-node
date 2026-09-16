---
type: report
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: idea
created: 2026-07-12
updated: 2026-07-12
created_by: agent
sources:
  - "[[brain/BRAIN-BENCHMARK-2026-07-10]]"
  - "[[00 - Control/CARTOGRAPHY-2026-07-12]]"
  - "[[PROJECT-F-BRAIN-SPEC]]"
  - "[[AGENT-CONTROL-INTERFACE]]"
tags: [project-f, brain, learning, bandit, acquisition, wiring, proposal, ops]
aliases: ["PROP-D2", "Wire Learning→Acquisition", "وصل‌کردنِ بندیت به جذب"]
---

# PROP-D2 — وصل‌کردنِ لایهٔ یادگیری (`learning.py`) به مسیرِ رتبه‌بندیِ جذب (`acquisition.py`)

> **PROPOSAL / propose-only.** این سند فقط یک طرحِ وصل است. هیچ کدی اعمال، هیچ تستی اجرا، و هیچ اکشنِ بیرونی انجام نمی‌شود. PLAN ≠ APPROVAL ≠ EXECUTION. هر «اجرا»ی تست = اجرای کد = زیرِ GATE 0 قرمز (بخش ۶).

## TL;DR
`brain/learning.py` (`ThompsonBandit` / `UCB1` / `LearningBridge`) **ساخته و ۱۰/۱۰ تست‌شده** است `[FACT — brain/test_learning.py]`، اما **در هیچ ماژولِ production ایمپورت نمی‌شود** `[FACT — grep زیر]`. مسیرِ زندهٔ رتبه‌بندی هنوز `AcquisitionBrain.analyze()` است که با **میانگینِ خامِ greedy** رتبه می‌دهد — یعنی **دقیقاً همان باگی که `BRAIN-BENCHMARK` ادعا می‌کند رفع شده، هنوز در مسیرِ جذب زنده است** `[FACT]`. این سند یک دیفِ حداقلی، additive، flag-gated و default-off پیشنهاد می‌کند تا رتبه‌بندی از `LearningBridge.recommend()` عبور کند، بدونِ شکستنِ هیچ مصرف‌کننده‌ای.

---

## ۱. مسیرِ greedy (file:line) در برابرِ API در دسترسِ LearningBridge

### ۱.۱ اثباتِ «سیم‌نشده» `[FACT]`
```
$ grep -rn "import learning|from learning|LearningBridge|.recommend(" --include=*.py  (پروژه)
brain/learning.py:263: class LearningBridge          ← تعریف
brain/learning.py:281: def recommend(...)            ← تعریف
brain/test_learning.py:8: import learning as L        ← تنها ایمپورت‌کننده = تست
```
هیچ فایلِ production (نه `orchestrator.py`، نه `acquisition.py`، نه `dual_brain_v3.py`) `learning` را ایمپورت نمی‌کند. `AGENT-CONTROL-INTERFACE.md:66` قابلیتِ `LearningBridge.recommend()` را **تبلیغ می‌کند** ولی runtime آن را صدا نمی‌زند → قرارداد اعلام‌شده ولی وصل‌نشده. `00 - Control/CARTOGRAPHY-2026-07-12.md:47` همین گاف را قبلاً ثبت کرده؛ این سند دنبالهٔ D2 آن است.

### ۱.۲ مسیرِ زندهٔ greedy — دقیق `[FACT]`
مصرف‌کنندهٔ زنده: `orchestrator.py:54` یک `AcquisitionBrain` می‌سازد. زنجیرهٔ رتبه‌بندی:

| گام | محل | رفتار |
|---|---|---|
| میانگینِ خام | `acquisition.py:120-131` `tag_performance()` | میانگینِ ساده روی همهٔ داده‌ها؛ **بدونِ recency، بدونِ اکتشاف** |
| اشباعِ امتیاز | `acquisition.py:128-129` | `min(1.0, upvotes/100 + comments/20 + unlocks/5)` → برندگانِ قوی به ۱٫۰ می‌چسبند |
| ساختِ insights | `acquisition.py:170-207` `analyze()` | `predicted_score` = `own*0.5` (l.182) / `comp*0.3` (l.194) / `combined+0.1` (l.203-204) |
| **رتبه‌بندیِ نهایی** | `acquisition.py:209` | `insights.sort(key=lambda i: i.predicted_score, reverse=True)` ← **greedy خالص** |
| مصرفِ رتبه | `acquisition.py:219` `plan_week()` | `top_tags = [i.tag for i in insights[:5]]`؛ برش نهایی `insights[:5]` (l.234) |
| A/B و فوکوس | `acquisition.py:223-224, 233-241` | مستقیماً از همان ترتیبِ greedy مشتق می‌شود |

نتیجه: هر تصمیمِ «هفتهٔ بعد چه کنم» از یک sortِ greedyِ بی‌اکتشاف می‌آید. طبقِ `regret_eval` خودِ سیستم (`learning.py:196-245`)، greedy در بخشی از اجراها روی برندهٔ نویزیِ اولیه قفل می‌شود `[FACT — کدِ eval موجود؛ عددِ «~۲۵٪ / regret 90-105» ادعای BENCHMARK §۳ است، در این سند اجرا/تأیید نشده → [EST]]`.

> نکتهٔ مرزی `[FACT]`: `orchestrator.py:130` هم `tag_performance()` را صدا می‌زند، ولی فقط به‌عنوان ورودیِ `consolidation` (نه رتبه‌بندی). آن مسیر عمداً بیرونِ دامنهٔ این وصل می‌ماند (بخش ۴/Preserved).

### ۱.۳ API در دسترس (چیزی که باید صدا زده شود) `[FACT]`
| عنصر | محل | امضا / رفتار |
|---|---|---|
| `LearningBridge(acq_memory, halflife_days, seed)` | `learning.py:263-279` | از `acq_memory._post_results` (l.275) یک bandit ephemeral می‌سازد؛ `_save` خنثی (l.273) → **کانِن دوم نمی‌سازد** |
| `recommend(candidate_tags) -> dict` | `learning.py:281-287` | `{ranked:[(tag,score)], top, explain, note}` — رتبهٔ اکتشاف‌دار + شفافیت |
| `ThompsonBandit.rank()` | `learning.py:134-147` | نمونهٔ posterior هر arm؛ min-pull boost برای armِ کم‌داده (l.143-144) |
| `normalize_reward()` | `learning.py:49-53` | `tanh(upvotes/80 + comments/15 + unlocks/4)` — **بی‌اشباع** (برخلافِ `tag_performance`) |
| `UCB1` (قطعی) | `learning.py:169-192` | جایگزینِ بدون‌تصادفِ Thompson (reproducible) |

**تفاوتِ ظریفِ نرمال‌سازی `[FACT]`:** `tag_performance()` از `/100, /20, /5` با سقفِ ۱ استفاده می‌کند؛ `LearningBridge` از `normalize_reward` با `/80, /15, /4` + `tanh`. یعنی وصل‌کردن **هم** باگِ greedy را رفع می‌کند **هم** نرمال‌سازی را عوض می‌کند → مقدارِ مطلقِ `predicted_score` حتی برای دادهٔ یکسان جابه‌جا می‌شود (ریسکِ R2).

---

## ۲. دیفِ پیشنهادی (pseudo-diff — اعمال نشود)

اصولِ طراحی: **additive · flag-gated · default-off · بدونِ کانِن دوم · شکلِ خروجی حفظ‌شده.** چون هیچ تستِ acquisition/orchestrator وجود ندارد (بخش ۳)، default-off یعنی رفتار بیت‌به‌بیت بدون‌تغییر و سوئیت سبز می‌ماند.

### ۲.۱ فلگ + وصلِ اختیاری در `AcquisitionBrain.__init__`
```diff
# acquisition.py — بالای فایل، کنارِ importها
+ # وصلِ اختیاری به لایهٔ یادگیری (default-off؛ فعال‌سازی با env یا آرگومان)
+ LEARNING_WIRED_ENV = "PF_LEARNING_WIRED"

  class AcquisitionBrain:
-     def __init__(self, memory: AcquisitionMemory | None = None):
+     def __init__(self, memory: AcquisitionMemory | None = None,
+                  use_learning: bool | None = None,
+                  learning_seed: int | None = 1337):
          self.memory = memory or AcquisitionMemory()
+         # پیش‌فرض: خاموش. فقط با env=1 یا آرگومانِ صریح روشن می‌شود (governance).
+         self._use_learning = (use_learning if use_learning is not None
+                               else os.environ.get(LEARNING_WIRED_ENV, "") == "1")
+         self._learning_seed = learning_seed   # seedِ ثابت → رتبهٔ reproducible در یک چرخه
```

### ۲.۲ عبورِ رتبه از bridge در انتهای `analyze()`
```diff
  # acquisition.py:208-210
          # sort by predicted_score desc
          insights.sort(key=lambda i: i.predicted_score, reverse=True)
+         if self._use_learning and insights:
+             insights = self._bandit_reorder(insights)   # اکتشاف‌دار؛ propose-only
          return insights
```

### ۲.۳ متدِ کمکیِ جدید (ephemeral، بدونِ نوشتنِ دیسک)
```diff
+     def _bandit_reorder(self, insights: list[ContentInsight]) -> list[ContentInsight]:
+         """رتبه‌بندیِ اکتشاف‌دار via LearningBridge — منبعِ حقیقت همان self.memory.
+         شکلِ ContentInsight حفظ می‌شود؛ فقط ترتیب + شفافیتِ reason به‌روز می‌شود."""
+         from learning import LearningBridge            # lazy: مسیرِ default ایمپورت‌آزاد
+         # dedupe: یک tag می‌تواند در دو دسته (own + both) تکرار شود (l.179 و l.199) →
+         # اولین ظهور را نگه‌دار تا رتبه دوباری نشود.
+         seen, uniq = set(), []
+         for i in insights:
+             if i.tag not in seen:
+                 seen.add(i.tag); uniq.append(i)
+         bridge = LearningBridge(self.memory, seed=self._learning_seed)
+         rec = bridge.recommend([i.tag for i in uniq])      # {ranked, explain, ...}
+         order = {tag: n for n, (tag, _score) in enumerate(rec["ranked"])}
+         expl = rec["explain"]["arms"]
+         for i in uniq:
+             stat = expl.get(i.tag, {})
+             # نکته: predicted_score را بازنویسی نمی‌کنیم تا مقیاسِ قدیم نشکند؛
+             # فقط شفافیتِ بندیت را به reason می‌چسبانیم (responsible-AI).
+             i.reason += f" · bandit μ={stat.get('mean','?')} σ={stat.get('uncertainty','?')}"
+         uniq.sort(key=lambda i: order.get(i.tag, 1e9))     # ترتیبِ اکتشاف‌دار
+         return uniq
```

**چرا حداقلی است:** یک آرگومان + یک شرطِ ۲خطی + یک متد. `plan_week()`/`suggest_next_action()` بدونِ تغییر رفتارِ جدید را ارث می‌برند (چون از `analyze()` تغذیه می‌شوند). مسیرِ default (فلگ خاموش) حتی `learning` را ایمپورت نمی‌کند (lazy import داخلِ متد).

**تصمیمِ باز برای A `[OPEN]`:** آیا `predicted_score` هم باید به `bandit μ` بازنویسی شود؟ اگر بله → رتبه و نمایش کاملاً از bandit می‌آید ولی مقیاسِ نمایشیِ کارت‌ها عوض می‌شود (R2). طرحِ فعلی محافظه‌کارانه فقط **ترتیب** را عوض می‌کند و امتیازِ نمایشی را دست‌نخورده می‌گذارد.

---

## ۳. طرحِ تستِ رگرسیون (چه چیزی قبل/بعد اضافه شود تا امن باشد)

> **وضعیتِ فعلی `[FACT]`:** هیچ `test_acquisition.py` یا تستِ orchestrator وجود ندارد (تنها تست‌ها: `brain/test_learning.py`, `langar/test_langar.py`, `studio/test_saba_studio.py`). پس «تست‌های موجود می‌شکند» درست نیست؛ خطرِ واقعی این است که **هیچ تور ایمنی‌ای زیرِ این تغییر نیست.** بنابراین اول باید characterization test نوشت.

### ۳.۱ قبل از تغییر — تثبیتِ رفتارِ فعلی (characterization / golden)
| # | تست | هدف |
|---|---|---|
| B1 | `test_analyze_orders_by_predicted_score_desc` | ثبتِ داده، assert ترتیب == sortِ greedyِ فعلی (l.209) |
| B2 | `test_plan_week_returns_top5_shape` | `focus_tags`، `posting_schedule`، `ab_test_idea` شکل و طولِ فعلی |
| B3 | `test_tag_performance_saturation_at_1` | پینِ رفتارِ `min(1.0,…)` (l.128-129) به‌عنوان baselineِ نرمال‌سازی |

### ۳.۲ بعد از تغییر — پاریتی + رفتارِ جدید
| # | تست | assert |
|---|---|---|
| A1 | `test_flag_off_is_bitwise_baseline` | با فلگ خاموش، خروجیِ `analyze()`/`plan_week()` **دقیقاً** == B1/B2 (اثباتِ default-off بی‌اثر) |
| A2 | `test_flag_off_does_not_import_learning` | با فلگ خاموش، `sys.modules` شاملِ `learning` نشود (lazy import) |
| A3 | `test_bandit_reorders_toward_high_reward` (seeded) | با seed ثابت، tagِ پرپاداش اکثراً بالاتر از پرداده‌ی ضعیف؛ **آماری روی N اجرا** نه تساویِ سخت (rank تصادفی است) |
| A4 | `test_explores_undersampled_competitor_tag` | tagِ رقیبِ هرگز-تست‌نشده گاهی در top-5 ظاهر شود (min-pull boost, `learning.py:143-144`) — آینهٔ test_learning #3 |
| A5 | `test_recency_demotes_stale_winner` | برندهٔ قدیمی که ترندش افت کرده تنزل کند — آینهٔ test_learning #6 |
| A6 | `test_no_second_canon` | بعد از `analyze()` با فلگ روشن، فایلِ `acquisition_memory.json` **تغییر نکند** و هیچ فایلِ bandit روی دیسک نوشته نشود (ephemeral, `learning.py:273`) |
| A7 | `test_deterministic_with_fixed_seed` | دو `AcquisitionBrain(use_learning=True, learning_seed=k)` ترتیبِ یکسان بدهند (R1) |
| A8 | `test_duplicate_tag_dedup` | tagِ حاضر در دو دسته (own+both) در ترتیبِ نهایی فقط یک‌بار بیاید (dedupِ ۲.۳) |
| A9 | `test_shape_preserved` | خروجی همچنان `list[ContentInsight]` با فیلدهای `.tag/.predicted_score/.confidence` (مصرف‌کننده‌ها نشکنند) |

نکتهٔ روش: چون `rank()` تصادفی است (`betavariate`, `learning.py:142`)، assertهای رفتاری باید **آماری روی N نمونه با seed ثابت** باشند (همان الگوی test_learning: `picks.count(...)`)، نه تساویِ یک‌باره. اگر A تکرارپذیریِ سخت بخواهد → گزینهٔ `UCB1` (قطعی، `learning.py:169`) برای مسیرِ production و Thompson برای آزمایش.

---

## ۴. قالبِ PMO

### Current (اکنون)
- رتبه‌بندیِ زندهٔ جذب = greedy mean (`acquisition.py:120-131` + sort `:209`)، بی‌اکتشاف، بی‌recency، با اشباعِ `min(1.0,…)`.
- `learning.py` کامل و تست‌شده ولی **مرده در runtime** (تنها ایمپورت‌کننده = test).
- `AGENT-CONTROL-INTERFACE.md:66` قابلیت را تبلیغ می‌کند اما وصل نیست → گافِ سند‑در‑برابر‑واقعیت.
- هیچ تستِ acquisition/orchestrator وجود ندارد → تغییر بدون تور ایمنی.

### Delta (تغییرِ پیشنهادی)
- افزودنِ فلگِ `use_learning`/`PF_LEARNING_WIRED` (default-off) + آرگومانِ `learning_seed` به `AcquisitionBrain.__init__`.
- شرطِ ۲خطی در `analyze()` (بعد از l.209) + متدِ `_bandit_reorder()` که رتبه را از `LearningBridge.recommend()` می‌گیرد.
- lazy importِ `learning` فقط وقتی فلگ روشن است.
- افزودنِ ۳ characterization + ۹ regression test (بخش ۳) — **نوشتن، نه اجرا** (GATE 0).

### Preserved (دست‌نخورده — خطوطِ قرمز)
- propose-only و `λ_persist<0`: bridge فقط ساعتِ تولیدِ سبک‌های ازقبل-compliant را رتبه می‌دهد؛ هیچ چیزی رو به فن دستکاری نمی‌شود (`learning.py:9-16`, BENCHMARK §۴).
- **منبعِ حقیقتِ واحد:** bandit ephemeral است (`learning.py:273`)؛ کانِن دوم ساخته نمی‌شود — همچنان `acquisition_memory.json`.
- فلور/سقفِ اکتشاف hard-coded ۵٪–۴۰٪ (`learning.py:34-35`)، min-pull=۳ → weekly allocator، نه per-post switcher.
- شکلِ `ContentInsight`/`WeekPlan` و همهٔ مصرف‌کننده‌ها (orchestrator, control-interface).
- مسیرِ `orchestrator.py:130` (`tag_performance()` → consolidation) بیرونِ دامنه، بدونِ تغییر.
- default-off = رفتارِ تولیدِ فعلی بیت‌به‌بیت حفظ می‌شود تا A صریحاً روشن کند (دوکلیده).

### Rollback
- **فوری:** فلگ را خاموش کن (unset `PF_LEARNING_WIRED` یا `use_learning=False`) → مسیرِ greedyِ قبلی بی‌کم‌وکاست برمی‌گردد؛ چون هیچ state جدیدی نوشته نمی‌شود، rollback بی‌عارضه است.
- **کامل:** `git revert` روی همان یک هانکِ additive در `acquisition.py`؛ بدونِ مهاجرتِ داده، بدونِ تغییرِ فرمتِ `acquisition_memory.json`.
- هیچ فایلِ جدیدِ حالت، هیچ اثرِ ماندگار → rollback بدونِ پاکسازی. (طبقِ قانونِ اساسی: انتقال/برگشت، نه حذف.)

---

## ۵. ریسک‌ها
| # | ریسک | شدت | کاهش |
|---|---|---|---|
| R1 | **نادترمینیسم:** `rank()` تصادفی (`learning.py:142`) → کارتِ /ops هر اجرا فرق کند، غیرقابل‌بازتولید | متوسط | `learning_seed` ثابت در طرح؛ یا `UCB1` قطعی برای production. `LearningBridge` پیش‌فرض `seed=None` است (`learning.py:270`) → **باید** seed صریح پاس شود |
| R2 | **واگراییِ نرمال‌سازی:** bridge از `tanh(/80,/15,/4)` استفاده می‌کند نه `min(1,/100,/20,/5)` → مقیاسِ `predicted_score` عوض می‌شود | متوسط | طرحِ فعلی `predicted_score` را بازنویسی نمی‌کند (فقط ترتیب)؛ تصمیمِ نهایی با A (OPEN بخش ۲.۳) |
| R3 | **surfaceشدنِ tagِ تست‌نشده:** min-pull boost tagِ رقیبِ ناآزموده را بالا می‌آورد | پایین (این هدفِ اکتشاف است) | همچنان propose-only + برچسبِ اکتشاف در `reason`؛ سقفِ ۴۰٪ hard-coded |
| R4 | **`Path("/dev/null")` هاردکد** در `LearningBridge` (`learning.py:272`) روی Windows | پایین | بی‌اثر (load خطا→[]، save خنثی) ولی بوی cross-platform؛ پیشنهاد: `data_path=None`+`_save=noop` تمیزتر است `[SPEC]` |
| R5 | **دو دسته با tagِ تکراری** (own+both, `acquisition.py:179`+`199`) → رتبهٔ دوباری | پایین | dedup در `_bandit_reorder` (تست A8) |
| R6 | **نبودِ تور ایمنی فعلی:** بدون characterization test، هر تغییر کور است | متوسط | B1-B3 قبل از هر چیز نوشته شوند |

---

## ۶. گِیت (اجرا = قرمز)
هر **اجرا**ی این تست‌ها یا هر `python`ای که این مسیر را لمس کند = اجرای کد = زیرِ GATE 0 پروژه‌ی Project-F **قرمز** است. این سند تست‌ها را **می‌نویسد/طرح می‌ریزد**، اجرا نمی‌کند. فعال‌سازیِ فلگ، اجرای سوئیت، و merge همگی نیازمندِ رأیِ صریحِ A (دوکلیده) هستند. PLAN ≠ APPROVAL ≠ EXECUTION.

## ۷. قدم‌های بعدی (پیشنهادی — منتظرِ رأیِ A)
- [ ] تصمیمِ A روی R2 (بازنویسیِ `predicted_score` یا فقط ترتیب؟) و R1 (Thompson-seeded یا UCB1؟).
- [ ] نوشتنِ B1-B3 (characterization) — بدون اجرا.
- [ ] نوشتنِ دیفِ بخش ۲ روی شاخهٔ جدا — additive، default-off.
- [ ] نوشتنِ A1-A9 — بدون اجرا.
- [ ] پس از رأیِ «اجرا کن»: تک‌بار روشن‌کردنِ فلگ در محیطِ تست + اجرای سوئیت (لحظهٔ خروج از قرمز، با تأییدِ A).

---

## پیوست — نقشهٔ فایل/خط (handoff)
- `brain/acquisition.py:120-131` — `tag_performance()` (greedy mean + اشباع)
- `brain/acquisition.py:170-210` — `analyze()`؛ sortِ greedy در `:209`
- `brain/acquisition.py:212-241` — `plan_week()`؛ top-5 در `:219`/`:234`
- `brain/learning.py:134-152` — `ThompsonBandit.rank()`/`select()`
- `brain/learning.py:263-287` — `LearningBridge`/`recommend()`
- `brain/learning.py:49-53` — `normalize_reward()` (tanh)
- `orchestrator.py:54` — نقطهٔ ساختِ `AcquisitionBrain` (مصرف‌کنندهٔ زنده)
- `orchestrator.py:130` — مصرفِ `tag_performance()` برای consolidation (بیرونِ دامنه)
- `brain/test_learning.py` — الگوی assertهای آماری (seed + count)
