# P5 — Arm-Gate: owner runbook + gate card

**چه چیزی ساخته شد:** `_ops/arm_gate.py` — یک گیتِ defense-in-depth که «قابلیتِ محیطیِ» ۱۲ لیورِ ACTIVATION را می‌بندد. یک capabilityِ خطرناک فقط وقتی باز می‌شود که **علاوه‌بر** فلگِ ACTIVATION، یک **arm-tokenِ تازه** (TTL ۲۴h) هم حاضر باشد — و برای خود-اصلاحی‌ها (code_autonomy/self_improve_auto/replicate) **دو توکن (دو-کلید)**. `test_arm_gate` ۱۶/۱۶.

**چرا:** درسِ فرارِ ژوئیهٔ ۲۰۲۶ — capability نباید «خاصیتِ محیطیِ همیشه‌حاضر» باشد؛ باید یک استثنای scoped/تازه/آگاهانه باشد. حضورِ فلگ روی دیسک دیگر کافی نیست.

**ناوردی‌های ایمنی:** فقط **سخت‌تر** می‌کند (هرگز چیزی را بازتر نمی‌کند) · fail-closed در همهٔ خطاها · هرگز arm-token/kill-switch/ACTIVATION نمی‌نویسد · وقتی `OCTOPUS_REQUIRE_ARM` خاموش است **byte-identical** با رفتارِ امروز.

**وضعیتِ wiring:** `code_autonomy.active()` وصل شد (نمایشی؛ dormant، صفر اثرِ زنده). `cortex_paid`/`self_improve_auto`/`replicate`/`governor_llm` در registry هستند؛ wiringشان در نقاطِ متناظر (paid_gate و…) گامِ بعد است (عمداً paid را دست نزدم تا cortexِ meteredِ فعلی نشکند).

---

## چطور روشن کنی (owner)

**۱) فعال‌سازیِ enforcement** (تا آن موقع byte-identical):
```
set OCTOPUS_REQUIRE_ARM=1
```
(در `_ops/OCTOPUS-flags.cmd` یا env؛ از restart بعدی خوانده می‌شود.)
⚠️ به‌محضِ روشن‌شدن، هر capabilityِ خطرناک بدونِ arm-tokenِ تازه **رد** می‌شود.

**۲) arm کردنِ یک capability** (اقدامِ آگاهانهٔ مالک — یک فایل JSON بنویس):
`_ops/state/arm/<capability>.arm.json`:
```json
{ "capability": "code_autonomy", "armed_at": <epoch-seconds-now> }
```
- **دو-کلید** (code_autonomy/self_improve_auto/replicate): فایلِ دومِ `<capability>.arm2.json` هم لازم است (هر دو تازه).
- **TTL ۲۴h:** توکنِ کهنه منقضی می‌شود → برای ادامه دوباره arm کن (این دقیقاً «قابلیتِ محیطیِ دائمی» را از بین می‌برد).
- **سخت‌سازیِ اختیاری (owner-only binding):** `set OCTOPUS_ARM_SECRET=<hex>` و فیلدِ `"hmac"` را در توکن با `HMAC_SHA256(secret, "cap|armed_at|key")` بگذار؛ آن‌گاه توکنِ بی‌امضا/جعلی رد می‌شود.

**۳) گزارش:** `arm_gate.arm_status()` وضعیتِ armed/reason هر capability را می‌دهد (برای /status و پنل).

## Rollback
`set OCTOPUS_REQUIRE_ARM=` (خالی) → بازگشتِ آنی به رفتارِ قبل. بدونِ migration، بدونِ state.

## مرزها
- این arm-gate جایگزینِ kill-switch یا capability_gate نیست — **لایهٔ اضافه** است.
- `merge_or_deploy`/`replicate` همچنان در `SELF_IMPROVEMENT_FORBIDDEN` می‌مانند؛ arm-gate فقط دروازهٔ arm است، نه اجازهٔ auto-apply.
