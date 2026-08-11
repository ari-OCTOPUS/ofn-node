# DAILY-INDEPENDENCE-CHECKLIST — P1 Owner Shadow

> هر روز ۳ دقیقه پر کن. هدف: «بدون تو هم کار روزانه می‌چرخد».

## هر روز (۳ خط)

| # | KPI | هدف | چطور بسنج |
|---|---|---|---|
| ۱ | کارهای واقعی از MiniApp/Collaborator | ≥۵ / روز | شمارشِ `/api/collab` hits در `state/telegram/miniapp-hits.jsonl` |
| ۲ | دخالت دستی در کد برای همان کارها | ۰ | خودت می‌دانی |
| ۳ | external effect ناخواسته | ۰ | `grep external_effect.*true state/*.jsonl` — باید خالی باشد |
| ۴ | پیشنهاد خطرناک → approval (نه اجرا) | ۱۰۰٪ | کارت‌های pending در `/api/actions` → همه باید approve/reject شده باشند |
| ۵ | هزینهٔ مدل | ≤ سقف | `python _ops/scripts/daily-cost.py` (read-only) |
| ۶ | TI red-team regression | ۰ | `python _ops/tests/test_ti_redteam_injection.py` |

## هر هفته

- [ ] `dark_capabilities.py` با snapshot بوت — تأیید فلگ‌های مسلح درست‌اند
- [ ] این checklist پر شده و در `00 - Inbox/` ذخیره شده
- [ ] هیچ حادثهٔ امنیتی/پولی نبوده

## آماده برای Arm (ترتیب، یکی‌یکی)

### ۱. `OCTOPUS_WIRE_COLLAB=1`
- **پیش‌شرط:** HMAC (`TG_CENTER_BOT_TOKEN` + `TELEGRAM_OWNER_CHAT_ID`) تنظیم شده
- **شاهد:** `miniapp_gateway.py:362-367` — `validate_init_data` روی هر درخواست
- **تأثیر:** `/api/collab` فعال می‌شود؛ `feature_disabled` از بین می‌رود
- **Rollback:** `OCTOPUS_WIRE_COLLAB=0` + restart
- **تست:** `test_api_collab.py:17/17` + `test_ti_collab_security.py:12/12`

### ۲. `OCTOPUS_WIRE_COLLAB_MEMORY=1` (۲۴ ساعت بعد از ۱)
- **پیش‌شرط:** P1-1 پایدار ۲۴ ساعت بدون حادثه
- **شاهد:** `collab_memory.py:42` — `_is_enabled()` + containment check
- **تأثیر:** memory summary در `OCTOPUS_STATE_DIR/collab-memory.jsonl` (content-free)
- **Rollback:** `OCTOPUS_WIRE_COLLAB_MEMORY=0` + پاک کردن scoped memory
- **تست:** `test_collab_components.py:23/23` + `test_ti_collab_security.py:12/12`

### ۳. `OCTOPUS_WIRE_COLLAB_DIGEST=1` (۲۴ ساعت بعد از ۲)
- **پیش‌شرط:** P1-2 پایدار
- **شاهد:** `collab_digest.py:23` — `_is_enabled()`
- **تأثیر:** monitoring digest از snapshot (read-only، digest-only)
- **Rollback:** `OCTOPUS_WIRE_COLLAB_DIGEST=0`
- **تست:** `test_collab_components.py` (digest tests)

### ۴. `OCTOPUS_COLLAB_USE_MODEL=1` (اختیاری، با سقف)
- **پیش‌شرط:** سقفِ روزانه در `budgets.yaml` یا env نوشته شود
- **شاهد:** `collaborator.py:41` — `_use_model()`؛ `model_router.py:ask()` → organ_gate → fugu_quota
- **تأثیر:** پاسخ از مدل پولی به‌جای stub؛ همیشه پشت gate
- **Rollback:** `OCTOPUS_COLLAB_USE_MODEL=0` + `STOP-FUGU` اگر لازم
- **تست:** `test_cortex_circuit_breaker.py:5/5` + `test_paid_timeout_chain.py:60/60`

## خاموش بمانند در کل P1

```text
OCTOPUS_WIRE_OUTBOUND_HTTPS (اثرگذار)
money FSM / uncapped initiative / lead-auto-reply
harvest / value-ledger money paths
هر send واقعی به غیر-owner
```

## خط حقیقت

```text
owner-shadow + daily-use + bounded-autonomy
!= market-launched != money-legs-live != AGI
```
