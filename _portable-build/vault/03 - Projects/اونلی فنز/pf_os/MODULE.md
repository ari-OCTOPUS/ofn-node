# pf_os — Project-F OS

> نقشهٔ ماژول · ۲۰۲۶-۰۸-۰۳ · نسخهٔ مستقلِ قابل‌حمل

## نقش
هستهٔ OS ماژولارِ Project-F. یکپارچه‌سازی با ارگانیسمِ مرکزی اختاپوس از طریقِ cortex (HTTP) و saba-bridge (file-based). همه additive، flag-off، $0 آفلاین، stdlib-only.

## Entry points (با `__main__`)
| فایل | دستور | flag | پورت/مسیر |
|---|---|---|---|
| `loop.py` | `python -m pf_os.loop` | `OCTOPUS_WIRE_PROJECTF_LOOP` | tick هر `PF_OS_TICK_SECONDS` (۳۰۰s) |
| `api.py` | `python -m pf_os.api` | `OCTOPUS_WIRE_PROJECTF_API` | `127.0.0.1:8780` |
| `bridge_beat.py` | `python -m pf_os.bridge_beat` | `OCTOPUS_WIRE_SABA_BRIDGE` | single-shot consumer |
| `run_saba.py` | `python -m pf_os.run_saba` | (token-driven) | shadow/live mode |

## کتابخانه‌ها
`config` · `cortex_client` · `events` · `event_bus` · `telemetry` · `capabilities` · `actuator` · `eval_loop` · `brain` · `bridge` · `spine` · `saba_link` · `singleton` · `learning_bus`

## Env vars
| کلید | پیش‌فرض | نقش |
|---|---|---|
| `PF_ROOT` | دو سطح بالاتر | ریشهٔ Project-F |
| `OCTOPUS_VAULT` | drive-relative رد | ریشهٔ vault اختاپوس |
| `OCTOPUS_CORTEX_URL` | `http://127.0.0.1:8772` | cortex مرکزی |
| `PF_OS_PORT` | `8780` | پورتِ API |
| `PF_OS_TICK_SECONDS` | `300` | دورهٔ tick |
| `PF_STUDIO_DIR` | `<PF_ROOT>/studio` | مسیرِ studio (تست) |
| `PF_AUDIT_FILE` | `<root>/langar/approvals.jsonl` | فایلِ حسابرسی (تست) |
| `PF_PII_BLOCKLIST` | (خالی) | فایلِ blocklist اضافی |

## Flags (default OFF)
`OCTOPUS_WIRE_PROJECTF_LOOP` · `OCTOPUS_WIRE_PROJECTF_API` · `OCTOPUS_WIRE_SABA_BRIDGE` · `OCTOPUS_WIRE_PROJECTF_CORTEX` · `OCTOPUS_WIRE_PROJECTF_EVAL` · `OCTOPUS_WIRE_PROJECTF_SPINE`

## وابستگی‌ها
- **درون‌پروژه‌ای**: `brain/dual_brain_v3`، `brain/store` (KPIRollup)، `studio/*` (در run_saba live)
- **اختاپوس**: `_ops/events.py`، `_ops/neural/*` (via orchestrator، نه مستقیم)
- **خارجی**: صفر (stdlib-only)

## State
- محلی: `pf_os_state/` (lock files، STOP-PFOS)
- اشتراکی: `{VAULT}/_ops/state/saba-bridge.jsonl` (هرگز PII)

## تست‌ها
`test_brain_saba` · `test_bridge_api_loop` · `test_bridge_beat` · `test_config` · `test_learning_bus` · `test_singleton` · `test_spine`
