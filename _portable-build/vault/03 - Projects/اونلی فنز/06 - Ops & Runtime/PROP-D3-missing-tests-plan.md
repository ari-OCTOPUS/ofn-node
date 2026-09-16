---
type: report
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: idea
created: 2026-07-12
updated: 2026-07-12
created_by: agent
sources:
  - "[[03 - Projects/اونلی فنز/brain/BRAIN-BENCHMARK-2026-07-10]]"
  - "[[03 - Projects/اونلی فنز/PROJECT-F-BRAIN-SPEC]]"
tags: [project-f, testing, brain, ops, coverage, propose-only]
aliases: ["PROP-D3 Missing-Tests Plan", "نقشهٔ تست‌های گمشدهٔ مغز", "D3 Test Plan"]
---

# PROP-D3 — نقشهٔ تست‌های گمشدهٔ مغزِ Project-F (propose-only)

> **این یک پلن است، نه دستورِ اجرا. PLAN ≠ APPROVAL ≠ EXECUTION.**
> **گیتِ اجرا = RED.** هیچ تستی در این سند نوشته/اجرا نشده؛ صرفاً طراحی‌شده و اولویت‌بندی‌شده.
> نوشتنِ فایل‌های تست و اجرایشان نیاز به رأی صریحِ A دارد.

## خلاصهٔ اجرایی

**یافتهٔ هسته‌ای `[FACT]`:** در کلِ Project-F فقط **۳ فایلِ تست** commit شده‌اند —
`brain/test_learning.py` (۱۱ تست)، `langar/test_langar.py` (۹)، `studio/test_saba_studio.py` (۱۰) = ۳۰ تست.
**صفر تست** برای ۹ ماژولِ مغز/ارکستراسیون وجود دارد:

`project_f_brain.py` · `dual_brain.py` · `dual_brain_v3.py` · `acquisition.py` · `ab_tracker.py` · `content_engine.py` · `kpi_dashboard.py` · `lifecycle.py` · `orchestrator.py`.

**تناقضِ خطرناک `[FACT]`:** سندِ `brain/BRAIN-BENCHMARK-2026-07-10.md` (§۱، خطوط ۱۹–۲۳) این ماژول‌ها را «✅ تست‌شده» اعلام می‌کند
(`acquisition`, `ab_tracker`, `project_f_brain`, `dual_brain_v3`). ولی هیچ فایلِ تستِ متناظری در درخت نیست →
آن سبزها **ad-hoc/uncommitted** بوده‌اند و **بازتولیدپذیر/CI-checkable نیستند**. هدفِ اصلیِ این پلن:
تبدیلِ ادعاهای §۱ بنچمارک به تست‌های commit‌شده (regression-lock).

**اولویت (ریسک نزولی):** ماژول‌هایی که خطِ قرمزِ ایمنی را نگه می‌دارند اول
(دو-Guard، budget-cap fail-closed، kill/protective، PII/forbidden-scan، no-media)،
سپس صحتِ یادگیری/آمار، سپس تولیدِ محتوا/رندر.

---

## §۱ — وضعیتِ فعلیِ پوشش

| لایه | فایل | تست؟ | ادعای بنچمارک §۱ |
|---|---|---|---|
| Learning core | `brain/learning.py` | ✅ `test_learning.py` (۱۱) | ✅ صادق و commit‌شده |
| Langar (tg) | `langar/langar_bot.py` | ✅ `test_langar.py` (۹) | — |
| Studio (tg) | `studio/saba_studio.py` | ✅ `test_saba_studio.py` (۱۰) | — |
| Control-plane | `brain/project_f_brain.py` | ❌ **صفر** | «✅ tested» — بازتولیدناپذیر |
| Dual-brain v3 | `brain/dual_brain_v3.py` | ❌ **صفر** | «✅ import و اجرا» — بدون تست |
| Dual-brain v1 | `brain/dual_brain.py` | ❌ **صفر** | — (احتمالاً supersede‌شده) |
| Acquisition | `brain/acquisition.py` | ❌ **صفر** | «✅ nylon>oil، Saturday، restart» — بدون فایل |
| A/B tracker | `brain/ab_tracker.py` | ❌ **صفر** | «✅ significance» — بدون فایل |
| Content engine | `brain/content_engine.py` | ❌ **صفر** | — |
| KPI dashboard | `brain/kpi_dashboard.py` | ❌ **صفر** | — |
| Lifecycle | `brain/lifecycle.py` | ❌ **صفر** | — |
| Orchestrator | `orchestrator.py` | ❌ **صفر** | «✅ import و اجرا» — بدون تست |

---

## §۲ — قراردادِ تست (استخراج‌شده از ۳ فایلِ موجود)

الگویی که هر فایلِ جدید باید **مو‌به‌مو** تقلید کند (شواهد با file:line):

1. **stdlib `unittest` تنها.** بدون pytest/mock خارجی. سرآیند: `from __future__ import annotations` — `test_learning.py:3`, `test_langar.py:3`.
2. **importِ ساده و کنارِ ماژول:** `import learning as L` (`test_learning.py:8`)، `import saba_studio as S` (`test_saba_studio.py:9`). → **فایلِ تست کنارِ ماژول** و اجرا با start-dir همان پوشه.
3. **هرمتیک، $0، آفلاین، deterministic:** tempdir در setUp، بازگردانی در tearDown. دو الگوی مرجع:
   - **تزریقِ مسیر از سازنده** (وقتی ماژول `data_path`/`config_path` می‌گیرد): `L.ThompsonBandit(data_path=Path(mkdtemp())/'b.json', seed=1)` — `test_learning.py:12-14`.
   - **بازنویسیِ گلوبالِ ماژول در setUp** (وقتی مسیر ماژول-گلوبال است): ذخیرهٔ `self._orig = (L.KILL_FILE, ...)`، هدایت به tmp، restore در tearDown — `test_langar.py:16-32` و `test_saba_studio.py:13-41`.
4. **fakeهای سبک به‌جای وابستگیِ واقعی:** `http_get`/`http_post` تزریقی (`test_langar.py:26-27`)، `FakeStudio` داخلِ متد (`test_saba_studio.py:76-81`)، `studio=None` برای مسیرِ fallback (`test_saba_studio.py:36`).
5. **تستِ خطوطِ قرمز به‌صورتِ صریح:** kill-switch (`test_langar.py:55`)، fail-closed (`:73`)، صفر media با اسکنِ `dir(bot)` (`test_langar.py:93`, `test_saba_studio.py:125`)، redactionِ PII (`test_langar.py:35`).
6. کامنت/داک‌استرینگِ فارسی، نامِ متد `test_*`، پایان با `unittest.main(verbosity=2)`.

### هارنسِ اجرا (پیشنهادی)

```bash
# واحد (brain/) — importهای ساده وقتی start-dir = brain باشد resolve می‌شوند:
python -m unittest discover -s brain -p "test_*.py" -v
# (test_learning.py موجود هم خودکار برداشته می‌شود؛ رگرسیون حفظ)

# یکپارچهٔ ارکستر — جداگانه، gated (نیازمندِ درختِ _ops/neural؛ §۵):
python -m unittest test_orchestrator -v   # از ریشهٔ Project-F
```

### گاچاهای ایزولاسیون (اجباری — وگرنه تست‌ها درختِ واقعی را آلوده می‌کنند) `[FACT]`

- **`project_f_brain._ARCHIVE_PATH`** در زمانِ import محاسبه می‌شود (`project_f_brain.py:33`) از `PF_BRAIN_DIR` یا کنارِ ماژول. توابعِ `_load_archive`/`_save_archive` این گلوبال را **در زمانِ فراخوانی** می‌خوانند (`:94`,`:102`) → **الگوی بازنویسیِ گلوبال در setUp کار می‌کند**. هر تستی که `ProjectFBrain()` می‌سازد **باید** اول `PB._ARCHIVE_PATH = tmp/'archive.json'` بگذارد؛ وگرنه `brain/archive.json` واقعی نوشته می‌شود.
- **`acquisition` / `ab_tracker` / `lifecycle`**: پیش‌فرضِ مسیر = کنارِ ماژول اگر `data_path` ندهی (`acquisition.py:69-71`, `ab_tracker.py:9`, `lifecycle.py:9`). **همیشه `data_path=tmp/...` پاس بده** (الگوی bandit).
- **`content_engine`**: RNG ماژول-گلوبال نیست ولی نمونه‌ای `random.Random(42)` است (`content_engine.py:47`) که در طولِ عمرِ instance پیش می‌رود → برای determinism، **در هر تست یک `ContentEngine` تازه** بساز.
- **`orchestrator`**: state از `_BRAIN_STATE = PF_BRAIN_DIR or _HERE/brain` (`orchestrator.py:28`) در زمانِ import؛ پارامترِ سازندهٔ `data_dir` فقط بخشی را می‌پوشاند. برای ایزولاسیونِ کامل، `os.environ["PF_BRAIN_DIR"]=tmp` را **قبل از `import orchestrator`** ست کن.

---

## §۳ — ماتریسِ ریسک (اولویتِ نوشتن)

| رتبه | ماژول | رفتارهای safety-critical | نوع | Gate |
|---|---|---|---|---|
| **P0-1** | `project_f_brain.py` | دو-Guard (drop سخت)، budget ۲٪ fail-closed، routing tiered (قیمت→A)، approval-gated archive | unit خالص | GREEN-able |
| **P0-2** | `orchestrator.py` | protective mode (pain>0.7 → فقط heartbeat)، throttle، `advisory_only`، تزریقِ checks کاملاً compliant | **integration** | **RED (نیازمندِ _ops/neural)** |
| **P0-3** | `dual_brain_v3.py` | scanِ FORBIDDEN_TERMS (PII/payment)، `_checks_pass`→blocked، `human_gated` همیشه، no-media | unit خالص | GREEN-able |
| **P1-4** | `acquisition.py` | propose-only (بدون auto-DM/follow/mass)، learn-from-aggregate (بدون PII)، restart-safe | unit خالص | GREEN-able |
| **P1-5** | `ab_tracker.py` | صحتِ آماری (برندهٔ کاذب)، آستانهٔ significance، persist | unit خالص | GREEN-able |
| **P1-6** | `lifecycle.py` | aggregate/صفر-PII، پیش‌بینیِ churn، persist | unit خالص | GREEN-able |
| **P2-7** | `dual_brain.py` | Guard parity (احتمالاً supersede‌شده — §۶) | unit خالص | GREEN-able |
| **P2-8** | `content_engine.py` | صفر LLM/PII، determinism | unit خالص | GREEN-able |
| **P2-9** | `kpi_dashboard.py` | صفر-PII / escaping (no-XSS/leak) | unit خالص | GREEN-able |

منطقِ رتبه‌بندی: **blast-radius اگر رفتار بی‌صدا خراب شود.** P0 = نقض یعنی پول/PII/انتشارِ کنترل‌نشده. P1 = یادگیریِ غلط یا نشتِ aggregate. P2 = خطای تولید/رندر با شعاعِ کوچک.

---

## §۴ — پلنِ per-module (نام + قصدِ یک‌خطی)

### P0-1 · `brain/test_project_f_brain.py` — کنترل‌پلین (unit خالص)
مرجع: guards `:152-174`، `process_draft` `:177-210`، `spend` `:233-239`، `archive` `:213-230`.

**safety-critical**
| متد | قصد |
|---|---|
| `test_compliance_guard_drops_on_missing_rule` | نبودِ هر یک از ۶ COMPLIANCE_RULE → `status="dropped"` (`:155-159`) |
| `test_ethics_guard_drops_on_missing_rule` | نبودِ هر ETHICS_RULE → drop (`:167-171`) |
| `test_both_guards_required_for_pass` | فقط با هر ۱۲ قاعدهٔ True هر دو flag سبز |
| `test_budget_fail_closed_over_cap` | `spend(600)` بعد از `spend(1500)` → False و budget بدون تغییر (`:235-238`) |
| `test_budget_boundary_exact_cap_allowed` | مرزِ دقیق: projected==۲۰۰۰ مجاز (شرطِ `>`) |
| `test_hitl_price_routes_to_ari_highrisk` | proposalِ `price` (high) → `route="ari"`, `status="submitted"` (`:202-204`) |
| `test_hitl_lowrisk_routes_to_saba` | strategy/copy/schedule → `route="saba"`, `status="gated"` (`:205-207`) |
| `test_hitl_dropped_when_guards_fail` | checks خالی → همه `route="dropped"` (`:200-201`) |
| `test_archive_learns_only_from_approved` | `learned` فقط برای `approved`/`published` (`:219`, `learned_entries` `:228-230`) |
| `test_archive_persists_across_restart` | بازنویسیِ `PB._ARCHIVE_PATH`→tmp؛ instance دوم آرشیو را می‌خواند (`:91-108`) |

**functional**
| `test_pricer_tiers` | low/mid/premium بر اساسِ base×content×time (`:118-128`) |
| `test_process_draft_shape` | خروجی: کلیدهای `proposals`/`routed_to`/`guards_passed` |

---

### P0-2 · `test_orchestrator.py` — حلقهٔ زنده (**integration، gated RED**)
مرجع: imports `:17-25`، sys.path `:10-15`، `tick` `:68-153`، protective `:86-90`، throttle `:93,103`، consolidation `:128-137`، `status` `:163-169`. جزئیاتِ گیت در §۵.

**safety-critical**
| متد | قصد |
|---|---|
| `test_advisory_only_always_true` | هر `TickResult.advisory_only` == True (`:44`) |
| `test_protective_mode_on_high_pain` | ورودیِ عصبی که pain>0.7 بدهد → `mode="protective"` و خروجِ زودهنگام (`:86-90`) `[OPEN]` قرارداد ورودی |
| `test_protective_returns_no_messages` | در protective، `messages`/`thoughts` خالی |
| `test_throttle_suppresses_thinking` | `throttle_brain=True` → بدون thoughts/messages (`:103-112`) |
| `test_orchestrator_passes_full_compliant_checks` | ارکستر همیشه ۱۲ قاعده را True می‌فرستد → brain هرگز از این مسیر blocked نمی‌شود (`:104-105`) |

**functional**
| `test_tick_increments_beat` | هر tick، `beat`++ (`:74`) |
| `test_consolidation_runs_every_ten_ticks` | فقط در `beat%10==0` (`:128`) |
| `test_status_keys` | کلیدهای `status()` (`:163-169`) |
| `test_injected_fakes_used` | `studio`/`brain`/`acquisition` تزریق‌پذیرند (`:50-54`) — با fake |

---

### P0-3 · `brain/test_dual_brain_v3.py` — تولیدِ متنِ بیرونی (unit خالص)
مرجع: FORBIDDEN_TERMS `:33-37`، `_guard_text` `:69-72`، `_checks_pass` `:75-76`، `process_all` blocked `:245-247`، `_safe` `:274-276`، `think_and_communicate` `:389-417`، `human_gated` `:65`.

**safety-critical**
| متد | قصد |
|---|---|
| `test_checks_pass_requires_all_rules` | `_checks_pass` فقط با همهٔ compliance+ethics True (`:75-76`) |
| `test_process_all_blocked_on_guard_fail` | checks ناقص → تنها `[Thought(kind="blocked")]` (`:245-247`) |
| `test_guard_detects_forbidden_terms` | `_guard_text("... sydney/paypal ...")` → violations ناتهی (`:69-72`) |
| `test_safe_blanks_forbidden_text` | `_safe` متنِ آلوده را با `[BLOCKED ...]` جایگزین می‌کند (`:274-276`) |
| `test_no_forbidden_terms_in_default_outputs` | اجرای کاملِ `think_and_communicate` با checksِ کامل → هر `message.text` عاری از FORBIDDEN_TERMS |
| `test_all_messages_human_gated` | همهٔ Messageها `human_gated=True` (`:65`) |
| `test_no_media_methods` | اسکنِ `dir()` — بدون photo/video/document (الگوی `test_langar.py:93`) |

**functional**
| `test_process_all_returns_ten_thoughts` | ۱۰ ساب‌عامل (`:248-259`) |
| `test_pricer_learns_from_approved_history` | historicalِ approved → base به میانگین کشیده می‌شود (`:104-108`) |
| `test_pricer_tier_bounds` | مرزهای tier (low<12، premium>20) |

---

### P1-4 · `brain/test_acquisition.py` — یادگیرندهٔ جذب (unit خالص، `data_path` تزریقی)
مرجع: `tag_performance` `:120-131`، `best_time` `:133-146`، `learning_confidence` `:157-160`، `analyze` `:170-210`، `plan_week` `:212-241`، `feedback_loop` `:260-266`، خطوطِ قرمزِ سرآیند `:15-16`.

**safety-critical**
| متد | قصد |
|---|---|
| `test_propose_only_no_auto_targeting_methods` | هیچ متدی با dm/follow/subscribe/mass/target در نامش (اسکنِ `dir`) — خطِ قرمزِ «no mass-anything» |
| `test_records_no_pii_fields` | `record_post_result` فقط aggregate می‌نویسد (tag/platform/metrics)، بدون فیلدِ فرد (`:94-98`) |

**functional (بازتولیدِ ادعای بنچمارک §۱)**
| `test_tag_performance_ranks_by_real_data` | nylon>oil از دادهٔ واقعی (`:120-131`) — قفلِ ادعای بنچمارک |
| `test_best_time_learns_best_day` | بهترین روز از داده (Saturday در نبودِ داده) (`:133-146`) |
| `test_learning_confidence_scales_with_n` | `min(1, n/20)` (`:157-160`) |
| `test_analyze_sorted_by_predicted_score` | خروجی نزولی بر اساسِ `predicted_score` (`:209`) |
| `test_analyze_confirm_bonus_for_own_and_competitor` | tagِ مشترک → bonus (`:199-206`) |
| `test_plan_week_top5_and_risk_notes` | ۵ اولویت + risk-note وقتی confidence<0.3 (`:228-231`) |
| `test_persistence_across_restart` | `feedback_loop` → instanceِ دوم با همان `data_path` داده را می‌خواند (قفلِ ادعای restart) |
| `test_cold_start_paths_safe` | حافظهٔ خالی → dictهای خالی، بدون crash (`:124`,`:135`,`:150`) |

---

### P1-5 · `brain/test_ab_tracker.py` — A/B آماری (unit خالص، `data_path` تزریقی)
مرجع: `create_test` `:46-53`، `record_result` `:55-61`، `analyze` `:63-81`، `auto_winner` `:83-91`، آستانه `:11`.

| متد | قصد |
|---|---|
| `test_significance_threshold_boundary` | relative دقیقاً ۰٫۱۵ → significant (`>=`, `:78`) — مرزِ برندهٔ کاذب |
| `test_below_threshold_inconclusive` | زیرِ آستانه → `significant=False` |
| `test_analyze_detects_winner_a` | sa>sb → `winner="a"` (`:77`) |
| `test_analyze_no_data` | نبودِ نتیجهٔ یک variant → `{"status":"no_data"}` (`:68`) |
| `test_auto_winner_sets_status_and_persists` | significant → `status=won_x`, `winner=x`, ذخیره (`:85-90`) |
| `test_auto_winner_none_when_insignificant` | زیرِ آستانه → None و بدونِ تغییرِ status |
| `test_create_test_id_format` | `AB-001` افزایشی (`:48`) |
| `test_record_unknown_test_is_noop` | `test_id` ناشناخته → بی‌اثر (`:57`) |
| `test_persistence_across_restart` | trackerِ دوم با همان `data_path` تست‌ها را می‌خواند |

---

### P1-6 · `brain/test_lifecycle.py` — چرخهٔ حیات (unit خالص، `data_path` تزریقی)
مرجع: `track` `:42-47`، `churn_rate` `:49-55`، `growth_rate` `:57-61`، `predict_at_risk` `:63-73`، `win_back_strategy` `:75-85`، `PeriodRecord` `:14-21`.

| متد | قصد |
|---|---|
| `test_aggregate_only_no_pii` | `PeriodRecord` فقط شمارنده‌ها دارد، هیچ فیلدِ فرد — خطِ قرمزِ صفر-PII |
| `test_churn_rate_needs_two_periods` | <۲ دوره → 0.0 (`:51`) |
| `test_churn_rate_from_recent` | نسبتِ churn روی ۴ دورهٔ اخیر (`:52-55`) |
| `test_growth_rate` | (last-prev)/prev (`:59-61`) |
| `test_predict_at_risk_trend_classification` | declining/stagnant/growing طبق growth (`:71`) |
| `test_predict_at_risk_no_data` | <۲ دوره → `status="no_data"` (`:66`) |
| `test_win_back_branches` | churn>0.3 و growth<0 شاخه‌های جداگانه (`:79-82`) |
| `test_persistence_across_restart` | `track` → instanceِ دوم history را می‌خواند |

---

### P2-7 · `brain/test_dual_brain.py` — نسخهٔ v1 (unit خالص؛ **کاندیدِ archive — §۶**)
مرجع: `process` blocked `:166-174`، `_guard_text`/`caption` `:197-216`، `report_for_ari` `:258-272`.
تستِ حداقلی برای parity تا وقتی ماژول زنده است:
| `test_thinking_blocked_on_guard_fail` | checks ناقص → `[blocked]` (`:171-174`) |
| `test_comm_guard_blocks_forbidden` | متنِ آلوده → `[BLOCKED by Ethics-Guard]` (`:213-214`) |
| `test_all_messages_human_gated` | `human_gated=True` (`:44`) |
| `test_no_media_methods` | صفر media |
| `test_process_and_communicate_shape` | کلیدهای `thoughts`/`messages`/`blocked` (`:316-317`) |

---

### P2-8 · `brain/test_content_engine.py` — تولیدِ ایده (unit خالص، deterministic)
مرجع: `generate_ideas` `:49-65`، `script_from_idea` `:67-76`، `batch_plan` `:78-81`، `ab_pairs` `:88-92`، `ideas_html` `:94-98`، SEASONAL `:12-15`، seed `:47`.

| `test_generate_ideas_deterministic` | ContentEngineِ تازه با seed 42 → عناوین/idهای پایدار (صفر LLM) |
| `test_generate_ideas_count` | پارامترِ `count` رعایت می‌شود |
| `test_ideas_include_season_tag` | هر ایده tagِ فصل را دارد (`:63`) |
| `test_unknown_season_falls_back_summer` | فصلِ ناشناخته → SEASONAL summer (`:52`) |
| `test_script_has_three_scenes` | ۳ صحنه (`:71`) |
| `test_batch_plan_session_math` | `ceil(total/max_session_min)` (`:80`) |
| `test_ab_pairs_pairing` | n ایده → `floor(n/2)` جفت (`:90`) |
| `test_ideas_html_caps_at_ten` | HTML حداکثر ۱۰ ردیف (`:96`) |

---

### P2-9 · `brain/test_kpi_dashboard.py` — رندرِ داشبورد (unit خالص، بدون I/O)
مرجع: `render` `:10-75`، escape‌ها `:29`(tag)،`:70`(insight)،`:73`(season)؛ **unescaped**: mode/color `:64`.

| متد | قصد |
|---|---|
| `test_escapes_tag_and_insight` | تزریقِ `"<script>"` در tag/insight → escape‌شده (`:29`,`:70`) — خطِ قرمزِ no-XSS/leak |
| `test_no_raw_pii_injection` `[SPEC]` | مستندسازیِ گاف: `mode`/`color` بدونِ `html.escape` رندر می‌شوند (`:64`) — sev پایین (منبعِ داخلی)، پیشنهادِ escape |
| `test_render_returns_html` | خروجی رشتهٔ HTML معتبر (`<!doctype`) |
| `test_funnel_math` | درصدهای sub/vis و ppv/subs (`:22`) |
| `test_tag_bars_capped_5` | حداکثر ۵ بار (`:27`) |
| `test_empty_inputs_defaults` | همهٔ ورودی‌ها None → بدون crash، پیش‌فرضِ 100/5/1 (`:21`) |

---

## §۵ — ارکستر: چرا Gate = RED و چه چیزی integration است `[FACT]`

`orchestrator.py:12-25` در زمانِ import مسیرهای `brain/`, `studio/`, `_VAULT/_ops/neural`, `_VAULT/_ops` را به `sys.path` تزریق و از آن‌ها import می‌کند:
`neural_driver`, `hebbian`, `consolidation`, `sprint`, `hooks`, `circadian`, `content_studio`. **این وابستگی‌ها injectable نیستند** —
فقط `studio`/`brain`/`acquisition` از سازنده تزریق‌پذیرند (`:50-54`)؛ `NeuralDriver()`/`HebbianAssociator(...)`/... hard-wired‌اند (`:56-62`).

- درختِ `_ops/neural` روی این ماشین موجود است `[FACT]` (`neural_driver.py`, `hebbian.py`, `consolidation.py`, `circadian.py`, `hooks.py`, `sprint.py` تأیید شد؛ `evaluate(self, beat, rhythm, sensory, ...)` در `neural_driver.py:65`).
- **علتِ RED:** (۱) اجرا در worktree ممکن است مسیرِ `_VAULT` را جای دیگری ببرد؛ باید importپذیری اول تأیید شود. (۲) قراردادِ ورودیِ لازم برای رساندنِ pain>0.7 (کدام `rhythm`/`sensory`/`spectral`/`budget`) هنوز pin نشده → **`[OPEN]`: قبل از نوشتنِ `test_protective_mode_on_high_pain` باید `neural_driver.evaluate` خوانده شود** تا ورودیِ درست ساخته شود (نه mockِ حدسی — درسِ «pipeline را تست کن، نه unit را»).

**دو حالتِ تست (هر دو integration، gated):**
- **A) نیمه‌ایزوله:** fake برای `studio`/`brain`/`acquisition` + واقعیِ `_ops/neural`. سریع‌تر، ولی هنوز نیازمندِ درختِ `_ops`.
- **B) تمام-واقعی:** همه واقعی؛ نزدیک‌ترین به production، کندتر.

**پیشنهادِ کد `[OPEN]` (propose-only، نه تست):** افزودنِ پارامترهای سازنده برای تزریقِ `neural`/`hebbian`/`consolidation` تا unit-isolationِ واقعی ممکن شود. این یک تغییرِ کد است و نیاز به رأی A دارد — خارج از دامنهٔ این سند.

---

## §۶ — یافته‌های جانبی (propose-only، حین طراحی دیده شد)

- **تکراری/مرده `[OPEN]`:** `orchestrator.py:17` از `dual_brain_v3` import می‌کند، نه `dual_brain`. `dual_brain.py` ظاهراً به هیچ مسیرِ زنده‌ای وصل نیست → کاندیدِ `_Archive` یا حذفِ تست‌محور. **رأی A لازم** (قاعدهٔ «هرگز حذف نکن؛ منتقل کن»).
- **ارکستر kill-switchِ فایلی ندارد `[OPEN]`:** برخلافِ `langar` (KILL) و `saba_studio` (HALT)، `orchestrator.tick` هیچ فایلِ kill/HALT را چک نمی‌کند؛ تنها ایمنی‌اش protective modeِ درونی (pain>0.7) است. آیا باید به kill-switchِ `_ops` وصل شود؟
- **escape ناقصِ داشبورد `[SPEC]`:** `kpi_dashboard.py:64` — `mode`/`color` بدونِ `html.escape`. sev پایین (منبعِ داخلیِ neural snapshot)، ولی خطِ «صفر-PII» ایجابِ escapeِ کامل می‌کند.

---

## §۷ — ترتیب و برآورد

**ترتیبِ نوشتن (ریسک نزولی):** P0-1 → P0-3 → P1-4 → P1-5 → P1-6 → P2-8 → P2-9 → P2-7، و **جداگانه/آخر** P0-2 (ارکستر، پس از رفعِ `[OPEN]`های §۵).

**برآوردِ تعداد `[EST]`:** ~۸۳ تستِ جدید (pfb ۱۲ · v3 ۱۰ · acq ۱۱ · ab ۹ · lifecycle ۸ · content ۸ · kpi ۶ · dual_v1 ۷ · orch ۹) → سوئیتِ کل ~۱۱۳ (۳۰ موجود + ۸۳).

**هدفِ regression-lock:** با commitِ P0-1/P0-3/P1-4/P1-5 ادعاهای `BRAIN-BENCHMARK §۱` (خطوط ۱۹–۲۳) بازتولیدپذیر و CI-checkable می‌شوند؛ سبزِ ad-hoc به سبزِ نگه‌داری‌شده تبدیل می‌شود.

**سؤالاتِ باز برای A:**
1. آیا `dual_brain.py` supersede شده و به `_Archive` برود (پس تست‌اش لازم نیست)؟
2. آیا ارکستر باید به kill-switchِ `_ops` وصل شود (پیش از نوشتنِ تستِ ایمنیِ آن)؟
3. تزریق‌پذیر کردنِ وابستگی‌های عصبیِ ارکستر مجاز است (تا unit-isolation ممکن شود)؟ — تغییرِ کد، خارج از این سند.

*همهٔ محتوا propose-only و ایزوله در Project-F؛ هیچ اکشنِ بیرونی؛ اجرا پشتِ GATE = RED.*
