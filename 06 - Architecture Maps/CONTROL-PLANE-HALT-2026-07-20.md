---
type: architecture
status: active
tags: [architecture, stop, halt, safety, control-plane]
created: 2026-07-20
updated: 2026-07-20
---

# قراردادِ توقف/HALT کنترل‌پلین (D-G)

> مرجعِ واحدِ «چه کسی چه STOPی را honor می‌کند». اوراکلِ کانِن = `opslib.master_halted()`
> (HALT-ALL ← STOP معمار، ترتیب‌دار) و `stop_probe.should_yield()`.

## سطوحِ توقف

| سطح | فایل | معنا | چه چیزی می‌ایستد |
|---|---|---|---|
| **HALT-ALL** 🔴 | `_ops/HALT-ALL` | پنیکِ سراسری | **هر** حلقه/watchdog/کاکپیت/launcher/کانکتور — بی‌استثنا |
| **STOP معمار** | `<parent>/STOP` (`F:\backup\STOP`) | توقفِ لایهٔ مادر | همهٔ لوپ‌های پایتون + (اکنون) watchdogها |
| **STOP-ORGANISM** | `_ops/STOP-ORGANISM` | کیلِ بدنهٔ ارگانیسم | organism (پورت 8771)؛ کاکپیت restart را رد می‌کند؛ launcher هرگز حذفش نمی‌کند |
| **STOP-CORTEX** | `_ops/STOP-CORTEX` | کیلِ مغز | cortex (8772) + watchdogش |
| **STOP-LIVE** | `_ops/STOP-LIVE` | کیلِ کاکپیت | live cockpit (8773) + watchdogش |

## ناوردی‌ها (اجراشده + تست‌شده)
1. **پنیکِ سراسری بر هر supervisor مقدم است.** `HALT-ALL` یا `STOP` معمار → هیچ watchdog/کاکپیت/launcher احیا/راه‌اندازی نمی‌کند. `[D-G, 2026-07-20]`
   - `watchdog.py STOP_FLAGS` حالا `HALT-ALL` را دارد (پیش‌تر فقط architect-STOP + STOP-ORGANISM).
   - `live-watchdog.ps1` و `cortex-watchdog.ps1` حالا `HALT-ALL`/architect-STOP را Test-Path می‌کنند (پیش‌تر فقط STOP-LIVE/STOP-CORTEXِ خودشان). `[test_stop_contract t_e]`
   - اوراکلِ واحد: `stop_probe.py` (`--global-halt` → exit 3، fail-closed).
2. **کاکپیت هرگز STOP مالک را ابطال نمی‌کند** (P2، ساختاری — launcher صفر `del STOP-ORGANISM`). `[dd07bab, S1-04]`
3. **STOP-ORGANISM = کیلِ scoped بدنه، نه پنیکِ سراسری.** پنیکِ سراسری = HALT-ALL/STOP معمار.
4. **fail-closed:** هر خطا در خواندنِ STOP = فرضِ yield/halt.

## آنچه هنوز باقی است (owner-gated)
- ثبتِ schtaskِ `OCTOPUS-TG-Center-Watchdog` (اگر خواسته شود) با همین قرارداد.
- سطحِ اختیاریِ `STOP-EXTERNAL` (فقط send/publish/pay را می‌ایستاند) — طراحیِ فاز بعد؛ در v1 اضافه نشد (scope).
- P4: توکنِ per-bootِ کنترل‌پلینِ محلی (curl/اسکریپتِ بی‌Origin) — خارج از Stage-1.

## تست
`_ops/tests/test_stop_contract.py` (5/5) + `test_master_halt.py` (5/5، بدونِ رگرسیون). `.ps1`ها CRLF-سالم، parse بدونِ خطا.
