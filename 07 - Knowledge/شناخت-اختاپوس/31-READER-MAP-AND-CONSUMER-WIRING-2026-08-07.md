---
type: knowledge
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [octopus, reader-map, actuator-poor, consolidation, smallest-fix, deep-synth, wiring]
created: 2026-08-07
updated: 2026-08-07
created_by: agent
sources:
  - "Reader-map + consumer-wiring agent (Claude Code session), evidence-grounded on live _ops code, 2026-08-07"
  - "_ops/ARCHITECTURE-LAYERS-2026-07-27.md §0 «هر لایه باید لایهٔ زیرِ خودش را بخواند»"
---

# Reader Map + وصلهٔ مصرف‌کنندگان — ۲۰۲۶-۰۸-۰۷

> اصلِ بنیادینِ اختاپوس (ARCHITECTURE-LAYERS-2026-07-27.md §۰): **«هر لایه باید
> لایهٔ زیرِ خودش را بخواند، وگرنه فقط دارد دفتر پر می‌کند.»** بیماریِ مرکزی =
> sensor-rich / actuator-poor. این نوت Reader Mapِ ۷ producer را می‌سازد و سه وصلهٔ
> افزودنی برای وصل‌کردنِ DEAD-OUTPUTها اعمال می‌کند. ادامهٔ [[24-COGNITION-SYNC-AUDIT-2026-08-07]]
> و [[23-P1-P5-VERIFIED-AND-NEXT-MEGAPROMPT-2026-08-07]].

## مرحلهٔ ۱ — Reader Map (نقشهٔ کامل)

| # | producer | output file | consumer وجود دارد؟ | consumer تصمیم می‌گیرد؟ | رأی |
|---|---|---|---|---|---|
| ۱ | `neural/bcm.py::step` | `state/bcm-weights.json` + `state/bcm-signal-weights.json` | ✅ دو مصرف‌کننده | ✅ **(دو مسیرِ زنده)**: (الف) `neural_driver.py:122-142` وزن‌ها → `learned_pressure` → `protective_override:1822-1833` (پشتِ `LEARNED_APPLY`) → `organism.py:642`. (ب) `wiring._apply_bcm:1937-1960` → `latent_space.remove()` هرسِ ایندکسِ retrieval. | 🟢 **زنده** |
| ۲ | `neural/hebbian.py::observe/decay` | `neural/hebbian.json` | ✅ چند مصرف‌کننده | ❌ **همه display/observability**: `deep_think.py:168` (LLM context)، `cockpit_readmodel.py:227` (داشبورد)، `approval_channel.py:4466` (تبِ کابین)، `wiring._emit_hebbian_observation:1392` (رویدادِ spine با `trust=ADVISORY`). هیچ اکچوئیتوری. | 🔴 **DEAD-OUTPUT** |
| ۳ | `neural/consolidation.py::run` | `neural/consolidation.json` (۵۸۳ ردیف) | ✅ چند مصرف‌کننده | 🟡 **نیمه‌زنده**: `recall_reach()` → `recall-trend.jsonl` (metric)، `cockpit` (display). مقدارِ واقعی «یادآوری» فقط وقتی `similar_keys` غیرخالی باشد که نادر است. | 🟡 **تکرارِ ۹۵.۲٪** (وصلهٔ فازی پایین) |
| ۴ | `doctor/self_knowledge.py::deep_dive` | `doctor/self-knowledge-latest.json::deep_dive.smallest_fix` | ✅ دو مصرف‌کننده | ❌ **هر دو display**: `organ_dialogue.py:142` (کارتِ تلگرام)، `negotiate.py:130` (چت). هیچ ماژولی آن را به proposal تبدیل نمی‌کرد. | 🔴 **DEAD-OUTPUT** (وصله پایین) |
| ۵ | `cortex/improve.py::_deep_synth` | `cortex/deep-synth.jsonl` | ✅ خود-خوان | ✅ **(از قبل وصل شده — ۲۰۲۶-۰۷-۲۷)**: `_deep_synth:134` `_previous_synth(n=3)` را می‌خواند و در prompt به‌صورتِ `قبلاً_گفتی` می‌نشاند + یادداشتِ «حرفِ تکراری نزن». شاهد: ۵ سنتزِ اخیر میانگینِ شباهت ۰.۱۶ (تنوعِ خوب) و صریحاً می‌گویند «چرا هنوز انجام نشده (اعتراف، نه تکرار)». | 🟢 **زنده** (نیازی به وصله نبود — راستی‌آزمایی شد) |
| ۶ | `neural/latent_space.py::embed` | `state/latent-vectors.json` (۱۷۳ بردارِ R³²) | ✅ از طریق `similar_keys` | ❌ **advisory فقط**: `similar_keys` به‌عنوان metadata روی ConsolidatedInsight می‌نشیند ولی هیچ کدِ branch روی آن تصمیم نمی‌گیرد. `recall_reach()` metric-only است. | 🔴 **DEAD-OUTPUT** |
| ۷ | `cortex/self_model.py::run_and_persist` | `cortex/self-model.json` | ✅ چند مصرف‌کننده | ✅ **زنده**: `snapshot.py:159` کهنه بودن → blocker `self-model-not-fresh`؛ `compass.py:43` آمادگی را تنزل می‌دهد؛ `improve.py:465` auto-apply را مسدود می‌کند؛ `goal_action_bridge.py:133` authority را به pipeline می‌دهد. | 🟢 **زنده** |

### جمع‌بندی: ۳ DEAD-OUTPUT (Hebbian، latent-vectors، smallest_fix)، ۱ نیمه‌زندهٔ تکراری (consolidation)، ۳ زنده (BCM، deep_synth، self_model).

---

## مرحلهٔ ۲ — وصله‌ها (فقط مواردِ ایمن و ارزشمند)

### ✅ وصلهٔ ۲(الف) — consolidation dedup فازی (commit `f234d52`)

**قبل:** ۵۸۳ ردیف، ۲۸ امضای یکتا (۴.۸٪) — **۹۵.۲٪ تکرار**. شواهدِ زنده:
آخرین ۵ ردیف همگی «آگاهیِ میانگین: 0.73» با `repeats=1`. علت: `consolidation.py`
فقط امضای دقیق (sha256) را dedup می‌کرد و مسیرِ exact روی درختِ زنده خاموش بود؛
نوسانِ عددی امضای عین‌هم نمی‌سازد.

**بعد (با فلگ روشن):** مسیرِ dedup فازیِ افزودنی (شباهتِ زیررشته‌ای جاکاردی،
آستانهٔ ۰.۷) روی آخرین N ردیف. وصله **محافظه‌کارانه** است: تک‌تغییرِ عددی
(0.72 vs 0.73 → jaccard=0.5) تکرار شمرده نمی‌شود؛ فقط بازنویسیِ واقعی
(jaccard≥0.7) fold می‌شود. ردیفِ دارای بردارِ latent هرگز مقصد نمی‌شود.
- فلگ: `OCTOPUS_CONSOLIDATION_DEDUP_FUZZY` (خاموش = بایت‌به‌بایتِ امروز).
- knobها: `DEDUP_N` (پنجره، پیش‌فرض ۸)، `DEDUP_SIM` (آستانه، پیش‌فرض ۰.۷).
- گزارش: `ConsolidatedInsight.dedup_skipped` (None وقتی فلگ خاموش).
- تست: `test_consolidation_fuzzy_dedup.py` (۶ چک)، mutation-test قرمز تأییدشده.
- regression: `test_consolidation_compress_and_recall` + `distinguish` سبز.

### ✅ وصلهٔ ۲(ج) — smallest_fix → proposal (commit `0ead7d0`)

**قبل:** `deep_dive.smallest_fix` روی ۱۸ چرخه محاسبه شد، **۰ بار مصرف** — فقط
در کارتِ تلگرام/چت نمایش داده می‌شد.

**بعد:** `improve.generate_proposals()` حالا یک proposal با `source=smallest_fix`
می‌سازد: `auto_applicable=False`، `status=proposed` — یعنی فقط کارتِ تأیید،
نه اجرای خودکار. هم‌الگو با audit/doctor/synth.
- `gather_signals()` حالا `self-knowledge-latest.json::deep_dive.smallest_fix` را
  می‌خواند (fail-soft: نبود/خراب = '').
- $0 (فقط خواندن از فایلِ محلی، بدونِ LLM).
- تست: `test_improve_smallest_fix_proposal.py` (۷ چک)، mutation-test قرمز.
- regression: ۴ سوییتِ improve (۳۶ چک) سبز.

### ⊘ وصلهٔ ۲(ب) — improve._deep_synth خود-خوان: **نیازی نبود**

راستی‌آزمایی نشان داد این وصله از قبل انجام شده (۲۰۲۶-۰۷-۲۷). `_deep_synth:134`
`_previous_synth(n=3)` را می‌خواند و در prompt به‌صورتِ `قبلاً_گفتی` + یادداشتِ
هدایت‌کننده می‌نشاند. شاهدِ کارآمدی: ۵ سنتزِ اخیر میانگینِ شباهت ۰.۱۶ (نه تکرار)
و صریحاً «چرا هنوز انجام نشده» را می‌گویند. بازنویسی ممنوع — فقط مستندسازی.

### ⊘ وصله‌های وصل‌نشده (با دلیلِ روشن)

- **Hebbian → تصمیم:** DEAD-OUTPUT است ولی وصلهٔ ایمنی پیدا نشد. مصرف‌کنندنده‌اش
  واقعاً فقط نمایش‌اند. اکچوئیتور ساختن = بازطراحیِ واقعی (نه یک‌خطی)، خارجِ
  دامنهٔ «افزودنی + پشتِ فلگ». توصیه: اگر روزی قرار شد وصل شود، مسیرِ طبیعی
  `learned_pressure`ـِ BCM است که از همان واژگانِ ۸تایی می‌خواند — Hebbian می‌توانست
  همان فشار را تأیید/تقویت کند. رأیِ مالک لازم.
- **latent-vectors → تصمیم:** DEAD-OUTPUT ولی `similar_keys` ذاتاً advisory است.
  مصرفِ واقعی بازطراحیِ recall است، نه وصله.
