# REPORT-P3

## خط حقیقت

```text
octopus-product-beta-documented + demo-script-ready + onboarding-ready + allowlist-template-ready
!= mass-market-launched != multi-user-live != AGI
```

## Done

### P3.1 — DEMO-SCRIPT.md
- ۵ دقیقه نمایش: خانه → پرسش → همکار → تأیید → توقف
- با شواهد واقعی (تب‌های MiniApp از `index.html:46-55`)
- خط حقیقت دمو

### P3.2 — BETA-ALLOWLIST.md
- allowlist مکانیزم (HMAC + chat_id از `validate_init_data:188`)
- دو روش گسترش: env یا hash
- قواعد بتا (deny پیش‌فرض، rate-limit، approval gate)
- جدول کاربران (مالک فعال، معتمدان pending)

### P3.3 — ONBOARDING.md
- یک‌صفحه‌ای: چه می‌کند / چه نمی‌کند / چطور استفاده / چطور متوقف / امنیت / هزینه
- برای کاربر بتا — ساده و صادق

### P3.4 — UX verification
- ۹ تب در MiniApp: خانه، تأییدها، پول، لیدها، کارها، سیستم، اسکن‌ها، اعلان‌ها، پرسش
- تب پرسش شامل همکار (`askCollab` chip)
- `/api/collab` در POST whitelist (`miniapp_gateway.py:475`)
- rate-limit اشتراکی با /api/ask: ۶ درخواست در ۳۰ ثانیه (`:131-132`)
- `/api/restart` برای توقف اضطراری (`:669`)

### P3.5 — Budget/rate-limit verification
- actions: ۱۲ درخواست در ۱۰ ثانیه (`:115-116`)
- ask/collab/mirror: ۶ درخواست در ۳۰ ثانیه (`:131-132`)
- monthly spend: AU$30 (یا US$200 تا ۲۰۲۶-۰۸-۱۳)
- daily fugu cap: ۳۰۰ پیش‌فرض
- fail ceiling: ۱۰

### P3.6 — Kill/stop documentation
- `/stop` در تلگرام → STOP-ORGANISM file
- `/api/restart` در MiniApp → approval card + restart_control
- fail-closed: اگر چیزی خراب شود، halt می‌زند

## Evidence

```text
MiniApp tabs:      _ops/telegram_center/miniapp/index.html:46-55
/api/collab route: _ops/telegram_center/miniapp_gateway.py:739-784
Rate limits:       _ops/telegram_center/miniapp_gateway.py:115-132
Kill path:         _ops/telegram_center/center.py:16-18, 63-64
Budget caps:       _ops/budget/budgets.yaml + fugu_quota.py
Collab security:   test_ti_collab_security.py:12/12
API collab:        test_api_collab.py:17/17

Demo script:       _ops/DEMO-SCRIPT.md
Allowlist:         _ops/BETA-ALLOWLIST.md
Onboarding:        _ops/ONBOARDING.md
```

## Gates

- [x] دمو ۵دقیقه‌ای بدون عذرخواهی معماری — DEMO-SCRIPT.md آماده
- [ ] KPI ۷ روز بتا — **PENDING (shadow تازه شروع شده)**
- [x] red-team collab همچنان pass — 12/12 + 17/17
- [ ] merge-to-master — **DONE (fast-forward)**

## Flags touched

```text
OCTOPUS_WIRE_COLLAB=1          → ARMED (5 processes confirmed)
OCTOPUS_FUGU_TIMEOUT_NOT_PROVIDER_FAIL=1 → ARMED
OCTOPUS_WIRE_OUTBOUND_HTTPS=1  → ARMED (pre-existing)
```

## NOT done / blocked

1. **Multi-user allowlist code** — propose-only، نیاز به تغییر `validate_init_data`
2. **7-day beta KPI** — نیاز به دادهٔ واقعی
3. **Golden traces** — نیاز به sessionهای واقعی (پس از ۷ روز)

## Owner decisions needed

1. **کاربر بتای بعدی کیست؟** — chat_id او را اضافه کن
2. **مدل پولی برای collab؟** — `OCTOPUS_COLLAB_USE_MODEL=1` با سقف

## خلاصهٔ کل مسیر P0-P4

```text
P0 ✅ TI + security + PRODUCT-V1 committed
P1 ✅ Arm plan + daily checklist + REPORT-P1 committed
P2 ✅ Route policy + chaos matrix + evidence ladder + REPORT-P2 committed
P3 ✅ Demo + allowlist + onboarding + REPORT-P3 committed
P4 ✅ Bridge contract + pilot plan + REPORT-P4 committed
run_all.py ✅ 597 entries (588 + 9 TI)
Merge ✅ Fast-forward to master
Arm ✅ COLLAB + TIMEOUT live
```
