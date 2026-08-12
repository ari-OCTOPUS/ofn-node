---
type: architecture
status: active
created: 2026-08-11
updated: 2026-08-12
tags: [octopus, heart, brain, 4d, status, integration]
related:
  - OCTOPUS-MEMORY-TRUTH-MAP
  - OCTOPUS-METAPHOR-DECODE-ENGINEERING-REALITY
  - ADR-033
  - ADR-034
  - ADR-035
  - 4d_system/DEPRECATED.md
  - _ops/state/ORGANISM-STATE.json
  - _ops/state/pulse/arbiter-latest.json
---

# Hearts · Dual Brains · 4D — وضعیت صادق (به‌روز 2026-08-12)

> **توضیح‌دهنده است، نه SoT اجرایی.**  
> SoT = `ORGANISM-STATE` + registries + ADR + test evidence.  
> هدف: جوابِ «وصل‌اند؟ دیباگ‌اند؟ به یکپارچه‌سازی امروز وصل‌اند؟»

## حکمِ یک‌خطی

**سه‌قلب + داور نبض LIVE و sleep را می‌رانند.** دو مغزِ زنده = **cortex + business_brain** داخل `_ops`. **`4d_system` / Super-Governor به ارگانیسم وصل نیست** (standalone/SPEC). پل حافظه (`research_ingest` / `self_loop_ingest`) LIVE. **ADR-035:** `OCTOPUS_NEURAL_LEARNED_APPLY=1` + protective_skip اجرایی (2026-08-12). Integration Wave بسته + CAPABILITY-OK.

**شاهد موج:** `_ops/state/adr-033/reports/INTEGRATION-WAVE-2026-08-11/07-FINAL-VERDICT.md` · ADR-035 evidence · Watch `WATCH-SMART-2026-08-12/`

---

## ۱) قلب‌ها

| قطعه | وضعیت | شاهد |
|---|---|---|
| `cardiac` | LIVE · رأی به arbiter | `arbiter-latest.json` period≈42s · `ORGANISM-STATE.cardiac.enabled=true` |
| `control_law` | LIVE · رأی | period≈126s · velocity-tracking |
| `rhythm` (`chrono_rhythm`) | LIVE · رأی | period≈81s · STEADY/GREEN |
| `pulse_arbiter` | **WIRED · wire_open=true · driver=consensus** | `effective_period_s≈75.25` · color GREEN · 3/3 present |
| hybrid `heart/shadow` production wire | **CLOSED (عمدی)** | Gate-0 Δ_self=0 + hash قانون≠SIM-REPORT |
| `work_pump` | WIRED (`OCTOPUS_WIRE_HEART_WORK`) | heart_beat → research/cadence jobs |
| استعاره‌ی «سه‌قلب» | explanatory | Metaphor Decode — اختیار نمی‌دهد |

**دیباگ:** مسیر sleep در `organism.py` از arbiter می‌خواند وقتی `wire_open`. دو «حقیقت قلب» همزمان: arbiter باز / hybrid بسته — این باگ نیست، containment است.

---

## ۲) دو مغز (سطح‌های زنده)

| مغز | مسیر | وضعیت | به improve/حافظه؟ |
|---|---|---|---|
| مغز مرکزی (cortex) | `_ops/cortex/` | **BUILT + LIVE** | بله — improve/synthesis/self_model |
| مغز دوم کسب‌وکار | `business_brain.py` | **BUILT + LIVE** (innervation 🟢) | بله → upgrades-digest |
| Doctor self_knowledge | `doctor/self_knowledge.py` | LIVE (wire) | بله → self_loop `self_knowledge` |
| brain_core parity | ORGANISM-STATE | **SHADOW-LIVE** · matched=0 / compared≈1200 | soak؛ promote نکن |
| Neural BCM / learned-apply | `_ops/neural` | **ARMED · APPLY=1 (ADR-035)** | beat-local `protective_skip` فقط؛ rollback=`APPLY=0` (ADR-034) |

Innervation زنده: **coverage 100% · dead_spots=[]** (spine/heart/cortex/work/business/learning/selfmodel/…).

---

## ۳) 4D / NBB / Super-Governor

| قطعه | وضعیت | معنی |
|---|---|---|
| `4d_system/` Streamlit Brain-OS | **BUILT standalone · DEPRECATED vs live** | به `_ops` import ندارد؛ لانچ نمی‌شود |
| NBB-CP کد | skeleton موجود · **unwired** | MemoryGate/ADR-033 را لمس نمی‌کند |
| Second Brain Super-Governor (۸ مغز) | **SPEC_NOT_BUILT** | سند معماری؛ ساخته نشده |
| نقشهٔ قدیمی `06/…/4D.md` | archived | با `4d_system/DEPRECATED.md` بخوان |

**Canonical زنده:** `_ops/cortex` + `model_router` — نه daemonِ 4d.

---

## ۴) وصل به یکپارچه‌سازی امروز (Memory / ADR)

| پل | کد | شواهد دیسک (پس از backfill 2026-08-11) | اختیار؟ |
|---|---|---|---|
| ADR-033/034 | ACCEPTED · APPLY=0 | restart evidence + WORKLOCK suites | PolicyGate فقط |
| `research_ingest` | wired در `web_research.run_and_persist` | `state/memory/research-ingest.jsonl` | خیر |
| `self_loop_ingest` | wired در improve/synthesis/self_model/part_loops/self_knowledge/chrono | `state/memory/self-loop-ingest.jsonl` | خیر |
| MemoryGate | flags ON | `memory.db` (~55+ rows پس از backfill) | citation/veto فقط |
| 4d → MemoryGate | **NO** | — | — |

**گپ دیباگ باقی:** ~~رشد خودکار trail~~ → **verify شد (2026-08-12 00:06):** `improve.run` زنده trail را +۸ کرد (dedupe skip روی محتوای قبلی). research-ingest هنوز منتظر cycle تحقیق بعدی است.

---

## ۵) ماتریس «ساخته / درست / دیباگ»

| لایه | ساخته؟ | درست؟ | دیباگ؟ |
|---|---|---|---|
| سه‌قلب + arbiter | ✅ | ✅ sleep≈75s | ✅ GREEN |
| hybrid production wire | ✅ کد | ⛔ بسته (عمدی) | نیاز SIM-rehash اگر بخواهی باز شود |
| cortex + business brain | ✅ | ✅ innervated | ✅ |
| خودآگاهی/خودترمیمی pulses | ✅ | ✅ می‌نویسند | ⚠️ ingest تا reload کامل خودکار نیست |
| Memory Truth Map bridges | ✅ کد+تست | ✅ may_authorize=false | ⚠️ نیاز reload + مشاهدهٔ رشد trail |
| 4d_system / Super-Gov | ✅/SPEC | ❌ وصل به زنده نیست | N/A برای runtime |
| brain_core promote | ❌ | matched=0 | SHADOW بماند |

---

## Precedence

اگر این نوت با runtime تعارض داشت: **ORGANISM-STATE + arbiter-latest + registries برنده**؛ تعارض را ADR/inventory ثبت کن.
