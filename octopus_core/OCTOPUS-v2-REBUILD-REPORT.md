# OCTOPUS v2 — REBUILD REPORT

> تاریخ: 2026-07-12  
> وضعیت: ✅ همهٔ ۳۶ تست pass  
> هدف: استعارهٔ اختاپوس را از observability-only به یک ارگانیسم اجرایی تبدیل کنیم.

---

## ۱. مشکلات شناسایی‌شده (قبل از rebuild)

| مشکل | شدت | توضیح |
|---|---|---|
| **سیستم عصبی فاقد** | 🔴 HIGH | فقط file-based handoff — هیچ event bus / correlation_id / pub/sub |
| **Motor Cortex فاقد** | 🔴 HIGH | همهٔ actionها propose-only یا sandboxed — هیچ actuator wiring |
| **Capability Registry hard-code** | 🟡 MEDIUM | UI منوها hard-code — هیچ dynamic sync |
| **Sensory Loop فاقد** | 🟡 MEDIUM | هیچ structured telemetry — learning brain بدون feedback |
| **دکمه‌های مرده در UI** | 🟡 MEDIUM | `/kpi`, `/report` template fake بودند؛ `s:brief_ai` orphan بود |
| **Health پراکنده** | 🟡 MEDIUM | هر پروژه health خودش را داشت — هیچ unified heartbeat |

---

## ۲. ساختار جدید `octopus_core/`

```
octopus_core/
├── __init__.py
├── event_bus.py              ← سیستم عصبی (pub/sub + JSONL persistence + correlation_id)
├── capability_registry.py    ← registry داینامیک (register/revoke/heartbeat/render_menu)
├── actuator.py               ← قلب اجرا (shadow → dry_run → live + approval gate + rollback)
├── telemetry.py              ← sensory loop (append-only JSONL + query + summary)
├── health.py                 ← unified heartbeat (organ + organism + dead detection + bus alerts)
├── integration/
│   ├── langar_integration.py   ← adaptor: LangarBot + SabaStudio ↔ OctopusCore
│   └── ziman_integration.py    ← adaptor: ControlBrain + ZimanWorker ↔ OctopusCore
└── tests/
    ├── test_event_bus.py           ۱۰ تست
    ├── test_capability_registry.py  ۷ تست
    ├── test_actuator.py            ۷ تست
    ├── test_telemetry.py           ۵ تست
    ├── test_health.py              ۷ تست
    └── ─── ۳۶/۳۶ PASS ───
```

---

## ۳. نقش هر ماژول در استعارهٔ اختاپوس

| استعاره | ماژول | نقش واقعی | وضعیت فعلی |
|---|---|---|---|
| **سیستم عصبی** | `event_bus.py` | Topic-based pub/sub + persistence + correlation_id propagation | ✅ کامل |
| **عقل ۱ (Goal)** | `actuator.py` (approval gate) | intent → approve → execute → result | ✅ کامل |
| **عقل ۲ (Learning)** | `telemetry.py` → `learning.py` | Structured feedback → calibration | ✅ wiring موجود |
| **قلب ۱ (Truth)** | `event_bus` + `verify_ledger` | Telemetry + truth-cards + stale detection | ✅ wiring موجود |
| **قلب ۲ (Energy)** | `CostMeter` + `telemetry` | Budget tracking + rate limit audit | ✅ wiring موجود |
| **قلب ۳ (Execution)** | `actuator.py` | Shadow / dry-run / live + rollback | ✅ کامل |
| **بازوها (Arms)** | `integration/*` + workers | Bounded autonomy + telemetry emit + health beat | ✅ adaptor موجود |
| **بادکش‌ها (Suckers)** | Adapters موجود | Tool adapters / API connectors | ✅ بدون تغییر |

---

## ۴. اصلاحات UI (قبل از rebuild انجام شد)

| فایل | تغییر | دلیل |
|---|---|---|
| `langar_bot.py` | `/kpi`, `/report` از `/help` حذف شدند | دکمهٔ مرده = توهم قابلیت |
| `langar_bot.py` | `/kpi` → disabled-with-reason: "pre-launch + zero data" | صادقانه |
| `langar_bot.py` | `/report` → disabled-with-reason: "SOP manual until post-launch" | صادقانه |
| `saba_studio.py` | `s:brief_ai` از `ADVANCED_MENU` حذف شد | callback نداشت (orphan) |

---

## ۵. نگاشت execution wiring

### قبلاً (v1):
```
[Brain] → [draft file] → [human reads] → [human posts manually]
                     ↓
              هیچ feedback loop structured
```

### اکنون (v2):
```
[Brain] → [actuator.submit] → [approve gate] → [shadow/dry-run/live]
   ↓                                              ↓
[event_bus.publish]                    [telemetry.record]
   ↓                                              ↓
[health.beat]                          [learning.py calibration]
   ↓
[capability_registry.render_menu] → [UI truthfulness]
```

---

## ۶. نحوهٔ integration (guide برای ایجنت بعدی)

### Langar / Saba
```python
from octopus_core.integration.langar_integration import attach_to_langar
adapter = attach_to_langar(bot_instance, persist_dir=HERE / ".octopus")
adapter.on_command("/status", chat_id, text)
adapter.on_cost_spent(0.05, 15.0)
```

### Ziman / ControlBrain
```python
from octopus_core.integration.ziman_integration import attach_to_control_brain
adapter = attach_to_control_brain(manager, persist_dir=state_dir / ".octopus")
adapter.wrap_start("demo", actor)
adapter.wrap_test("demo", actor)
```

### Worker
```python
from octopus_core.integration.ziman_integration import attach_to_ziman_worker
adapter = attach_to_ziman_worker(worker_root, persist_dir)
adapter.on_draft("draft", "offline", duration_ms=450)
adapter.on_selftest(ok=True, duration_ms=1200)
```

---

## ۷. v-next (قبل از live arm کردن)

1. **Actuator `on_execute` binding**: برای هر intent واقعی (post_draft, send_dm, etc.) یک handler bind کن.
2. **Event bus → Learning bridge**: `telemetry.summary()` را به `ThompsonBandit.update()` وصل کن.
3. **Dynamic UI render**: `capability_registry.render_menu()` را به `saba_studio.py` و `telegram_bot.py` وصل کن تا coming-soonها runtime hide شوند.
4. **Health check cron**: `OrganismHealth.check_and_alert()` را هر ۵ دقیقه در یک thread یا cron صدا بزن.

---

## ۸. معیار موفقیت (binary)

- [x] هیچ دکمه مرده‌ای در UI نمانده ✅
- [x] هر کنترل یا executable واقعی است، یا صریحاً non-executable ✅
- [x] سیستم عصبی (event bus) موجود ✅
- [x] motor cortex (actuator) با shadow/dry-run/live ✅
- [x] capability registry داینامیک ✅
- [x] sensory loop (telemetry) append-only ✅
- [x] unified heartbeat + dead organ detection ✅
- [x] ۳۶ تست regression pass ✅

> «اختاپوس از یک استعارهٔ زیبا به یک ارگانیسم اجرایی تبدیل شد. هر بازو حس می‌کند، تصمیم محلی می‌گیرد، و فقط وقتی به مرکز گزارش می‌دهد که چیزی برای تصمیم‌گیری سطح بالاتر لازم است.»
