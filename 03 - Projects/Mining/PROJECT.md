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
updated: 2026-07-29
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

- **2026-07-29 (اسکنِ گروهِ تلگرام — تأییدِ مستقل):** حقیقتِ پایهٔ [[../../OCTOPUS-DOCTOR/50-اسکن‌ها/TG-GROUP-SCAN-PACKAGE-2026-07-29|TG-SCAN-PACKAGE]] وضعِ ۰۷-۲۸ را مستقل تأیید کرد: هر سه فلگِ اتصالِ `mining_os` (`_OS`/`_UI`/`_VERDICT_SYNC`) هنوز در `OCTOPUS-flags.cmd` غایب‌اند — **عمداً staged در `_ops/ARMING-ORDER-2026-07-29.md`، منتظرِ OWNER_AUTH** — و دایجستِ تاپیکِ ⛏ همچنان از skeletonِ `mining_leg` با `live=False` می‌آید (۲۳.۵ روز کهنه). ⚠️ دامِ گزارش‌خوانی: `OCTOPUS_WIRE_MINING=1` (پای skeleton) ست است و با فلگ‌های mining_os اشتباه گرفته می‌شود. منوی `/mining` و رأی‌های `mo:` ساخته‌اند ولی با فلگِ خاموش به مالک نمی‌رسند.
- **2026-07-28 (جوابِ مالک + بازسازیِ سیم‌کشی):** اسکنِ کاملِ پروژه ([[03 - Projects/Mining/SCAN-REPORT-FULL_v1.0|SCAN-REPORT]]) راستی‌آزمایی شد. بخشِ سازمانی‌اش درست بود، بخشِ «وصل است» **غلط**: بستهٔ `mining_os` (کامیتِ `88aaa29`، ۳۲ تستِ سبز) **صفر صداکننده** داشت — `ACTIVATION.md` هوکی در `organism.py:712` ادعا می‌کرد که آن‌جا بلوکِ **فیشر** است، و هیچ‌کدام از سه فلگِ `_OS`/`_UI`/`_VERDICT_SYNC` در درخت وجود نداشت. یعنی «روشن‌کردنِ فلگ» در نقشهٔ راه اجراشدنی نبود. **سیم‌کشی واقعاً ساخته شد** (`wiring.mining_os_beat` + صداکننده در `organism.py` + ۳ هوکِ `center.py`)، همه **flag-off** و بیرونِ `PAPER_FULL_FLAGS`؛ گاردِ call-site `_ops/tests/test_mining_os_wiring.py` (۹/۹، هر ۵ جهش قرمز شد) تا دوباره بی‌صدا نیفتد — [[03 - Projects/Mining/DecisionLog|D-012]]. **چهار جوابِ مالک ثبت شد** (D-008/D-009/D-011): ۱۶۲ نود، همه خاموش، خورشیدیِ فعال، یک سایت (سیدنی)، فازِ «شروعِ ماینِ واقعی». MIN-V1/V2/V3/V5 بسته شدند.
- **2026-07-18 (اینتگریشنِ معماری):** معماریِ کاملِ «Coin Hunter Bot / Autonomous Accumulator» (۱۳ سند در `01 - Docs/Coin-Hunter-Bot Architecture/`) به مغزِ پروژه وصل شد. **⏭️ نقطهٔ ورود: `[[00 - MASTER-ARCHITECTURE]]`، بعد `[[_STATUS-and-HANDOFF]]`.** تصمیمِ Regime هزینه **قطعی شد: Regime A (صفر دلار)** — رأی مالک، `[[03 - Projects/Mining/DecisionLog|D-006]]`. عددِ ناوگانِ معماری (۱۶–۵۰ Pi + ۵۰–۲۰۰ ESP32) با تحقیقِ solar-swarm (۱۶ Pi + ۱۴۰ ESP32) هم‌راستاست؛ «۶ نود» کهنه است (D-007). **Round-1 هماهنگ‌سازی کامل و کامیت شد (`c25e135`):** قفلِ D-006 در هر ۱۲ سند منتشر شد، مالک‌های canonical یکدست (schema=۱۰، death-watch=۰۸، LIMBO=۰۴، شمارشِ ناوگان=۰۷)، قطع‌شدگیِ `_STATUS` ترمیم شد؛ راستی‌آزماییِ ۴-لنزهٔ خصمانه + هر دو validator سبز. **Round-2 (تصمیم‌های طراحی) منتظرِ مالک** — ۱۲ مارکرِ `[OPEN — Round 2]` داخلِ اسناد.
- **2026-07-14:** تحقیق خامِ درشتی (پیست AI-chat، ۱۳۳۲ خط) که در پوشهٔ بی‌ربطِ `04 - Research/Quantum Physics Dataset/` افتاده بود پیدا و جابجا شد → [[03 - Projects/Mining/04 - Research/2026-07-14 1512 solar-swarm-mining-research|فایل جدید]] (INDEX.md هم به‌روزشد). محتوا: کاندیدهای جدید کوین (Salvium، CoinCync، Wownero، Ratio1، Nodle، Grass) برای [[03 - Projects/Mining/Coin Scouting Framework|چارچوب شکار کوین]] + مگاپرامپت Solana DeFi off-ramp + طرح تخصیص سخت‌افزار سیدنی/ایران. **مهم‌ترین یافته:** این سند ۱۶۲ نود (۱۶ Orange Pi 5 Pro + ۱۴۰ ESP32 + ۲ FPGA) را «already bought» فرض می‌کند — در تناقض با فرض «۶ نود»ی که تا الان مبنای این پروژه بود؛ صرفاً تحقیق/پیش‌نویس است، هیچ اجرایی نشده.
- **2026-07-06 (جلسه ۱۷):** کد پروژه به `_code/` منتقل شد (B1 پلن NONMD-TRIAGE؛ propose→executed با verdict آری). لاگ کامل: `00 - Inbox/nonmd-move-log-2026-07-06.csv`.

- تمرکز فعلی: **راه‌اندازیِ فیزیکیِ اولین OPI** — تا یک نودِ زنده نباشد، هر عددِ هش‌ریت/سود حدس است
- تغییرات اخیر: 2026-07-03 — Phase 0 (انتقال secretها) + ارتقا به manifest فاز ۱ + دو نوت چارچوب · 2026-07-04 — [[03 - Projects/Mining/04 - Research/SCOUT-B|SCOUT-B]] (تحقیق Track B) از Inbox به `04 - Research` منتقل شد · 2026-07-04 — کیت مغز پروژه (INDEX·DecisionLog·OpenQuestions طبق LIVING-BRAIN-BLUEPRINT) ساخته شد · 2026-07-14 — تحقیق خامِ mining/Solana جابجا و کاتالوگ شد (بالا)
- ۳ قدم بعدی: (۱) **مالک: OPI-01 را تنها روشن کند** + شبکه/Tailscale → اولین ردیفِ واقعیِ رجیستری (۲) رأیِ MIN-V6 (swap خودکار یا دستی؟) (۳) چرخشِ wallet/کلیدها (مالک)
- تصمیم‌های باز: **MIN-V6** — بات حق دارد خودکار swap کند یا فقط پیشنهاد بدهد؟ · MIN-V4 — رجیستریِ تک‌نود کِی پر می‌شود؟ · کوینِ #۱ کدام است (VerusCoin بهترین راندمانِ گزارش‌شده)؟

## Progress

- چه کار می‌کند: زیر-OSِ `mining_os` **واقعاً به اختاپوس وصل شد** (flag-off، ۳۲+۹ تستِ سبز) · لگِ `mining_leg` در `business_legs` با `live=False` صادق · تاپیکِ ⛏ تلگرام = ۲۴ · کدِ بات‌ها موجود (خاموش) · چارچوب‌ها تعریف شد
- چه مانده: راه‌اندازیِ فیزیکیِ نودها · پرکردنِ `mining_os/state/MINING-STATE.json` با ناوگانِ واقعی (تا آن‌موقع `live=False` درست است) · rotation · رأیِ MIN-V6 · اولین آزمایشِ ثبت‌شده
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
