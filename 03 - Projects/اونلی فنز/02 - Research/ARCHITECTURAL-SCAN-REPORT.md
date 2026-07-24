# گزارش اسکن معماری — Project-F (اونلی فنز)

> **تاریخ اسکن:** 2026-07-12  
> **مسیر پروژه:** `F:/backup/03 - Projects/اونلی فنز/`  
> **نسخه گزارش:** 1.0  
> **حجم کد:** ~2,100 خط پایتون + ۲۰۸ خط JSON  
> **تست‌ها:** ۲۹/۲۹ سبز (۱۱ brain + ۸ langar + ۱۰ studio) + ۲۲/۲۲ acquisition pipeline

---

## فهرست

1. [خلاصهٔ اجرایی](#1-خلاصهٔ-اجرایی)
2. [نمای کلی معماری](#2-نمای-کلی-معماری)
3. [لایهٔ مغز — brain/](#3-لایٔه-مغز--brain)
4. [لایهٔ استودیو — studio/](#4-لایٔه-استودیو--studio)
5. [لایهٔ کاکپیت — langar/](#5-لایٔه-کاکپیت--langar)
6. [ارکستراتور — orchestrator.py](#6-ارکستراتور--orchestratorpy)
7. [انسان در حلقه (HITL)](#7-انسان-در-حلقه-hitl)
8. [اتصال به اختاپوس](#8-اتصال-به-اختاپوس)
9. [قراردادها و مانیفست](#9-قراردادها-و-مانیفست)
10. [سوئیچ‌های ایمنی و kill-switch](#10-سوئیچهای-ایمنی-و-kill-switch)
11. [بستهٔ تست](#11-بستٔ-تست)
12. [کدها و فایل‌ها](#12-کدها-و-فایلها)
13. [شکاف‌ها و ریسک‌ها](#13-شکافها-و-ریسکها)
14. [توصیه‌ها](#14-توصیهها)

---

## 1. خلاصهٔ اجرایی

**Project-F** یک creator brand faceless (فقط پا) با مدل ۵۰/۵۰ دو نفره (A=Operator, C=Creator) در فاز validation است. سیستم مولتی‌ایجنتی آن شامل:

- **DualBrainV3** — ۱۰ ساب‌عامل تفکر + ۷ نوع خروجی ارتباطی
- **ProjectFBrain** — کنترل‌پلین + ۷ زیرعامل (Strategist, Pricer, Scheduler, Copywriter, Analyst, Compliance-Guard, Ethics-Guard)
- **Acquisition Pipeline** — propose-only: draft → صف → approve → آمادهٔ پست دستی
- **ThompsonBandit** — یادگیری contextual با اکتشاف (جایگزین greedy)
- **Saba Studio** — رابط تلگرامی creator (صبا)
- **Langar Cockpit** — رابط تلگرامی operator (آری)

**وضعیت:** ۲۹/۲۹ تست سبز. ۲۲/۲۲ تست acquisition pipeline سبز. **GATE 0 باز** — هیچ execution outward تا بسته شدن.

---

## 2. نمای کلی معماری

```text
┌────────────────────────────────────────────────────────────────────────────┐
│                         OCTOPUS (Architect)                                 │
│                              │                                              │
│  ┌───────────────────────────▼──────────────────────────────────────────┐   │
│  │                    PFOrchestrator (orchestrator.py)                   │   │
│  │  tick() → neural snapshot → think → comm → hebbian → consolidation   │   │
│  │  λ_persist<0 · advisory-only · protective mode if pain>0.7           │   │
│  └──────────┬─────────────────┬─────────────────┬──────────────────────┘   │
│             │                 │                 │                          │
│  ┌──────────▼─────┐  ┌────────▼──────┐  ┌──────▼───────┐                  │
│  │ brain/         │  │ studio/       │  │ langar/      │                  │
│  │                │  │               │  │              │                  │
│  │ DualBrainV3    │  │ SabaStudio    │  │ LangarBot    │                  │
│  │ (10 think +    │  │ (Telegram UI  │  │ (Telegram    │                  │
│  │  7 comm)       │  │  for Creator) │  │  Cockpit     │                  │
│  │                │  │               │  │  for Ari)    │                  │
│  │ ProjectFBrain  │◄─┤ ContentStudio │  │              │                  │
│  │ (7 sub-agents) │  │ (engine)      │  │ OpsecGuard   │                  │
│  │                │  │               │  │ CostMeter    │                  │
│  │ Acquisition    │  │ affirm.py     │  │ SelfModel    │                  │
│  │ ThompsonBandit │  │ (warm layer)  │  │ UpgradeEngine│                  │
│  │ LearningBridge │  │               │  │              │                  │
│  └────────────────┘  └───────────────┘  └──────────────┘                  │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │  File Handoffs (JSON):                                              │  │
│  │  studio/drafts.json → studio/for_saba.json → studio/to_ari.json    │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. لایهٔ مغز — brain/

### 3.1 DualBrainV3 (نسخهٔ عمیق)

**ThinkingBrain** — ۱۰ ساب‌عامل تخصصی:

| # | ساب‌عامل | خروجی | confidence |
|---|---|---|---|
| 1 | Strategist | wall/PPV split | 0.7 |
| 2 | Pricer | contextual bandit (base×content×time) | 0.6 |
| 3 | Scheduler | best time per platform | 0.7 |
| 4 | RiskAnalyzer | partner-burnout, scope-creep, ToS | 0.5 |
| 5 | Segmenter | VIP/regular/lurker策略 | 0.5 |
| 6 | CompetitorIntel | hot tags (aggregate) | 0.6 |
| 7 | TrendForecaster | seasonal trends | 0.4 |
| 8 | RetentionStrategist | churn actions | 0.5 |
| 9 | ContentOptimizer | best/worst tag | 0.1–0.8 |
| 10 | FunnelAnalyst | visitor→sub→PPV rates | 0.6 |

**CommBrain** — ۷ نوع خروجی:
- caption, dm_draft, brief_for_saba, report_for_ari, trend_note, retention_dm, ab_announcement

**گاردهای اخلاقی:**
- `_guard_text()` — بررسی FORBIDDEN_TERMS (persian, sydney, iran, real name, paypal, crypto, …)
- `_checks_pass()` — COMPLIANCE_RULES + ETHICS_RULES
- `human_gated=True` روی همهٔ Messageها

### 3.2 ProjectFBrain (control-plane + ۷ زیرعامل)

| زیرعامل | وظیفه | risk_level |
|---|---|---|
| Strategist | نردبان ارزش (wall vs PPV) | low |
| Pricer | contextual bandit سه‌لایه | **high** → آری |
| Scheduler | زمان بهینه | low |
| Copywriter | کپشن/عنوان draft | low |
| Analyst | KPI تجمیعی (صفر PII) | low |
| Compliance-Guard | گیت سخت (faceless, feet_only, …) | drop if fail |
| Ethics-Guard | ضد dark-pattern, محدودهٔ صبا مقدم | drop if fail |

**HITL flow (tiered):**
1. صبا draft ثبت → ۲. Guard گیت → ۳. low-risk → صبا / high-risk → آری → ۴. verdict → archive

### 3.3 AcquisitionBrain

**هوشمند یافتن مشتری (propose-only):**
- `analyze()` → ContentInsight از دادهٔ خودی + رقبا + فصلی
- `plan_week()` → WeekPlan (۵ اولویت + زمان‌بندی + A/B)
- `suggest_next_action()` → توصیهٔ قدم بعدی
- `feedback_loop(tag, platform, upvotes, comments, unlocks, day)` → یادگیری

**AcquisitionMemory:**
- persistence: JSON file (restart-safe)
- داده‌های خودی (`post_result`) + رقبا (`competitor`) + سیگنال (`signal`)
- `tag_performance()` → normalized score 0..1
- `best_time()` → از دادهٔ واقعی

### 3.4 ThompsonBandit (learning.py)

**چرا ساخته شد:** مغز قبلی (acquisition.analyze) از **میانگین خام (greedy)** استفاده می‌کرد — قفل روی برندهٔ نویزی اولیه.

**ویژگی‌ها:**
- Thompson sampling (Beta-Bernoulli) با `random.betavariate`
- recency-decay با نیمه‌عمر ۲۱ روز
- explore floor=۵٪، cap=۴۰٪
- min-pull=۳ (هیچ سبکی نادیده نمی‌ماند)
- approval-gated: فقط `approved=True` وارد یادگیری
- `normalize_reward()` با `tanh` (نه `min(1,…)`)

**UCB1:** جایگزین قطعی برای reproducibility.

**Eval harness:**
- `regret_eval()` — شبیه‌سازی محیط غیرایستا با shift
- `regret_eval_avg()` — میانگین روی ۴۰ seed

### 3.5 AcquisitionPipeline

**جریان propose-only:**
```
auto_plan(n) → drafted → approve(item_id, actor="owner") → approved
→ finalize(item_id) → ready (payload برای پست دستی انسان)
```

**copy guard (rule #6 / CLAIMS-REGISTER):**
- banned: "اونلی", "onlyfans", "fansly", "صبا", "sydney", "سیدنی", "persian", "iranian", …
- flagged draft → هرگز persist نمی‌شود
- finalize belt-and-suspenders: گارد نهایی روی payload

**هیچ متد post/send/dm/publish/pay وجود ندارد.**

---

## 4. لایهٔ استودیو — studio/

### 4.1 SabaStudio (saba_studio.py)

**رابط تلگرامی Creator (صبا):**
- منوی سه‌سطحی inline keyboard
- HTML غنی
- conversation state سبک (per-chat dict)
- صفر رسانه/هویت/PII

**صفحات:**
- 🏠 home (pending drafts, capacity, inbox)
- 📤 ثبت درفت (title → self-cert checkbox → ثبت)
- 📋 drafts_page
- 🌟 today_page (تمرکز هفته + ایده)
- 🗓 cal_page (تقویم)
- 🔎 trend_page
- 💡 ppv_page
- 📈 stats_page
- 🫶 cap_page (ظرفیت هفتگی)
- 📬 inbox_page (پیام‌های آری)
- ✋ scope_page (محدودهٔ صبا)
- 🔒 rules_page
- 🧠 brief_page

**self-cert اجباری:**
- faceless ✅ · feet_only ✅ · no_explicit ✅ · over_18 ✅

**handoff دوطرفه:**
- صبا → آری: `studio/to_ari.json`
- آری → صبا: `studio/for_saba.json`

### 4.2 ContentStudio (content_studio.py)

**موتور مشترک:**
- `submit_draft(title, self_cert)` → DraftSubmission with ID
- persistence: `drafts.json` (atomic write)
- PPV plan از `config.json`
- analytics از `config.json`

### 4.3 affirm.py

**لایهٔ پیام گرم/تحسین‌گر (pure render):**
- `welcome()`, `spotlight(sets)`, `streak_msg(days)`, `thanks(drafts)`
- `celebrate_milestone(kind)`
- content-free، بدون فشار/دستکاری

---

## 5. لایهٔ کاکپیت — langar/

### 5.1 LangarBot (langar_bot.py)

**رابط تلگرامی Operator (آری) — ⚓ کاکپیت خودآگاه:**

**OpsecGuard:**
- `clean(text)` → redact نام‌ها (صبا→C، آری→A)، شهرها (Sydney→⟦geo⟧)، مسیرها
- blocklist قابل پیکربندی
- fail-closed: config خراب → سخت‌گیرترین حالت

**CostMeter:**
- سقف ماهانه AUD (پیش‌فرض ۱۵)
- fail-closed: فایل خراب → مصرف ممنوع

**SelfModel:**
- `outward_locked()` → بررسی Branch A در PROJECT.md
- `open_questions()` → شمارش از OpenQuestions.md
- `pending_verdicts()` → لیست از THREAD-CLOSURE §۹
- `saba_bridge()` → وضعیت صبا (درفت‌ها، halt، ظرفیت)

**UpgradeEngine:**
- propose-only: فایل proposal می‌نویسد
- هرگز سورس خودش را دست نمی‌زند
- کاندیداهای ارتقا: blocklist, LLM layer, brain import, GATE 0

**دستورها:**
- `/status` — وضعیت کامل پروژه + خود
- `/gates` — G0–G4
- `/verdicts` — لیست verdictهای منتظر
- `/saba` / `/drafts` — bridge به استودیوی صبا
- `/brief` — بریف هفتگی
- `/think <topic>` — تحلیل propose-only
- `/upgrade` — پیشنهادهای ارتقا
- `/kill` / `/revive` — kill-switch فایل‌محور
- `/pf_*` — خط لولهٔ اکتساب (pf_admin)

**LLM layer (اختیاری):**
- Haiku زیر CostMeter
- system prompt با قواعد قفل‌شده
- redact قبل از ارسال

---

## 6. ارکستراتور — orchestrator.py

**PFOrchestrator** — حلقهٔ زندهٔ Project-F:

```python
tick():
  1. neural snapshot (NeuralDriver.evaluate)
  2. protective mode? (pain > 0.7 → فقط heartbeat)
  3. throttle check
  4. acquisition feedback (if post_feedback)
  5. thinking (DualBrainV3.think_and_communicate)
  6. hebbian observe (co-occurring signals)
  7. consolidation (هر ۱۰ tick)
  8. sprint management (SprintRunner)
```

**λ_persist = -1.0** (ضد بهینه‌سازی بقا)

**advisory_only = True** (هیچ اجرای خودکار)

---

## 7. انسان در حلقه (HITL)

### 7.1 مدل دوکلیده (two-brain)

```
صبا (Creator) ──draft──► ProjectFBrain ──low-risk──► صبا
                         │
                         └──high-risk──► آری (Operator) ──verdict──► اجرا
```

### 7.2 tiered routing

| risk | مسیر | مثال |
|---|---|---|
| low | مستقیم به صبا | ایدهٔ محتوا، زمان‌بندی |
| high | به آری (human-append) | قیمت PPV، انتشار، DM فروش |
| dropped | Guard رد کرد | نقض compliance/ethics |

### 7.3 قواعد قفل‌شده (۸ عدد)

1. فقط پا — بدون صورت/بدن/explicit
2. geo-block کامل ایران
3. پرداخت فقط داخل پلتفرم
4. بدون نقض ToS
5. privacy دوطرفه
6. بدون geo-fact حد شهر
7. کد Project-F بیرون از پوشه
8. ۱۸+ و رضاعت؛ محدودهٔ C حاکم

### 7.4 GATEها

| گیت | شرط | وضعیت |
|---|---|---|
| **G0** | Branch A تأیید + توافق امضا + پاسخ سؤال آخر | 🔴 **OPEN — blocker** |
| G1 | ≥200 کلیک + ≥10% click→follow + delivery ≥80% | not started |
| G2 | ≥30 free-sub + ≥5% free→paid + AUD 100 | not started |
| G3 | ≥AUD 2k/mo ×3 + churn<30% | not started |
| G4 | ۱۲ ماه سودده + ابزار داخلی | not started |

---

## 8. اتصال به اختاپوس

### 8.1 نقشهٔ اتصال

| سطح | مسیر/فایل | نقش |
|---|---|---|
| Manifest | `PROJECT-F-CONTROL-MANIFEST.json` | قرارداد ماشین‌خوان (صفر-PII) |
| Interface | `AGENT-CONTROL-INTERFACE.md` | روایت انسان‌خوان |
| Brain Spec | `PROJECT-F-BRAIN-SPEC.md` | مغز ۷ زیرعامل + HITL |
| Patch Plan | `PATCH-PLAN-OCTOPUS-ADAPTER.md` | (وجود ندارد — یافت نشد) |

### 8.2 کنترل سطح (از MANIFEST)

```json
{
  "master_agent_boundary": "The master may OBSERVE, TASK the propose-only layers, route verdicts to the human, and trigger kill-switches. The master MUST NOT execute any hard-gated/outward action."
}
```

### 8.3 فایل‌های handoff

| فایل | جهت | محتوا |
|---|---|---|
| `studio/drafts.json` | C→O | درفت‌های pending |
| `studio/to_ari.json` | C→O | اعلان‌ها، halt، boundary |
| `studio/for_saba.json` | O→C | inbox آری |
| `studio/capacity.json` | C→O | ساعت هفتگی |
| `studio/boundary_log.json` | C→O | تغییرات محدوده (append-only) |

---

## 9. قراردادها و مانیفست

### 9.1 PROJECT-F-CONTROL-MANIFEST.json

| بخش | محتوا |
|---|---|
| identity | code: Project-F, domain: creator-economy, team: 2-person 50/50 |
| status_snapshot | ZERO execution, GATE 0 open, 11 pending verdicts |
| hard_rules_locked | ۸ قاعده غیرقابل تغییر بدون verdict انسانی |
| gates | G0–G4 با شرایط pass |
| autonomy_model | default=autonomous for reversible in-folder work; hard_gated=human verdict |
| capabilities | ۹ قابلیت (research, decision_matrix, playbook, content_studio, cockpit, brain_hitl, learning, experimentation) |
| control_surface | read_state_files, cockpit_commands, studio_actions, file_handoffs, programmatic_api |
| kill_switches | ۴ scope (cockpit, studio/creator-boundary, brain-budget, platform-warning) |
| budget_caps | tooling AUD 100/mo, cockpit LLM AUD 15/mo, brain ۲٪ cap, injection AUD 200/mo |

### 9.2 Programmatic API

| کلاس | ماژول | متدهای کلیدی |
|---|---|---|
| ProjectFBrain | `brain/project_f_brain.py` | process_draft, compliance_guard, ethics_guard, archive, spend |
| AcquisitionBrain | `brain/acquisition.py` | analyze, plan_week, feedback_loop, suggest_next_action |
| LearningBridge | `brain/learning.py` | recommend, ThompsonBandit.observe/select/rank/explain |
| ABTestTracker | `brain/ab_tracker.py` | create_test, record_result, analyze, auto_winner |
| ContentStudio | `studio/content_studio.py` | submit_draft, drafts_html, halt |

---

## 10. سوئیچ‌های ایمنی و kill-switch

| سوئیچ | تریگر | اثر |
|---|---|---|
| **cockpit /kill** | `/kill` یا `touch langar/KILL` | refuse all commands except /status, /revive |
| **studio /halt** | `/halt` یا `touch studio/HALT` | studio halt; Operator notified; boundary supreme |
| **brain-budget** | spend > ۲٪ cap یا > AUD 15/mo | fail-closed; LLM calls blocked |
| **platform-warning** | هر platform warning | stop automation + log to DecisionLog |
| **GATE 0** | باز بودن | همه hard-gated actions مسدود |
| **OpsecGuard** | هر خروجی تلگرام | redact PII/شهر/مسیر قبل از ارسال |
| **Compliance-Guard** | هر پیشنهاد | drop if faceless/feet_only/no_explicit/over_18/geo-block/payment fail |
| **Ethics-Guard** | هر پیشنهاد | drop if dark-pattern/manipulation/engagement-optimization |

---

## 11. بستهٔ تست

### 11.1 تست‌های brain

| فایل تست | چه تست می‌کند | وضعیت |
|---|---|---|
| `test_learning.py` | ThompsonBandit, exploration, recency, eval, persistence | ✅ ۱۱ تست سبز |

**نمونه assertions:**
- reward با tanh اشباع نمی‌شود
- nylon پس از ۴۰ observe اکثراً انتخاب می‌شود
- arm کم‌داده explore می‌شود (min-pull guard)
- explore_rate در floor/cap می‌ماند
- Thompson regret < greedy regret (میانگین ۴۰ seed)

### 11.2 تست‌های langar

| فایل تست | چه تست می‌کند | وضعیت |
|---|---|---|
| `test_langar.py` | opsec redaction, stranger-silence, kill-switch, cost fail-closed, outward-lock, no-media, upgrade-scope | ✅ ۸ تست سبز |

### 11.3 تست‌های studio

| فایل تست | چه تست می‌کند | وضعیت |
|---|---|---|
| `test_saba_studio.py` | submit flow, cert-gate, capacity, boundary-halt, inbox, no-media, stranger-silence | ✅ ۱۰ تست سبز |

### 11.4 تست acquisition pipeline

| فایل تست | چه تست می‌کند | وضعیت |
|---|---|---|
| `test_acquisition_pipeline.py` | draft→approve→finalize, copy guard, flagged rejection, no auto-post | ✅ ۲۲ تست سبز |

**جمع:** ۵۱/۵۱ تست سبز (۲۹ unit + ۲۲ pipeline)

---

## 12. کدها و فایل‌ها

### 12.1 inventory کد

```
orchestrator.py          (169 خط) — ارکستراتور اصلی

brain/
  project_f_brain.py     (247 خط) — control-plane + ۷ زیرعامل
  dual_brain_v3.py       (417 خط) — ۱۰ think + ۷ comm
  acquisition.py         (266 خط) — AcquisitionBrain + Memory
  acquisition_pipeline.py (223 خط) — خط لوله propose-only
  learning.py            (295 خط) — ThompsonBandit + UCB1 + Eval
  ab_tracker.py          (—) — A/B test tracker
  content_engine.py      (—) — موتور محتوا
  kpi_dashboard.py       (—) — داشبورد KPI
  lifecycle.py           (—) — چرخهٔ حیات
  dual_brain.py          (—) — نسخه قدیمی
  test_learning.py       (119 خط)
  test_acquisition_pipeline.py

studio/
  saba_studio.py         (458 خط) — رابط تلگرامی صبا
  content_studio.py      (224 خط) — موتور مشترک
  affirm.py              (66 خط) — لایه گرم
  studio_telegram.py     (—) — نسخه قدیمی
  studio_telegram_v3.py  (—) — نسخه v3
  test_saba_studio.py    (132 خط)
  test_affirm.py         (—)

langar/
  langar_bot.py          (493 خط) — کاکپیت آری
  pf_admin.py            (—) — ادمین اکتساب
  test_langar.py         (110 خط)
```

### 12.2 فایل‌های کلیدی markdown

| فایل | نقش |
|---|---|
| `PROJECT.md` | manifest اصلی پروژه |
| `PROJECT-F-BRAIN-SPEC.md` | مغز ۷ زیرعامل |
| `PROJECT-F-CONTROL-MANIFEST.json` | قرارداد ماشین‌خوان |
| `AGENT-CONTROL-INTERFACE.md` | رابط کنترل ایجنت مادر |
| `CLAUDE.md` | منشور حاکمیت |
| `DECISION-MATRIX-M2-2026-07-10.md` | ماتریس تصمیم |
| `COMPLIANT-PLAYBOOK-M3-2026-07-10.md` | پلن اجرایی |
| `ROADMAP-10-STAGES-2026-07-12.md` | نقشه ۱۰ مرحله‌ای |
| `CARTOGRAPHY-2026-07-12.md` | نقشه‌برداری تأییدشده |
| `RISK-LADDER.md` | نردبان ریسک |
| `SOURCE-OF-TRUTH-MATRIX.md` | ماتریس منبع حقیقت |
| `MIGRATION-MAP-2026-07-12.md` | نقشه مهاجرت |
| `ACQUISITION-ENGINE-2026-07-05.md` | موتور اکتساب |
| `Feet-Content-Business-Master-Playbook.md` | پلی‌بوک کامل |

---

## 13. شکاف‌ها و ریسک‌ها

### 13.1 بلوکرهای باز

| # | شکاف | شدت | توضیح |
|---|---|---|---|
| B1 | **GATE 0 باز** | 🔴 **CRITICAL** | محل اقامت پارتنر ثبت نشده؛ Branch A/B undecided؛ همه چیز پشت این گیت |
| B2 | **۱۱ verdict منتظر آری** | 🔴 HIGH | G0, Playbook+M3-a, balance>$100, cap AUD 15, EXT-04, brand, Fansly, X labeling, AU block, Langar activation, body freeze |
| B3 | **learning.py greedy bug** | 🟡 MEDIUM | باگ greedy هنوز به acquisition سیم‌نشده (PROP-D2) |
| B4 | **project_f_brain مرده در runtime** | 🟡 MEDIUM | در cartography شناسایی شد؛ learning سیم‌نشده |
| B5 | **drafts.json = ۲۴۴ ردیف تستی** | 🟡 MEDIUM | نیاز به پاکسازی/بازنشانی |
| B6 | **body expansion در تضاد** | 🟡 MEDIUM | production plan شامل body است ولی صبا رد کرده؛ منجمد یا حذف؟ |
| B7 | **۱۳۵ خطای frontmatter** | 🟢 LOW | نوت‌های top-level واژگان type محلی دارند |
| B8 | **تعهد پارتنر مشروط** | 🟡 MEDIUM | صبا می‌خواهد مسیر پول‌دهی را قبل از ادامه ببیند |

### 13.2 ریسک‌های معماری

| ریسک | احتمال | اثر | کاهش |
|---|---|---|---|
| GATE 0 هرگز بسته نشود | متوسط | پروژه منجمد | پیام آماده به صبا ارسال شود |
| ThompsonBandit بدون دادهٔ واقعی | بالا | پیشنهادات حدسی | ۳ پست اول برای جمع‌آوری داده |
| drift بین studio/langar/brain | متوسط | ناسازگاری state | فایل‌های JSON canonical ثابت |
| OpsecGuard ناقص (blocklist خالی) | بالا | leak هویت | blocklist واقعی پر شود |
| CostMeter state خراب | پایین | مصرف بی‌حساب | fail-closed design |
| λ_persist>0 در آینده | پایین | engagement-at-any-cost | کد review دوره‌ای |

---

## 14. توصیه‌ها

### 14.1 فوری (P0)

1. **GATE 0 را ببند:**
   - پرسشنامه سؤال آخر را بازنویسی ساده‌تر کن
   - به صبا پیام آماده ارسال کن (بلوپرینت §۴.۲)
   - محل اقامت ثبت + Branch A/B انتخاب

2. **۱۱ verdict را تصمیم بده:**
   - Verdict Queue را مرور و هر item را approve/reject/defer کن

3. **PROP-D2 را اجرا کن:**
   - learning.py را به acquisition سیم کن (wire learning to acquisition)
   - باگ greedy را برطرف کن

### 14.2 کوتاه‌مدت (P1)

4. **Langar را فعال‌سازی گیت‌دار کن:**
   - BotFather + shadow week + owner allowlist

5. **OpsecGuard blocklist واقعی بساز:**
   - نام‌های واقعی، نام‌های کاربری، هشتگ‌های ممنوعه

6. **drafts.json را پاکسازی کن:**
   - ۲۴۴ ردیف تستی را archive یا حذف کن

7. **body expansion را حل کن:**
   - منجمد کن یا از production plan حذف کن

### 14.3 میان‌مدت (P2)

8. **AB Tracker را به acquisition pipeline وصل کن:**
   - A/B test واقعی روی Reddit/X

9. **KPI Dashboard را بساز:**
   - از `kpi-dashboard-spec.md` شروع کن

10. **Funnel tracker واقعی راه بینداز:**
    - دادهٔ اولیه از Reddit → OF

11. **برند Anar Soles را finalize کن:**
    - Yalda Arch reserve → verdict #۶

---

> **پایان گزارش.**  
> هرگونه تناقض یا ابهام → `⚑ برای معمار`  
> منبع حقیقت: `PROJECT.md` + `PROJECT-F-CONTROL-MANIFEST.json` + `CLAUDE.md`
