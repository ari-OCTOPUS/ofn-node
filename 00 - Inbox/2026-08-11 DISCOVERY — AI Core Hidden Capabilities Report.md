---
type: knowledge
project: "[[03 - Projects/NBB-Control-Plane/PROJECT]]"
status: active
tags: [octopus, hidden-capabilities, discovery, evidence-ladder, owner-verdict, real-world-alignment]
created: 2026-08-11
updated: 2026-08-11
created_by: agent
sources:
  - "[[00 - Inbox/2026-08-11 OWNER — Focus AI Core Hidden Capabilities]]"
---

# DISCOVERY REPORT — قابلیت‌های پنهان هوش مصنوعی اختاپوس (2026-08-11)

> پاسخ به رأی مالک: کدام قابلیت‌های پنهان واقعاً وجود دارند، کدام ارزش فعال‌سازی دارند،
> و چه آزمایش‌هایی بدون پول واقعی آن‌ها را ثابت می‌کند.
> خط حقیقت: `octopus-ai-core + hidden-capability-discovery + real-world-alignment`
> `!= money-legs-live != reconcile-blocked != lead-CRM-focus`

## خلاصهٔ اجرایی

| لایه | وضعیت | تعداد |
|---|---|---|
| **موتور (router/breaker/quota/kill/collab)** | TESTED + **اکثراً ARMED (زنده)** | ۱۲+ قابلیت |
| **تست‌اینتلیجنس (discovery/red-team/golden traces)** | TESTED + آمادهٔ shadow | ۶ ابزار |
| **قابلیت‌های پنهان مغز (cortex)** | STRUCTURAL — کد کامل، تست سبز، **فلگ تاریک** | ۱۰ فلگ |
| **پول/لید (خارج از خط حقیقت این فاز)** | تاریک و عمداً خاموش | ۶ فلگ |

اسکن زنده (dark_capabilities.py): **۲۲ دروازهٔ تاریک از ۳۶۸ فلگ** (+۰ جزئی · ۸۱ تنظیمی) —
منبع live: center، cortex، live، miniapp-gateway، organism.

---

## ۱) کدام قابلیت‌های پنهان واقعاً وجود دارند؟

### A. موتور — TESTED + ARMED (زنده، مسلح در هر ۵ پروسه)

تأییدشده با اجرای همین جلسه (همه سبز):

| قابلیت | شاهد | وضعیت زنده |
|---|---|---|
| **model_router سه‌لایه** (local→secondary→primary) | `test_ti_router_snapshot: 8/8` ✅ | ARMED — `OCTOPUS_GOVERNOR_USE_ROUTER=1` |
| **circuit_breaker** (CLOSED→OPEN→HALF_OPEN) | `test_ti_breaker_chaos: 10/10` ✅ | ARMED |
| **kill_seam** (STOP-ORGANISM) | `test_kill_seam_wire: 8/8` ✅ | ARMED — `OCTOPUS_WIRE_KILL_SEAM=1` |
| **collaborator** (همکار مالک) | `test_ti_collab_security: 12/12` ✅ | **ARMED — `OCTOPUS_WIRE_COLLAB=1` در هر ۵ پروسه** |
| **fugu_quota / budget_gate** (سقف و STOP-FUGU) | `test_paid_timeout_chain: 60/60` (مستند) | ARMED — سقف AU$30/ماه + پنجرهٔ US$200 تا ۰۸-۱۳ |
| **context_bundle / control_contracts / approval_store / outbound_https / MiniApp gateway** | ۱۳/۱۳ · ۱۰/۱۰ · ۱۷/۱۷ · ۱۴/۱۴+۱۸/۱۸ · ۱۱/۱۱+۱۶/۱۶ (مستند) | ARMED |
| **route_shadow** (سایهٔ تصمیم‌های مسیریابی) | — | **ARMED — `OCTOPUS_WIRE_ROUTE_SHADOW=1`** |

### B. تست‌اینتلیجنس — TESTED، آمادهٔ shadow (هزینه $0)

| ابزار | شاهد | نقش |
|---|---|---|
| **discovery eval** (پنج‌تکرار، digest-only) | `test_ti_discovery_eval: 9/9` ✅ | ادعای کشف فقط با تکرار ≥۳ از ۵ قبول می‌شود |
| **red-team injection** | `test_ti_redteam_injection: 3/3 — 25/25 case` ✅ | ۲۵ سناریوی تزریق × ۶ کد ASI |
| **policy_oracle** | `test_ti_policy_oracle: 9/9` ✅ | نظارت سیاست در سایه |
| **held_out_evaluator** (۳ لایه: canary suite + hash-chain ledger + sealed predictions) | **اجرای همین جلسه: 5/5 · ledger valid · overall=pass · anti_hacking=False** ✅ | محک نگه‌داشته‌شدهٔ ضد-دورزدن |
| **trace_schema / build_evidence / dark_inventory** | `test_ti_trace_contract: 8/8` + `test_ti_dark_inventory: 4/4` (مستند) | ردگیری digest-only (بدون PII/secret) |

### C. قابلیت‌های پنهان مغز — STRUCTURAL (کد کامل + تست سبز، فلگ تاریک)

این‌ها همان «تاریک‌ترین» قابلیت‌های واقعی‌اند — خوانده می‌شوند، هرگز مسلح نشده‌اند:

| فلگ تاریک | خواننده‌ها | چه می‌کند |
|---|---|---|
| `CORTEX_SELF_MONITOR` | **۶ خواننده** (بیشترین کدِ خفته) | خودپایشی مغز |
| `CORTEX_IGNITION` | ۳ | راه‌اندازی شمردهٔ cortex |
| `CORTEX_CONSOLIDATE` | ۳ | تثبیت حافظه/مفاهیم |
| `CORTEX_ROUTE_SCORER` | ۳ | مشورت امتیازدهی مسیر (fail-soft) |
| `CORTEX_LOCAL_FIRST` | ۱ | local-first با quality gate (صرفهٔ واقعی) |
| `CORTEX_TRUTH_BY_CYCLE` / `CORTEX_IMPROVE_DEEP` / `CORTEX_INDICATOR_SCORECARD` | ۱–۱–۱ | حقیقتِ چرخه‌ای / بهبود عمیق / کارت شاخص |
| `OCTOPUS_WIRE_COLLAB_MEMORY` / `COLLAB_DIGEST` / `COLLAB_USE_MODEL` | ۲/۱/۱ | حافظهٔ اپیزودیک همکار / دیجست / مدل واقعی |
| `OCTOPUS_WIRE_SEMANTIC_TRACE` / `SEMANTIC_ABLATION` | ۱/۱ | ردیابی/حذف معنایی |
| `OCTOPUS_WIRE_KERNEL_BRIDGE_READER` | ۱ | خوانندهٔ body_bridge (artifact کهنه — Jul 14) |

### D. خارج از خط حقیقت این فاز (عمداً تاریک بمانند)

`OCTOPUS_WIRE_HARVEST` · `OCTOPUS_WIRE_LEAD_FIRST_REPLY/RESPONSE/RESPONSE_LLM` ·
`OCTOPUS_ENFORCE_MONEY_FSM` · `OCTOPUS_INITIATIVE_UNCAPPED` (این یکی به‌خاطر امنیت
**هرگز** نباید روشن شود).

### E. باگ‌های کشف‌شده

- `OCTOPUS_WIRE_RUNNER_APPLY` — مسلح ولی **هیچ خواننده‌ای ندارد** (تایپو یا کدِ حذف‌شده).
- `capability_classifier`: `body_bridge_reader` → artifact missing؛ `c6` → وضعیت unknown.

---

## ۲) کدام ارزش فعال‌سازی دارند؟

### اولویت بالا (AI-core — هم‌راستا با رأی مالک)

1. **`CORTEX_SELF_MONITOR`** — ۶ خواننده، بزرگ‌ترین قابلیتِ خفتهٔ مغز؛ خودپایشی یعنی همان
   «کیفیت تصمیم» که مالک خواسته. آزمایش: بدون پول، فقط رفتار خودش.
2. **`CORTEX_ROUTE_SCORER` + `CORTEX_LOCAL_FIRST`** — کیفیت مسیریابی + صرفهٔ هزینه.
   مسیر پولِ واقعی را لمس نمی‌کند؛ تصمیمِ tier را بهتر می‌کند.
3. **`OCTOPUS_WIRE_COLLAB_MEMORY`** (و بعد `COLLAB_USE_MODEL` با سقف روزانه) —
   تجربهٔ AI مالک (P1 shadow)؛ طبق پلن P1: بعد از ۲۴ ساعت پایدار بودن COLLAB.
4. **`OCTOPUS_WIRE_SEMANTIC_TRACE`** — ردیابی معناییِ تصمیم‌ها = شواهد قابل‌بازبینی.

### میانه (ارزش دارد ولی نه فوری)

- `CORTEX_IGNITION` / `CORTEX_CONSOLIDATE` — زیرساختِ consolidation؛ وقتی SELF_MONITOR فعال شد.
- `OCTOPUS_WIRE_KERNEL_BRIDGE_READER` — بعد از تازه‌کردن body_bridge (الان artifact کهنه است).

### فعال نکن

- همهٔ فلگ‌های D (خارج از خط حقیقت) تا رأی جدا.
- `OCTOPUS_INITIATIVE_UNCAPPED` — امنیت.

---

## ۳) چه آزمایش‌هایی بدون پول واقعی آن‌ها را ثابت می‌کند؟

همهٔ این‌ها $0 و بدون effect خارجی هستند — همگی **همین جلسه** اجرا و سبز شدند:

```bash
# نردبان شاهد برای هر arm (قبل ← بعد):
python _ops/dark_capabilities.py --json          # DARK → ON را نشان می‌دهد

# تست‌های موتور (offline/mock):
python _ops/tests/test_ti_router_snapshot.py     # 8/8 ✅
python _ops/tests/test_ti_breaker_chaos.py       # 10/10 ✅
python _ops/tests/test_kill_seam_wire.py         # 8/8 ✅
python _ops/tests/test_ti_collab_security.py     # 12/12 ✅
python _ops/tests/test_api_collab.py             # 17/17
python _ops/tests/test_collab_components.py      # 23/23

# تست‌اینتلیجنس:
python _ops/tests/test_ti_discovery_eval.py      # 9/9 ✅
python _ops/tests/test_ti_policy_oracle.py       # 9/9 ✅
python _ops/tests/test_ti_redteam_injection.py   # 3/3 (25/25) ✅

# محک نگه‌داشته‌شده (3 لایه، ضد-دورزدن):
python -c "from held_out_evaluator import evaluate_held_out; print(evaluate_held_out())"
# → fixed_suite 5/5 · ledger valid · overall=pass ✅

# کل سوئیت (588 تست — تأییدشده در REPORT-P0):
python _ops/tests/run_all.py                     # 588/588 GREEN
```

**پروتکل ارتقا (طبق EVIDENCE-LADDER):**
1. STRUCTURAL → TESTED: تست offline سبز با SUT واقعی ✅ (همین الان برای موتور برقرار است)
2. TESTED → SHADOW: اجرای سایه روی دادهٔ واقعی، ۷ روز بدون حادثه (پلن P1 آماده است)
3. SHADOW → ARMED: فلگ + boot snapshot + restart موفق (دقیقاً همان‌چیزی که COLLAB الان دارد)

**مشاهدهٔ کلیدی برای مالک:** `OCTOPUS_WIRE_COLLAB=1` **همین الان روی درخت زنده مسلح است**
(برخلاف REPORT-P1 که arm را pending می‌دانست) — یعنی قدمِ اولِ P1 عملاً برداشته شده.
گام بعد: `COLLAB_MEMORY` بعد از ۲۴ ساعت پایداری، و بعد `COLLAB_USE_MODEL` با سقف روزانهٔ
نوشته‌شده در budgets.yaml — همه بدون لمس پول واقعی.

---

## ARM RESULTS — رأی مالک «همرو فعال کن» (همان روز، 2026-08-11 ~19:30)

### اجرا شد

| اقدام | جزئیات | شاهد |
|---|---|---|
| **۵ فلگ جدید در `OCTOPUS-flags.cmd`** | `COLLAB_MEMORY` · `COLLAB_DIGEST` · `SEMANTIC_TRACE` · `SEMANTIC_ABLATION` · `KERNEL_BRIDGE_READER` | ۳۰۳ فلگ در snapshot (از ۲۹۸) |
| **ری‌استارت کامل** | `RESTART-ALL.ps1` — cortex→center→gateway→live→organism، همه با کد تازه | ۵ PID جدید + پورت 8771/8774 + beat ادامه‌یافته (31554→31558) |
| **رفع نقطهٔ کور اندازه‌گیری** | `flag_drift.TRACKED_PREFIXES` += `CORTEX_` | `test_flag_drift` + `test_dark_capabilities 18/18` سبز |

### نتیجهٔ اسکن نهایی: **۲۲ ← ۹ تاریک** (منبع live)

- **۸ فلگ CORTEX_ (SELF_MONITOR، ROUTE_SCORER، LOCAL_FIRST، IGNITION، CONSOLIDATE، TRUTH_BY_CYCLE، IMPROVE_DEEP، INDICATOR_SCORECARD): حالا ON** — از batch armِ ۰۸-۰۹ مسلح بودند؛ ما آن‌ها را نمی‌دیدیم (پیشوند CORTEX_ در snapshot نبود).
- **۹ باقیمانده — همه عمداً خاموش:** `COLLAB_USE_MODEL` (پول خارجی) · `ENFORCE_MONEY_FSM` · `INITIATIVE_UNCAPPED` (امنیت) · `LEAD_FIRST_*` (۳ عدد، پیام خارجی لید) · `VALUE_LEDGER` · `HARVEST` · `STATE_DIR` (نویز — مسیر است نه گیت).
- **یتیم:** `OCTOPUS_WIRE_RUNNER_APPLY` مسلح ولی بی‌خواننده — تایپو یا کدِ حذف‌شده (بازبینی بعدی).

### نکات

- گیت پذیرش RESTART-ALL در ابتدا «organism state تازه‌ننوشت» گفت — کاذب: ارگانیسم در اولین beat (≈۳ دقیقه بعد) state نوشت و سالم می‌تپد.
- `OCTOPUS_WIRE_OUTBOUND_HTTPS=1` از batch armِ ۰۸-۰۹ مسلح بود (پیش از این جلسه) — طبق P0، zero-mutation تا وقتی WIRED نشده + approval-gated؛ این جلسه دست‌نخورده.
- `EVIDENCE-LADDER.md` با ردیف‌های ARMED جدید به‌روز شد.
- commit این تغییرات — همچنان منتظر رأی مالک (طبق REPORT-P0).
