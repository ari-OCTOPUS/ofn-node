---
type: project
kind: area
project: "[[03 - Projects/Mining/PROJECT]]"
status: active
owner: آری
risk_level: medium
autonomy_level: read-only
tags: [mining, crypto, orange-pi, esp32]
created: 2026-07-03
updated: 2026-09-07
---

# پروژه: Mining

> 🏗️ **رکنِ ساخت:** [[04 - Architect System/MYCELIAL-MASTER-SPEC|MYCELIAL-MASTER-SPEC]] — این پروژه یک node در §۳ رجیستریِ اتصال است (build/test/delete پشتِ verdict).

## Mission

شکار کوین‌های نوظهور CPU/ARM-پذیر با ناوگان کوچک (Orange Pi 5 Pro + ESP32) — آزمایش بلندمدت با معیار مرگ **survival-based** (D2)، نه payback. **tenant #3** (D-26)؛ برای architect فقط INFORM — execution مالی HARD_STOP (D-10).

## Current state (شواهد)

- کد بات‌ها: `Ai bots/` (sentinel، QuantumAlphaBot، deploy) و `Robo-data/` — .envها به secrets-export منتقل شد؛ توکن‌های hardcode در config.py/setup_main.sh redact شدند `[Verified: Phase 0]`
- `Mining-1/Hcash/config.env` (۳۶ متغیر نود) منتقل شد — pointer جایش است `[Verified]`
- کیف پول Monero: seed در چرخش — [[ROTATION_CHECKLIST]] ردیف ۱ `[Verified]`
- معماری بات‌ها: `Ai bots/ARCHITECTURE.md` `[Verified: وجود فایل]` · ماینرها (nanominer/xmrig/gminer) در `_Archive`
- سود/هزینه واقعی: `[To measure]` — هیچ عدد profitability تأییدشده‌ای ثبت نشده

## Assets & resources

**۱۶۲ نود** `[Owner-confirmed 2026-07-28 — D-008]` = ۱۶ Orange Pi 5 Pro + ۱۴۰ ESP32 + ۲ FPGA · همه در **سیدنی** · **همه خاموش** · برق: **خورشیدیِ نصب‌شده و فعال** → قیدِ ساختاری <$0.05/kWh **پاس**

> **⚠️ قیدِ صداقت:** ۱۴۰ ESP32 **ماینر نیستند** (سنسور/تله‌متری) — پایهٔ هش = **۱۶** نود. هر عددِ هش‌ریتی که ۱۶۲ را ضرب کند غلط است. شمارش قفل شد ولی IP/سلامتِ تک‌نود هنوز `[To measure]` است: [[03 - Projects/Mining/Hardware Registry & Runbook|رجیستری]].

## Active workstreams

1. تکمیل [[03 - Projects/Mining/Hardware Registry & Runbook|رجیستری سخت‌افزار]] (مالک). 2. اولین کوین با [[03 - Projects/Mining/Coin Scouting Framework|چارچوب شکار کوین]]. 3. راه‌اندازی مجدد بات‌ها بعد از rotation.

## KPIs

نود فعال/کل `[To measure]` · کوین‌های تحت آزمایش · uptime ناوگان `[To measure]` — payback و نقدشوندگی = فیلد اطلاعاتی، **نه** معیار قطع (D2)

## Agent interface

- **می‌خواند:** این manifest، رجیستری، لاگ آزمایش کوین‌ها، دیتای عمومی شبکه‌ها.
- **می‌نویسد:** گزارش death-watch، پیشنهاد کوین جدید (draft)، هشدار برق/آپتایم.
- **verdict انسانی:** هر خرید/فروش/برداشت، هر deploy روی نود، شروع/توقف هر آزمایش.
- **ممنوع:** SSH مستقیم به نودها (D-20 — فقط مسیر repo+deploy gate)؛ دسترسی به کیف پول (D-11).
- **Security Gate:** read-only تا بسته شدن CRITICALها.

## Open blockers

**۱۶۲ نودِ خاموش** (راه‌اندازیِ فیزیکی — کارِ مالک) · seed کیف پول در انتظار چرخش · IP/سلامتِ تک‌نود اندازه‌گیری‌نشده (MIN-V4) · بات‌ها بدون .env (به‌عمد، تا rotation) · **MIN-V6: «عوض کردنِ کوین» با D-10 در تضاد — منتظرِ رأیِ مالک**

## Active Context


- PARKED — فعال نیست؛ بازگشایی فقط با رأی مالک؛ فلگ MINING_OS روشن (بدهی پیکربندی).
- ۳ قدم بعدی: هیچ تا رأی بازگشایی.
- باز: بازگشایی یا آرشیو؛ خاموش‌سازی فلگ‌های مرده.

## Progress

- 2026-09-07: PARKED تأیید؛ اسکن ۱۰-جنبه‌ای جدا از سیزن.
- 2026-09-07: اسکن ۱۰-جنبه‌ای: جدا از سیزن (PARKED)؛ باینری‌ها ۲.۳۹GB.
- چه کار می‌کند: زیر-OSِ `mining_os` **واقعاً به اختاپوس وصل شد** (flag-off، ۳۲+۹ تستِ سبز) · لگِ `mining_leg` در `business_legs` با `live=False` صادق · تاپیکِ ⛏ تلگرام = ۲۴ · کدِ بات‌ها موجود (خاموش) · چارچوب‌ها تعریف شد · **UIِ عددیِ ماینینگ ساخته شد (۲۰۲۶-۰۸-۰۱): کارت/دایجستِ ۱۶۲ + اندازه‌گیری‌نشده، ثبتِ نیتِ توقف، رسیدِ سوییچ، کارتِ swap، فیکسِ age_days — همه پشتِ فلگ/فقط-ثبت**
- چه مانده: راه‌اندازیِ فیزیکیِ نودها · پرکردنِ `mining_os/state/MINING-STATE.json` با ناوگانِ واقعی (تا آن‌موقع `live=False` درست است) · rotation · اولین آزمایشِ ثبت‌شده · **دکمه‌های DM برای swap/stop باید به `center.py` وصل شوند (به رأیِ مالک برای اضافه‌کردنِ `mo` به گروه)** · مسیرِ زندهٔ swap/switch/stop هنوز اثبات‌نشده
- مشکلات شناخته: هیچ عددِ profitability معتبری نداریم · وضعیتِ فیزیکیِ تک‌تکِ نودها نامعلوم · `test_mining_leg.py`/`test_mining_wiring.py` قرمزِ **از پیش‌موجود** (phantom — کلاسِ `MiningLeg` و `wiring.make_mining_leg` هرگز ساخته نشدند)؛ ربطی به سیم‌کشیِ تازه ندارند

## Next actions

- [ ] **مالک:** OPI-01 را روشن کن + Tailscale → اولین ردیفِ واقعیِ [[03 - Projects/Mining/Hardware Registry & Runbook|رجیستری]]
- [ ] **مالک:** رأیِ [[03 - Projects/Mining/VERDICT_QUEUE|MIN-V6]] — swap خودکار یا فقط پیشنهاد؟
- [ ] **مالک:** چرخش Monero seed + کلیدها
- [ ] **مالک:** کامیتِ دیفِ سیم‌کشی + (اختیاری) روشن‌کردنِ `OCTOPUS_WIRE_MINING_OS` — [[03 - Projects/Mining/mining_os/ACTIVATION|ACTIVATION]]
- [ ] بنچِ هش‌ریتِ واقعی روی OPI-01 (پس از روشن‌شدن)
- [ ] آزمایش کوین #۱ طبق [[03 - Projects/Mining/Coin Scouting Framework|چارچوب]]

## نوت‌های مرتبط

- [[03 - Projects/Mining/Hardware Registry & Runbook|Hardware Registry & Runbook]] · [[03 - Projects/Mining/Coin Scouting Framework|Coin Scouting Framework]]
- [[03 - Projects/Mining/Mining|لاگ پیام‌های تلگرام — Mining]] · [[03 - Projects/Mining/Ai bots/ARCHITECTURE|Ai bots ARCHITECTURE]]
- [[03 - Projects/Mining/04 - Research/SCOUT-B|SCOUT-B (Track B)]] · [[03 - Projects/Mining/04 - Research/2026-07-14 1512 solar-swarm-mining-research|تحقیق خام Solar Swarm (۲۰۲۶-۰۷-۱۴)]]
- 🏗️ **[[00 - MASTER-ARCHITECTURE|معماری Coin Hunter Bot — MASTER]]** · [[_STATUS-and-HANDOFF|وضعیت و Handoff معماری]] (پوشهٔ `01 - Docs/Coin-Hunter-Bot Architecture/`)
