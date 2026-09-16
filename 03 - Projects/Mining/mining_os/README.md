# mining_os — زیر-OSِ منطبقِ Mining (وصل‌شده، flag-off)

پکیجِ Mining به‌عنوان mini-organism، **دقیقاً روی الگوی Ziman OS / Project-F**: ساخته‌شده + تست‌شده + **وصل‌شده به `_ops/organism.py`** پشتِ فلگِ خاموشِ `OCTOPUS_WIRE_MINING_OS`. با فلگ خاموش، رفتارِ ارگانیسم **بایت‌به‌بایت** بدون‌تغییر است.

## وضعیت (۲۰۲۶-۰۷-۱۹)
- خانه: `03 - Projects/Mining/mining_os/` (هم‌الگوی `ziman_os/`).
- هوک: `_ops/organism.py:712` — additive/flag-off/fail-soft، `_mining_loop.tick(_sub_beat)`.
- راستی‌آزمایی: py_compile ✅ · flag-off بایت‌به‌بایت ✅ · flag-on smoke ✅ · **۲۰ تستِ سبز**.
- فلگ **خاموش**، uncommitted. فعال‌سازی: `ACTIVATION.md`.

## قرارداد
- تنها ورودی به ارگانیسم: `loop.tick(beat)` → `core.mining_beat(state)` — fail-soft، هرگز crash، فقط‌خواندنی.
- **نامتغیرِ صداقت:** تا `state/MINING-STATE.json` دادهٔ واقعیِ ناوگان+برق نداشته باشد → `live=False, signal="skeleton"`.
- `secrets=()` · `spawn=0` · `$0` · stdlib-only · governance fail-closed (D-10/D-11/D-20 + گیتِ برق).

## اجزا
```
core.py            mining_beat — منطقِ ضربان
loop.py            tick(beat) — نقطهٔ اتصال به heartbeat (هم‌الگوی ziman_os.loop.tick)
state.py           اسکیمای MINING-STATE.json (جایگزینِ org['mining']ِ شکسته — C13)
organs/governance  گیت‌های fail-closed (اقدامِ ممنوع/برق/wallet)
organs/death_watch معیارِ D2 (بقا، نه payback)
brains/hardware 🛠 خلاصهٔ ناوگان · brains/coin ⛏ کاندیدها
ui/telegram        منوی ۶-گزینه‌ای (mo:) + پینِ زنده + verdict-cards
tests/             ۲۰ تستِ pure-unit (stdlib)
```

## تست (بدونِ pytest)
```
python run_tests.py
```

> ⚠️ این لایه هرگز به `Ai bots/fleet` (SSH/subprocess واقعی) وصل نمی‌شود؛ کنترلِ ماینر پشتِ P5+ و کارتِ تأیید است. پول همیشه **P7**.
