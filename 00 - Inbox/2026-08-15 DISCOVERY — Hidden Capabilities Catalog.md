---
type: knowledge
kind: discovery-catalog
status: active
created: 2026-08-15
updated: 2026-08-15
created_by: agent (discoverer)
audience: owner
tags: [octopus, hidden-capabilities, catalog, vote-cards, propose-only]
sources:
  - "[[_ops/dark_capabilities.py]]"
  - "[[_ops/flag_drift.py]]"
  - "[[_ops/orphan_scan.py]]"
  - "[[_ops/effector_registry.py]]"
  - "[[_ops/capability_registry.py]]"
  - "[[_ops/capabilities/*.json]]"
scanner_commands:
  - "py -X utf8 _ops/dark_capabilities.py"
  - "py -X utf8 _ops/dark_capabilities.py --json"
  - "py -X utf8 _ops/flag_drift.py"
  - "py -X utf8 _ops/orphan_scan.py"
---

# DISCOVERY — Hidden Capabilities Catalog (2026-08-15)

> **نقض = توقف:** فلگ روشن نشد. send/pay/restart/git-apply نشد. مقدار env چاپ نشد.
> **روش:** سه اسکنر موجود + rg verification + AST تفاضل SCAN_DIRS. ابزار موازی ساخته نشد.

---

## خلاصه اجرایی — اعداد زنده

| شاخص | مقدار | فرمان |
|---|---|---|
| n_flags | 403 | `py -X utf8 _ops/dark_capabilities.py --json` |
| n_live_on | 303 | همان |
| n_dark (class 1) | 15 | همان |
| n_partial (class 2) | 0 | همان |
| n_tuning (class 4) | 95 | همان |
| n_orphan_armed (class 3) | 1 | همان |
| live_source | `live` | پنج پروسه: center, cortex, live, miniapp-gateway, organism |
| flag_drift | 5/5 پروسه drift (SMTP ×4 each) | `py -X utf8 _ops/flag_drift.py` |
| orphan_scan weighty | 18 | `py -X utf8 _ops/orphan_scan.py` |
| effector dead-output | 0 | `effector_registry.py` (08-08 verified) |
| effector display-only | 5 | همان |
| effector wired | 3 | همان |
| effector armed-apply | 1 | همان |
| effector shadow | 1 | همان |
| class 7 (invisible to telegram) | ~45 packages | SCAN_DIRS vs os.listdir |
| class 8 (dual-stack / unwired) | 4 items | rg + STATUS check |

**اعلان STALE — اعداد نوت‌های قدیمی باطل:**
- `128 dark از 326` (نوت ~08-07): **STALE** — قبل از batch-arm و Hub/Hypothesis.
- `64 dark از 347` (08-08): **STALE** — قبل از batch-arm 63 فلگ (08-09).
- `22 dark از 368` (گزارش کشف 08-11): **STALE** — بعدش Talk Discovery / Hub / Hypothesis / Epistemic / APPLY مسلح شدند.
- `COLLAB_USE_MODEL تاریک` (گزارش 08-11 §C): **STALE** — همان شب ARMED شد.
- `CORTEX_CONSOLIDATE ست نشده` (نوت‌های 08-06): **STALE** — پروسه زنده با آن می‌دوید.
- `ORGANISM-SPEC یک پروسه` (07-07): **STALE** — زنده = پنج پروسه.
- `capability_registry SCAN_DIRS کامل است`: **STALE** — conversation_hub / epistemics / hypothesis_engine / math_control / memory / ... داخلش نیستند.

---

## کاتالوگ کلاس ۱ — DARK flag (15 ردیف)

تعریف: کد فلگ را می‌خواند؛ در OCTOPUS-flags.cmd مسلح نیست؛ در PAPER_FULL_FLAGS هم نیست؛ در هیچ پروسه زنده ON نیست.

### 1.1 bucket: `ops-surface`

| flag | readers | class | bucket | ladder | arm_risk | note |
|---|---|---|---|---|---|---|
| OCTOPUS_BOARD_CP | `board_cp/__init__.py` | 1 | ops-surface | STRUCTURAL | owner-chat-ok | اگر روشن شود: برد命令 صف SQLite اجرا می‌کند. ماژول کامل + تست دارد. |
| OCTOPUS_KILL_SWITCH | `policy/talk_gate.py:36` | 1 | ops-surface | TESTED | needs-vote | اگر روشن شود: talk_gate ورودی مالک را بلوک می‌کند. kill-switch واقعی. |
| OCTOPUS_IMPROVE_REFRACTORY_H | `cortex/improve.py` | 1 | ops-surface | TESTED | owner-chat-ok | اگر روشن شود: دوره冷却 بین improve runs تنظیم می‌شود. |
| OCTOPUS_PROFILE | `budget/cockpit_readmodel.py`, `dashboard/server.py`, `wiring.py` | 1 | ops-surface | STRUCTURAL | owner-chat-ok | اگر روشن شود: پروفایل بودجه فعال می‌شود (اسم فقط؛ رفتار تنظیمی). |

### 1.2 bucket: `money-lead`

| flag | readers | class | bucket | ladder | arm_risk | note |
|---|---|---|---|---|---|---|
| OCTOPUS_LEAD_DAILY_SEND_CAP | `legs/outbound_worker.py` | 1 | money-lead | STRUCTURAL | needs-vote | سقف ارسال روزانه لید. **مالک صریح: مسیر پول خارج از خط حقیقت این فاز.** |
| OCTOPUS_SPEND_CAP_USD | `money_caps_snapshot.py` | 1 | money-lead | STRUCTURAL | needs-vote | سقف مخارج دلاری. |
| OCTOPUS_SPEND_CAP_UNTIL | `money_caps_snapshot.py` | 1 | money-lead | STRUCTURAL | needs-vote | تاریخ انقضای سقف مخارج. |

### 1.3 bucket: `dangerous`

| flag | readers | class | bucket | ladder | arm_risk | note |
|---|---|---|---|---|---|---|
| OCTOPUS_SMTP_FROM | `legs/mail_credentials.py` | 1 | dangerous | STRUCTURAL | needs-vote | مکانیزم SMTP. ارسال ایمیل = اثر خارجی. **ممنوع در این مأموریت.** |
| OCTOPUS_SMTP_HOST | `legs/mail_credentials.py` | 1 | dangerous | STRUCTURAL | needs-vote | همان. |
| OCTOPUS_SMTP_PORT | `legs/mail_credentials.py` | 1 | dangerous | STRUCTURAL | needs-vote | همان. |
| OCTOPUS_SMTP_USER | `legs/mail_credentials.py` | 1 | dangerous | STRUCTURAL | needs-vote | همان. |

### 1.4 bucket: `ai-core`

| flag | readers | class | bucket | ladder | arm_risk | note |
|---|---|---|---|---|---|---|
| OCTOPUS_WIRE_CHRONO_RHYTHM | `scripts/verify_math_atlas.py`, `wiring.py` | 1 | ai-core | SHADOW | owner-chat-ok | Chrono Rhythm CR-B0: یکپارچه‌سازی ریتم circadian با pulse_arbiter. capabilities JSON: `enabled: true`, `evidence_level: SHADOW`. **تناقض:** JSON می‌گوید enabled اما اسکنر DARK می‌گوید — دلیل: `capabilities/chrono-rhythm-cr-b0.json` enabled field مستقل از flags.cmd است و JSON قدیمی ممکن است اشتباه کند. حقیقت زنده: DARK در flags.cmd. |
| OCTOPUS_OTLP_ALLOW_REMOTE | `telemetry/criticality_metrics.py` | 1 | ai-core | STRUCTURAL | needs-vote | اگر روشن شود: OTLP traces به remote collector می‌رود. اثر شبکه‌ای. |

### 1.5 bucket: `dead-name` / noise

| flag | readers | class | bucket | ladder | arm_risk | note |
|---|---|---|---|---|---|---|
| OCTOPUS_LIMITED_EFFECT_PHASE_N | `memory/limited_effect.py` | 1 | dead-name | STRUCTURAL | never | نام فلگ در scanner: `OCTOPUS_LIMITED_EFFECT_PHASE_N` ولی کد واقعاً `LIMITED_EFFECT_PHASE_N` را می‌خواند (بدون OCTOPUS_ prefix). scanner تایپو شناسایی کرد. |
| OCTOPUS_STATE_DIR | 36 reader | 4 (TUNING) / noise | dead-name | STRUCTURAL | never | مسیر state directory — دروازه نیست، مسیر است. 36 خواننده دارد ولی مقایسه نمی‌شود با `"1"`. **تله شناخته‌شده #4.** |

---

## کاتالوگ کلاس ۲ — PARTIAL (0 ردیف)

**صفر PARTIAL امروز.** هر پنج پروسه از منبع یکسان (`live`) خوانده‌اند. drift فقط SMTP flags است (4 فلگ × 5 پروسه = 20 رانش) ولی آن‌ها در flags.cmd اصلاً set نشده‌اند (DARK)، پس PARTIAL نیستند — فقط drift روی مقدار default.

**توجه:** `CORTEX_HYPOTHESIS=1` ALREADY-ON در همه پروسه‌هاست. council-conflict: شورا گفت 0 بماند، مالک 08-15 رأی 1 داد. **نه کشف، نه قابل آرم — از قبل روشن و مورد بحث.**

---

## کاتالوگ کلاس ۳ — orphan_armed (1 ردیف)

| flag | armed_in_file | readers | bucket | note |
|---|---|---|---|---|
| OCTOPUS_DOCTOR_USE_CENTRAL_ROUTER | `=1` در OCTOPUS-flags.cmd:1478 | **صفر reader** | dead-name | فلگ=1 ولی هیچ کدی آن را نمی‌خواند. احتمالاً بعد از rename/cleanup باقی مانده. پیشنهاد: document + حذف از flags.cmd (نه آرم). |

---

## کاتالوگ کلاس ۴ — TUNING (95 ردیف — نمونه)

تعریف: `getenv` با پیش‌فرض دارد و با `"1"` مقایسه نمی‌شود — به هر حال می‌دود، دروازه نیست.

فقط نمونه‌های قابل ذکر (بقیه 95 ردیف تنظیمی خنثی):

| flag | default | readers | note |
|---|---|---|---|
| CORTEX_CONSOLIDATE_HALFLIFE_H | تنظیمی | cortex/consolidate.py | نیمه‌عمر تلفیق |
| CORTEX_IGNITION_THRESHOLD | تنظیمی | cortex/ignition.py | آستانه جرقه |
| OCTOPUS_AGENT_GATEWAY_PORT | تنظیمی | legs/agent_gateway_http.py | پورت HTTP agent |
| OCTOPUS_CODE_APPLY_REFRACTORY_S | `300` | cortex/code_autonomy.py | دوره بین apply |
| OCTOPUS_TEACHER_DAILY | تنظیمی | teacher_loop.py | تعداد دوره معلم |

TUNING ذاتاً پنهان ارزشمند نیست — مقادیر تنظیمی‌اند. اگر owner بخواهد مستندش کنند.

---

## کاتالوگ کلاس ۵ — یتیم کد (18 weighty)

ماژول کامل + تست، صفر importer تولیدی، بیرون از SCAN_DIRS.

| ماژول | خطوط | نمادهای کلیدی | bucket |
|---|---|---|---|
| `hypothesis_engine/experiments/analysis.py` | 422 | bootstrap_cliffs_delta, budget_efficiency | ai-core |
| `epistemics/benchmark.py` | 407 | BenchmarkReport, CandExp | ai-core |
| `state_guard.py` | 391 | RepairResult, ScanResult, is_maintenance_locked | ops-surface |
| `scripts/unlock_self_progress.py` | 366 | deny_stalled_and_open_rfcs, gate_status | ops-surface |
| `phase_gate.py` | 362 | get_phase_state, post_phase_check | ops-surface |
| `legs/agent_gateway_http.py` | 353 | enabled, serve, verify_and_dispatch | ops-surface |
| `watchdog_extension.py` | 257 | WatchdogHealthCheck, WatchdogMonitor | ops-surface |
| `seed/redteam_harness.py` | 256 | EscapeAttempt, HarnessResult | ai-core |
| `legs/budget_frustration.py` | 218 | frustration_index, frustration_snapshot | ai-core |
| `evidence_plane/seven_day.py` | 196 | PromotionGateResult | ai-core |
| `legs/books_xero.py` | 184 | connect_check, create_draft_invoice | money-lead |
| `outcomes/reconcile_card.py` | 137 | build_aggregate_card | ops-surface |
| `cortex/depth_guard.py` | 107 | check_delegation | ai-core |
| `budget/drawdown_guard.py` | 103 | shadow_count, verdict | money-lead |
| `doctor/box/primitive.py` | 94 | DeliberationResult | ai-core |
| `now_moves/unified_bus_guard.py` | 83 | wrap | ops-surface |
| `now_moves/kill_seam_closer.py` | 76 | seam_denies | ops-surface |
| `stop_probe.py` | 64 | global_halt, should_yield | ops-surface |

همچنین 2 weighty با importer:
| ماژول | خطوط | note |
|---|---|---|
| `telemetry/neural_apply_evidence.py` | 1106 | EvidenceReport, PainRecord |
| `telegram_center/owner_readiness.py` | 867 | parse_flags_cmd |

---

## کاتالوگ کلاس ۶ — DEAD-OUTPUT / display-only (effector_registry)

رجیستری verified_at 2026-08-08. rg verification انجام شد.

| effector | status | rg verification | note |
|---|---|---|---|
| bcm.learned_pressure | armed-apply | wired via wiring.emit_pain_assessment | **فعال** — BCM APPLY زنده. |
| bcm.weights_bidirectional | display-only | cockpit_readmodel, live_snapshot: all display | وزن BCM فقط نمایش داده می‌شود — تصمیمی نمی‌خواند. |
| hebbian.associations | display-only | deep_think.py:168 context-injection فقط | هببیان به پرامپت تزریق می‌شود نه تصمیم. |
| consolidation.insights | wired | retrieval_router episodic/procedural | بخش conclusions/frontier هنوز dead. |
| deep_dive.smallest_fix | partial (propose-only) | improve.py:318-433 | به proposal وصل شد؛ auto_applicable=False. |
| c6.hypothesis_producer | wired | c6_trigger → RFC card | حلقه بسته فرضیه→آزمایش→RFC. |
| self_model.pathology | display-only | alert فقط | pathology نمایش داده می‌شود نه action. |
| effect_shadow.would_throttle | shadow | observation-only طراحی | سایه bcm. |
| vault_bridge.rag_evidence | wired | retrieval_router context injection | شاهد RAG زنده. |
| latent_space.vector | display-only | zero decision consumer | بردار آگاهی persist ولی مصرف‌کننده تصمیم ندارد. |

**DEAD-OUTPUT واقعی: صفر.** بقیه display-only (5), shadow (1), partial (1), wired (3), armed-apply (1).

**conclusions/frontier از consolidation:**
`retrieval_router` فقط namespace‌های `episodic` و `procedural` را می‌خواند — `conclusions` و `frontier` (بینش‌های 290+ سیکل) هنوز بی‌مصرف‌کننده‌اند. این dead-output subtree است نه کل effector.

---

## کاتالوگ کلاس ۷ — نامرئی تلگرام (بیرون از SCAN_DIRS)

SCAN_DIRS = `("", "telegram_center", "doctor", "heart", "outcomes", "cortex", "budget", "legs", "neural", "chord", "tg")`

پکیج‌هایی با `card()` یا `__init__.py` واقعی **بیرون** از SCAN_DIRS — تلگرام نمی‌بیندشان:

### با manifest (visibility via MANIFEST_ROOTS):
| پکیج | manifest | visibility |
|---|---|---|
| `action_bridge` | `capability-manifest.json` | دیده می‌شود (MANIFEST_ROOTS) |
| `world_discovery` | `capability-manifest.json` | دیده می‌شود |
| `integrations/world_discovery_action` | `capability-manifest.json` | دیده می‌شود |
| `owner_console` | `capability-manifest.json` | دیده می‌شود |
| `unified_control` | `capability-manifest.json` | دیده می‌شود |
| ریشه `_ops` | `capability-manifest.json` (self_goal_cycle) | دیده می‌شود |

### بدون manifest و بدون card — **کاملاً نامرئی:**
| پکیج |理由 | bucket |
|---|---|---|
| `conversation_hub` | ADR-040 façade; OCTOPUS_UNIFIED_CHAT=1 ON; `card()` ندارد; manifest ندارد | ai-core |
| `epistemics` | `may_execute=False` hard-coded; benchmark/bayes only; manifest ندارد | ai-core |
| `hypothesis_engine` | manifest ندارد; card() ندارد | ai-core |
| `math_control` | manifest ندارد; card() ندارد | ai-core |
| `memory` | بزرگترین پکیج؛ manifest ندارد; card() ندارد | ai-core |
| `agi2027_control` | PolicyGate دوم; manifest ندارد; card() ندارد | ops-surface |
| `cognitive` | manifest ندارد; card() ندارد | ai-core |
| `discovery` | manifest ندارد; card() ندارد | ai-core |
| `intel_spine` | manifest ندارد; card() ندارد | ai-core |
| `collab` | manifest ندارد; card() ندارد | ai-core |
| `debate` | manifest ندارد; card() ندارد | ai-core |
| `observability` | manifest ندارد; card() ندارد | ops-surface |
| `octopus_mcp` | manifest ندارد; card() ندارد | ops-surface |
| `now_moves` | manifest ندارد; card() ندارد | ops-surface |
| `reconcile` | manifest ندارد; card() ندارد | ops-surface |

### بدون manifest ولی با card() — **card در SCAN_DIRS نیست = نامرئی:**
(تحقیق نشان داد هیچ پکیج non-SCAN_DIRS ای card() بدون آرگومان ندارد)

---

## کاتالوگ کلاس ۸ — دو-نسخه / unwired (DO-NOT-ARM — dual-stack)

### 8.1 STATUS دروغین: `owner_console`

| فایل | STATUS | واقعیت |
|---|---|---|
| `owner_console/__init__.py:6` | `IMPLEMENTED_NOT_WIRED` | **دروغ** — collaborator.py wired است (OCTOPUS_COLLAB_USE_MODEL=1, talk-discovery ARMED, `handle` production caller). الگوی C-015. |

### 8.2 STATUS واقعی: `unified_control`

| فایل | STATUS | واقعیت |
|---|---|---|
| `unified_control/__init__.py:7` | `IMPLEMENTED_NOT_INTEGRATED` | **درست** — خودش می‌گوید «no runtime caller and owns no canonical state». |

### 8.3 Dual-stack: conversation_hub vs owner_console/collaborator

| مسیر | وضوح | note |
|---|---|---|
| `conversation_hub/` | façade ADR-040 | `OCTOPUS_UNIFIED_CHAT=1` ON — روی MiniApp. `collaborator` را import می‌کند. |
| `owner_console/collaborator.py` | production wired | `OCTOPUS_COLLAB_USE_MODEL=1` — روی تلگرام. |

دو ورودی چت: Hub (MiniApp/统一) و Collaborator (تلگرام). هر دو زنده. **DO-NOT-ARM — dual-stack.**

### 8.4 Dual-stack: PolicyGate دوم

| مسیر | note |
|---|---|
| `agi2027_control/` | پکیج کامل با runtime, rollback, ops_actions. manifest ندارد. card() ندارد. |
| `policy/talk_gate.py` | PolicyGate موجود. |

agi2027_control = لایه دوم حاکمیت (AGI-2027 roadmap). **DO-NOT-ARM — dual-stack.**

### 8.5 capabilities JSON تناقض

| capability | JSON claim | scanner reality |
|---|---|---|
| criticality-v2 | `enabled: false` | OCTOPUS_WIRE_CRITICALITY_OTLP در flags.cmd ? بررسی: NOT SET → DARK |
| chrono-rhythm-cr-b0 | `enabled: true` | OCTOPUS_WIRE_CHRONO_RHYTHM NOT SET → scanner says DARK |
| bayes-engine | `production_caller: NOT_FOUND` | درست — فقط benchmark |

**درس:** `enabled` field در capabilities JSON مستقل از flags.cmd است. حقیقت زنده = scanner.

---

## capabilities/*.json — تطبیق با scanner (7 فایل)

| فایل | capability | truth_status | evidence_level | flag | scanner state |
|---|---|---|---|---|---|
| bayes-engine.json | bayes_engine | TESTED | STRUCTURAL | null | N/A (no flag) |
| chrono-rhythm-cr-b0.json | chrono-rhythm-cr-b0 | TESTED | SHADOW | OCTOPUS_WIRE_CHRONO_RHYTHM | DARK |
| criticality-v2.json | criticality-v2 | SHADOW | SHADOW | OCTOPUS_WIRE_CRITICALITY_OTLP | DARK |
| evidence-control-plane.json | evidence-control-plane | TESTED | TESTED | null | N/A |
| neural-learned-apply.json | neural-learned-apply | TESTED | ARMED | OCTOPUS_NEURAL_LEARNED_APPLY | ON (all 5) |
| spectral-metrics-sensor.json | spectral-metrics-sensor | SHADOW | SHADOW | null | N/A |
| talk-discovery.json | talk-discovery | ARMED | ARMED | OCTOPUS_WIRE_COLLAB | ON (all 5) |

---

## نامزد AI-core (Phase D — حداکثر 8)

از bucket `ai-core` مرتب بر (ارزش مالک × کم‌ریسکی × تعداد خواننده):

### نامزد 1: OCTOPUS_WIRE_CHRONO_RHYTHM
```
NAME: OCTOPUS_WIRE_CHRONO_RHYTHM
WHY_HIDDEN: class 1 (DARK flag) — capabilities JSON says SHADOW, scanner says DARK
WHAT_IT_DOES: Chrono Rhythm CR-B0: یکپارچه‌سازی ریتم circadian با pulse_arbiter.
  wiring.py: chrono_rhythm را در neural_beat فراخوانی می‌کند. advisory-only در JSON.
  حالا trace_only: shadow log در state/pulse/arbiter-shadow.jsonl.
LADDER_NOW: SHADOW (7-day shadow log exists per JSON)
IF_ARMED: ریتم circadian در تصمیم pulse_arbiter مشاوره می‌دهد. age_tick/hash-chain untouched.
PROOF_WITHOUT_MONEY: test_rhythm.py; shadow trace arbiter-shadow.jsonl
RISK: zero external effect. trace_only. advisory.
RECOMMEND: owner-vote-to-arm
COUNCIL: no NO-GO conflict. PEP R20a not relevant (not action_bridge).
```

### نامزد 2: CORTEX_ROUTE_SCORER
```
NAME: CORTEX_ROUTE_SCORER (ON — در scope اسکنر نیست)
WHY_HIDDEN: class 1 — scanner shows ON, card() in capability_registry SCAN_DIRS دارد
WHAT_IT_DOES: route_scorer.py: مدل routing را score می‌دهد. model_router:283-284 پشت پرچم.
  اگر پرچم ON و tier صریح نداده باشد، score را به عنوان hint اضافه می‌کند.
LADDER_NOW: SHADOW (wired, writing scores, observation in test_intelligence/dark_inventory.py)
IF_ARMED: — already ON, behavior already active
PROOF_WITHOUT_MONEY: test_route_scorer (likely); dark_inventory records it
RISK: routing bias — low risk, advisory.
RECOMMEND: leave-dark-to-shadow (already ON; document shadow status)
COUNCIL: no conflict
```

### نامزد 3: self_insight module
```
NAME: self_insight (module, no flag)
WHY_HIDDEN: class 5 (یتیم کد) — card() دارد ولی importer تولیدی صفر. در SCAN_DIRS هست
  ولی فقط از CLI صدا زده می‌شود. تلگرام کارت دارد ولی مالک باید خودش بزند.
WHAT_IT_DOES: یافته → فرضیه → نمره خودش. rank = impact × confidence ÷ cost.
  پبینی‌های قبلی را در اجرای بعدی می‌سنجد. ژورنال self-score دارد.
LADDER_NOW: STRUCTURAL (فایل+تست+card, صفر production caller)
IF_ARMED: periodic self-assessment در digest تلگرام
PROOF_WITHOUT_MONEY: self_insight.py --json خروجی دارد
RISK: zero external effect. فقط‌خواندنی روی کد + ژورنال.
RECOMMEND: owner-vote-to-arm (wire into digest/periodic beat)
COUNCIL: no conflict
```

### نامزد 4: output_critic module
```
NAME: output_critic (module, no flag)
WHY_HIDDEN: class 5 (یتیم کد) — card() دارد ولی importer تولیدی صفر. در SCAN_DIRS هست.
WHAT_IT_DOES: ارگانیسم خروجی خودش را می‌سنجد. نمره کیفیت پیام خودکار.
  حلقه گمشده: 83 پیام بدون نمره. تکراری 35%. spam detection.
LADDER_NOW: STRUCTURAL (فایل+card, importer صفر)
IF_ARMED: هر پیام خودکار نمره می‌گیرد → بهبود کیفیت
PROOF_WITHOUT_MONEY: output_critic.py card() خروجی دارد
RISK: zero external. فقط نمره داخلی.
RECOMMEND: owner-vote-to-arm (wire into output pipeline)
COUNCIL: no conflict
```

### نامزد 5: epistemics package (manifest-less)
```
NAME: epistemics (package)
WHY_HIDDEN: class 7 (نامرئی تلگرام) — SCAN_DIRS ندارد، manifest ندارد، card() ندارد
WHAT_IT_DOES: bayes.py: Bayesian belief update (benchmark only per JSON).
  benchmark.py: systematic evaluation framework.
  claim_builder.py: gate with may_execute=False hard-coded.
  پروسه زنده epistemic sandbox دارد.
LADDER_NOW: TESTED (bayes test exists) / STRUCTURAL (rest)
IF_ARMED: manifest + visibility in telegram → مالک می‌بیند وضعیت epistemic
PROOF_WITHOUT_MONEY: test_epistemic_bayes.py, benchmark.py
RISK: may_execute=False hard-coded — safe by design.
RECOMMEND: shadow-only (add manifest; never arm may_execute)
COUNCIL: ADR-039 §7.2 hard-codes may_execute=False — respect it.
```

### نامزد 6: OCTOPUS_KILL_SWITCH
```
NAME: OCTOPUS_KILL_SWITCH
WHY_HIDDEN: class 1 (DARK flag)
WHAT_IT_DOES: policy/talk_gate.py:36 — اگر ON، ورودی مالک بلوک می‌شود.
  واقعاً kill-switch: talk_gate غیرفعال می‌شود.
LADDER_NOW: TESTED (reader exists, single-line gate)
IF_ARMED: مالک نمی‌تواند از طریق تلگرام حرف بزند.
PROOF_WITHOUT_MONEY: test_talk_gate (likely exists)
RISK: self-inflicted DOS. اما rollback = restart.
RECOMMEND: leave-dark (existential safety — owner should know it exists)
COUNCIL: no conflict. مفید برای emergency.
```

### نامزد 7: conversation_hub (visible but manifest-less)
```
NAME: conversation_hub (package)
WHY_HIDDEN: class 7 (نامرئی تلگرام) — ON (OCTOPUS_UNIFIED_CHAT=1) ولی SCAN_DIRS ندارد،
  manifest ندارد، card() ندارد. MiniApp می‌بیندش ولی تلگرام نه.
WHAT_IT_DOES: ADR-040 façade. classify_intent → route → handle.
  روی collaborator سوار است. زنده و فعال.
LADDER_NOW: SHADOW (ON, wired, real traffic on MiniApp)
IF_ARMED: — already ON. only visibility gap.
PROOF_WITHOUT_MONEY: production traffic on MiniApp
RISK: dual-stack with collaborator. adding manifest = visibility, not activation.
RECOMMEND: shadow-only (add manifest for telegram visibility)
COUNCIL: no conflict. document dual-stack.
```

### نامزد 8: OCTOPUS_WIRE_CRITICALITY_OTLP
```
NAME: OCTOPUS_WIRE_CRITICALITY_OTLP
WHY_HIDDEN: class 1 (DARK flag) — criticality-v2.json says SHADOW, enabled:false
WHAT_IT_DOES: CriticalityV2.observe — spectral metrics → OTLP export.
  capabilities JSON: allowed_effects=[], may_trigger_external_action=false.
LADDER_NOW: SHADOW (JSON says SHADOW, tests exist)
IF_ARMED: spectral metrics via OTLP. but OCTOPUS_OTLP_ALLOW_REMOTE still DARK.
PROOF_WITHOUT_MONEY: test_approval_state.py, test_cognitive_unify.py
RISK: OTLP = telemetry. اگر ALLOW_REMOTE هم روشن = external network.
RECOMMEND: owner-vote-to-arm (without ALLOW_REMOTE = local-only telemetry)
COUNCIL: no NO-GO conflict. separate vote for ALLOW_REMOTE.
```

---

## ۵ کارت رأی برای مالک

### [VOTE 1] Chrono Rhythm — از shadow به armed
```
الان: DARK (capabilities JSON says SHADOW but flag OFF in flags.cmd)
پیشنهاد: arm
اگر arm: فقط این فلگ: OCTOPUS_WIRE_CHRONO_RHYTHM=1
ریسک: zero external. trace_only advisory. pulse_arbiter behavior unchanged.
اثبات بعد: py -X utf8 _ops/dark_capabilities.py | grep CHRONO
نه: age_tick و hash-chain را قاطی نکنید — این فقط advisory است.
```

### [VOTE 2] Output Critic — از یتیم به وصل‌شده
```
الان: invisible (class 5 — یتیم کد، card() دارد، صفر importer)
پیشنهاد: shadow
اگر shadow: periodic output_critic.card() در digest تلگرام (نیاز به wire)
ریسک: zero external. فقط نمره داخلی.
اثبات بعد: output_critic.card() — خروجی باید نمره نشان دهد.
نه: مسیر money/lead را قاطی نکنید — این فقط quality score است.
```

### [VOTE 3] Criticality OTLP — telemetry local-only
```
الان: DARK (class 1 — enabled:false in JSON, flag not in flags.cmd)
پیشنهاد: arm (local-only)
اگر arm: فقط این فلگ: OCTOPUS_WIRE_CRITICALITY_OTLP=1 (ALLOW_REMOTE ممنوع)
ریسک: telemetry فقط — بدون ALLOW_REMOTE zero network. allowed_effects=[].
اثبات بعد: ls _ops/state/criticality/criticality-v2.jsonl | head -5
نه: OCTOPUS_OTLP_ALLOW_REMOTE را هم روشن نکنید — اثر خارجی دارد.
```

### [VOTE 4] conversation_hub — manifest برای دیدن
```
الان: invisible-to-telegram (class 7 — ON در MiniApp ولی SCAN_DIRS ندارد)
پیشنهاد: shadow (visibility only)
اگر shadow: اضافه کردن capability-manifest.json به conversation_hub/
ریسک: zero — فقط visibility. فلگ از قبل ON.
اثبات بعد: py -X utf8 _ops/capability_registry.py | grep conversation_hub
نه: collaborator را تعویض نکنید — dual-stack است. هر دو بمانند.
```

### [VOTE 5] orphan_armed DOCTOR_USE_CENTRAL_ROUTER — پاک‌سازی
```
الان: orphan_armed (=1 در flags.cmd, صفر reader)
پیشنهاد: leave (document و حذف از flags.cmd در جلسه بعد)
اگر arm: هیچ — صفر reader یعنی صفر اثر.
ریسک: zero effect. فقط noise.
اثبات بعد: rg OCTOPUS_DOCTOR_USE_CENTRAL_ROUTER _ops/*.py → خالی
نه: فکر نکنید rename کردن فلگ قابلیت را وصل می‌کند — reader ندارد.
```

---

## چیزهایی که عمداً تاریک ماندند

| آیتم | دلیل |
|---|---|
| OCTOPUS_SMTP_* (4 فلگ) | dangerous — اثر خارجی SMTP. ممنوع در این مأموریت. |
| OCTOPUS_LEAD_DAILY_SEND_CAP | money-lead — خارج از خط حقیقت این فاز. |
| OCTOPUS_SPEND_CAP_* | money-lead — خارج از خط حقیقت این فاز. |
| OCTOPUS_INITIATIVE_UNCAPPED | ممنوع — 3.3 صریح. |
| OCTOPUS_ENFORCE_MONEY_FSM / VALUE_LEDGER | مسیر پول — ممنوع. |
| STUDIO_LLM_CLOUD_VIA_ROUTER | کسب‌وکار زنده — ممنوع. |
| brain_core promote / 4d attach | ممنوع — هرگز هم‌زمان. |
| FUGU_VIA_CENTRAL_GATE | DEPRECATED (4d) — رأی جدا لازم. |
| action_bridge wiring | leave-dark تا PEP R20a — «وصلش کن» = دور زدن شورا. |
| epistemics may_execute | leave-dark — ADR-039 §7.2 hard-coded False. |
| PAT in scout_all_in_one.py | وجود دارد — مقدار هرگز چاپ/کپی نشد. |
| ~72 F-AUTO-ALERT در OCTOPUS-DOCTOR | امضاها با تکرار زیادند — مستند شد اگر به کلاسی بخورد. |
| CORTEX_HYPOTHESIS | ALREADY-ON / council-conflict — نه کشف. |

---

## کار بعدی (نه DEBT-SWEEP، نه اتصال 4d)

1. **VOTE 1–5 بالا** — مالک رأی بدهد.
2. **owner_console STATUS fix** — `__init__.py` هنوز `IMPLEMENTED_NOT_WIRED` می‌گوید ولی collaborator wired است (C-015).
3. **OCTOPUS_DOCTOR_USE_CENTRAL_ROUTER cleanup** — حذف از flags.cmd.
4. **conversation_hub manifest** — برای telegram visibility.
5. **consolidation conclusions/frontier dead-output** — retrieval_router فقط episodic/procedural را می‌خواند.
6. **ORPHAN_SCAN weighty → importer audit** — 18 ماژول کامل بدون caller.
7. **capabilities JSON sync** — criticality-v2 enabled:false vs scanner DARK; chrono enabled:true vs scanner DARK.

---

## منابع و فرمان‌های بازتولید

```bash
# Phase A scanners
py -X utf8 _ops/dark_capabilities.py
py -X utf8 _ops/dark_capabilities.py --json > "00 - Inbox/_scratch-dark.json"
py -X utf8 _ops/flag_drift.py
py -X utf8 _ops/orphan_scan.py

# Phase C verification
rg -n "STATUS = " _ops --glob __init__.py
rg -rn "def card(" _ops --glob "*.py" | grep -v tests/__pycache__
ls _ops/capabilities/*.json

# Dual-stack check
rg -n "conversation_hub" _ops/owner_console/ --glob "*.py"
rg -n "collaborator" _ops/owner_console/collaborator.py
```

---

> HANDOFF: `[[00 - Inbox/2026-08-15 DISCOVERY — Hidden Capabilities Catalog]]`
> فایل scratch: `[[00 - Inbox/_scratch-dark.json]]` (secret-free)
