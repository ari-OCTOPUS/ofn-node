# AGENT-INVENTORY — 2026-08-16

> عامل: Worker Agent (ZCode/GLM-5.3) · فاز ۰ دستورالعمل `OCTOPUS Implementation Directive`
> روش: خواندن فایل واقعی (R7) — هر ادعا زیر با مشاهدهٔ مستقیم از درخت زنده ساخته شده، نه از حافظه یا طرح.
> ارگانیسم **زنده** است: beat≈38410 · arbiter GREEN · ۴ پروسه (organism/center/cortex/live) — بدون restart (R5).

---

## ۱. وضعیت لحظه‌ای ارگانیسم (اندازه‌گیری مستقیم)

| سنجه | مقدار | منبع |
|---|---|---|
| beat | 38410 | `ORGANISM-STATE.json` ts=22:09 |
| halted | false · `frozen: true` (heart work skipped=FREEZE) | `ORGANISM-STATE.json` |
| arbiter | GREEN · period 124.65s · wire_open | همان |
| cortex | coherence 0.9 · ۱۱/۱۱ عضو present · stale: work_pump | `cortex-state.json` |
| قلب | `wire_open: false` (سایه) · FREEZE.flag روی دیسک (untracked) | همان |
| آخرین رویداد spine | `system.beat beat_4125` @ 12:13:14Z — **الان زنده** | `state/spine/spine.db` |

نکتهٔ مهم: شمارندهٔ beat_scheduler (۴۱۲۵) از beat ارگانیسم (۳۸۴۱۰) جدا است — دو ساعت‌سنج موازی.

---

## ۲. inventor ماژول‌ها (فایل‌های واقعی روی دیسک)

### `_ops/heart/` — ۱۸ فایل py
autoregulation · budget_judge · cognition_effect · control_law · doctor_setpoint · fuel_meter · heartstate · interface · kalman_shadow_pipeline · money_pulse · producers · pulse_arbiter · pulse_shadow_compare · replay_s · shadow · sim_heart · sog_math · work_pump
(+ `cardiac-budget.json` در `state/` — امروز: spent 500 / cap 2000)

### `_ops/neural/` — ۱۶ فایل py + ۲ json
bcm · circadian · consolidation · encoders · hooks · latent_space · neural_driver · nociceptor · pain_assessment · reflex · signal_hub · sparse_filter · sprint

### `_ops/control_plane/` — ۵ فایل py
collector · live_snapshot · supervisor · __init__ — **`dual_brain.py` هنوز وجود ندارد** (فاز ۶ آن را می‌سازد)

### `_ops/cortex/` — ۴۱ فایل py
model_router · improve · code_autonomy · business_brain · registry · autonomy_matrix · … — **`provider_adapter.py` هنوز وجود ندارد** (فاز ۵)

### ماژول‌های خفته/نیمه‌وصل (مبنای فازهای ۲ و ۸)

| ماژول | فایل‌ها | پرچم | وضعیت واقعی (اندازه‌گیری ۲۰۲۶-08-16 22:15) |
|---|---|---|---|
| **event spine** | `_ops/spine/` (event_spine, spine_adapters, spine_reconcile, boot_certificate) | `OCTOPUS_WIRE_SPINE` | **WIRED و زنده** — پرچم در env هر ۵ پروسه=1 · spine.db با **۴۷۷۰ رویداد** (system 4283 · doctor 399 · proposal 48 · neural 24 · lead 6 · ziman 10) · آخرین رویداد همین حالا |
| **beat scheduler** | `_ops/beat_scheduler.py` | `OCTOPUS_ONE_HEARTBEAT` | **ON** در env (ضربان سایه فعال، beat 4125) |
| **intel spine** | `_ops/intel_spine/` (obsidian_sync, telegram_adapter, webapp_adapter) | `OCTOPUS_INTERACTION_LOG` | پرچم **ON** در env · آداپتورها موجود · state اختصاصی روی دیسک دیده نشد → «flag-on, خروجی تأییدنشده» |
| **action bridge** | `_ops/action_bridge/` (۹ فایل: classifier, executor, owner_gate, planner, rollback, …) | `OCTOPUS_WIRE_ACTION_BRIDGE` | پرچم **ON** در env ولی **صفر ارجاع در wiring.py** و هیچ state/خروجی روی دیسک → **flag-on، مسیر مرده** (بدون runtime caller) |
| **afferent** | `_ops/afferent/` (sensory_bus, ingest_raw, school_bridge) | نامشخص — `CHRONO_AFFERENT_EVERY_N_BEATS` knob (1440) در wiring | **UNWIRED** — هیچ state/pulse یافت نشد؛ afferent_ratio از live_loop فقط advisory |
| **synapse** | `_ops/synapse/` (sense, egress_policy, trajectory_monitor) | `SYNAPSE_ENABLED` | **UNWIRED** — پرچم در env هیچ پروسه‌ای نیست · `out/proposal-*.json` وجود ندارد |
| **chord** | `_ops/chord/` (۷ فایل: ledger, observation, repair_policy, uncertainty_gate, …) | `OCTOPUS_WIRE_CHORD` (هنوز خواننده‌ای ندارد) | **UNWIRED** — هیچ state چورد روی دیسک نیست |
| **4d_system** | `4d_system/` (پکیج کامل ۹تایی + control_plane با approvals/killswitch/policy) | `FOURD_*` (هیچ‌کدام در env نیست) | **UNWIRED** — تأیید CURRENT-TRUTH: «4d_system / Super-Governor: وصل نیست» · MANIFEST مستقل، TCB خودش را دارد |

---

## ۳. پرچم‌ها

### `ACTIVATION-*.flag` روی دیسک (۱۵ RAISED + ۱ .off) — رجیستری tracked: `_ops/ACTIVATION-FLAGS.md`

C6-RESEARCH · CODE-AUTONOMY · CORTEX-PAID · DEBATE · GO-LIVE · GOVERNOR-LLM (+`.flag.off` یادگار) · HEART-DOCTOR · **HEARTSTATE** · PULSE-ARBITER · PULSE · RAW-SHELL · REPLICATION · RESEARCH-EARLY · SELF-IMPROVE-AUTO · WORK-LLM — همه RAISED.

⚠️ همان هشدار §ACTIVATION-FLAGS: `HEARTSTATE` با **فایل** مسلح است نه env؛ ممیزیِ مبتنی‌بر `flags-loaded-*.json` امروز آن را خاموش گزارش می‌دهد در حالی که `heartstate.py` هر ضربان می‌نویسد (فاز ۳ همین را اصلاح می‌کند).

### env — منبع زنده: `_ops/OCTOPUS-flags.cmd` (gitignored) → snapshot در `state/flags-loaded-{organism,cortex,center,live,miniapp-gateway}.json`

- `.env` زیر الگوی `.agentignore` (`*.env`) است → ایجنت **نمی‌نویسد/نمی‌خواند**. فلگ‌های جدید از مسیرِ قانونی `owner-verdicts.yaml` (tracked، non-secret، reader=`wiring.effective_flag`) ثبت می‌شوند؛ env برنده می‌ماند.
- وضعیت پرچم‌های هدف (از هر ۵ snapshot):
  - `OCTOPUS_WIRE_SPINE=1` · `OCTOPUS_INTERACTION_LOG=1` · `OCTOPUS_ONE_HEARTBEAT=1` · `OCTOPUS_WIRE_ACTION_BRIDGE=1` — **همگی از قبل در env روشن‌اند**
  - `SYNAPSE_ENABLED` · `OCTOPUS_WIRE_CHORD` · `OCTOPUS_WIRE_AFFERENT` · `FOURD_DATA_ACCESS` · `DUAL_VETO` · `LIFE_CURRENCY` — **غایب** (خاموش)
- ۴۰+ `wire_*` دیگر در `ORGANISM-STATE.json.wiring` = true (live profile).

### رأی‌های tracked موجود: `_ops/owner-verdicts.yaml`
spend_cap · goal_max_circular · fugu_weekly_share · neural_learned_apply · chrono_rhythm_cr_b0 · math_control_spine · math_autotune_knobs · limited_effect_phase_n

---

## ۴. درخت dirty (R: ثبت قبل از شروع)

- شاخه: `equip/g5-infra-20260816` · HEAD: `a396d05`
- ~۷۰ فایل modified (عمدتاً state زندهٔ ارگانیسم + نوت‌های Inbox/Knowledge از کار مالک) + ۳ deleted (epoch قدیمی) + ~۴۰ untracked (سه سند 04-SYSTEMS همین امروز، evidence های G4/G5، `octopus_v3/`، `beat_lease`، …)
- **قاعدهٔ کار من:** هر commit فقط فایل‌های خودِ همان فاز را stage می‌کند (`git add <explicit paths>`) — هرگز `-A`. دست‌نخورده می‌ماند.
- `_ops/budget/FREEZE.flag` (untracked) روی دیسک است → کار قلب FREEZE است؛ من کم نمی‌کنم.

---

## ۵. مبنای تست

- pytest 9.1.1 موجود · تست‌ها در `_ops/tests/` (از جمله test_event_spine, test_spine_multidomain, test_activation_flag_presence, test_flag_load_shortfall, test_synapse_*, test_chord*, test_intel_spine)
- الگوی تست‌های موجود: tmp_path + بدون شبکه + monkeypatch env — همان سبک را ادامه می‌دهم.

---

## ۶. تفاوت‌های طرح ↔ واقعیت (مهم برای فازها)

1. **فاز ۲ (spine) در تولید از قبل انجام شده** — پرچم روشن، spine.db زنده با trace_id. باقی‌مانده: تستِ تأییدِ wired بودن + ثبت رأی tracked. **هیچ init جدیدی به wiring.py اضافه نمی‌شود** (spine در LEG-07 و beat_scheduler از قبل init می‌شود؛ اضافه‌کردن دوباره = دومین نویسنده، خلاف R10).
2. دستورالعمل می‌گفت فلگ‌ها در `.env` — `.env` توسط `.agentignore` ممنوع است؛ مسیر قانونی: `owner-verdicts.yaml` + env از طرف مالک (پرچم‌های spine/intel/one-heartbeat/action-bridge از قبل در env هستند).
3. `supervisor.py` کنترل‌پلین singleton-snapshot است، نه ارزیاب پروپوزال — فاز ۶ `dual_brain.py` را جدید می‌سازد و به مسیر approvals موجود (`4d_system/control_plane/approvals.py` + صف `_octopus/queue/`) وصل می‌کند.
4. `events.py` نام‌های رویداد را از taxonomy سخت می‌گیرد (نام ناشناس → task.failed + drift). برای heartbeat ماژول‌های خاموش باید `module.heartbeat` به EVENT_NAMES اضافه شود (additive).
5. `model_router.py` خودش fallback paid→local دارد؛ `provider_adapter.py` فاز ۵ لایهٔ ارکستراسیون D5/D6 روی همان می‌سازد، بدون دست‌زدن به مسیر paid زنده.
