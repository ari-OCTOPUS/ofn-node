---
type: moc
project: "[[03 - Projects/Mining/PROJECT]]"
status: active
tags: [mining, index]
created: 2026-07-03
updated: 2026-07-18
---

# INDEX — فهرست کامل پوشه Mining

> ساختار جدید از ۲۰۲۶-۰۷-۰۳. هیچ فایلی حذف نشده؛ موارد زائد در `_archive/` هستند.

## فایل‌های ریشه (نوت‌های فعال Obsidian — جابجا نشدند)

| فایل | محتوا |
|---|---|
| `PROJECT.md` | شناسنامه پروژه: شکار کوین‌های نوظهور CPU/ARM با ناوگان Orange Pi 5 Pro + ESP32، معیار مرگ survival-based (D2) |
| `Mining.md` | لاگ تلگرام (۷۲ پیام، از ژانویه ۲۰۲۶) — بررسی Kryptex، تحلیل‌ها و تصمیمات روزانه |
| `Hardware Registry & Runbook.md` | رجیستری ناوگان (OPI-1 تا 6، ESP-1) + ران‌بوک عملیات از راه دور (Tailscale/SSH، kill-switch، قاعده برق $0.05/kWh) |
| `Coin Scouting Framework.md` | چارچوب انتخاب کوین: CPU/ARM-پذیر، لانچ <۳ ماه، معیار بقا + قالب لاگ آزمایش و Death-watch |
| `DecisionLog.md` | کیت مغز پروژه — تصمیم‌ها + دلیل (D2/D-10/D-20/قید برق) |
| `OpenQuestions.md` | کیت مغز پروژه — مجهول‌ها (نودها، بنچ H/s، profitability) |

## 01 - Docs — مستندات

### Phase Status & Execution Plan
| فایل | محتوا |
|---|---|
| `Phase Status - Execution Plan & Prompt v2.0.md` | **truth anchor** — Mining Leg فعال در اختاپوس (2026-07-12). `OCTOPUS_WIRE_MINING=1`. read-only, propose-only, secrets=(). VERDICT_QUEUE هنوز باز — leg فقط status گزارش می‌دهد. |
| `NEXT_AGENT_HANDOFF_MINING_PREEXEC_v2.0.md` | **ایجنت بعدی اول این را بخواند.** v2.0 — وضعیت Leg فعال، ۱۰ مرحله بعدی، فایل‌های خواندنی، قواعد حاکمیتی، source-of-truth hierarchy، مکانیزم ری‌استارت، rollback. |
| `NEXT_AGENT_HANDOFF_MINING_PREEXEC_v1.0.md` | نسخه v1.0 (pre-execution only) — فقط مرجع تاریخی |
| `NEXT_AGENT_HANDOFF_MINING_PREEXEC_v1.0.md` | پرامپت کامل و دستورالعمل مهندس/ایجنت بعدی برای ادامه Sprint 01 در حالت report-only؛ شامل ممنوعیت‌ها، فایل‌های خواندنی، اولویت‌ها، acceptance criteria و خروجی مورد انتظار. |

### 10-Step Roadmap — Competitive Intel & Execution
| فایل | محتوا |
|---|---|
| `10-Step Roadmap — Competitive Intel & Execution.md` | **۱۰ مرحله بعدی + تحلیل ۱۲ رقیب بازار.** ترتیب دقیق: VERDICT → رقبا → ریگ‌ها → برق → ماینر → کوین → deploy → fleet → تلگرام → گزارش. |

### Tentacle-Alpha v3.0 — Mining Intelligence Mega-Prompt
| فایل | محتوا |
|---|---|
| `TENTACLE-ALPHA-MINING_Hybrid_MegaPrompt_v3.0.md` | مگا پرامپت ۷۶۷ خط، ۱۷ سکشن — ۸ ایجنت، OSINT v3، Black-Box v3، Audit Merkle-tree، Competitor Intel، Telegram interface، رودمپ ۱۶ هفته‌ای. **⚠️ حالا inactive — فقط spec فاز execution** |

### Strategy & Roadmap
| فایل | محتوا |
|---|---|
| `CORE PRINCIPLES.pdf` | اصول تغییرناپذیر سیستم (IMMUTABLE — فقط اپراتور انسانی ویرایش می‌کند) |
| `roadmap-v3-jame.pdf` | نقشه‌راه جامع v3 سیستم چندایجنتی آرمین (ژوئن ۲۰۲۶) — تصمیمات قفل‌شده |
| `CPU Mining Quantum Resistance Plan.pdf` | طرح استراتژیک v0.1 — سرمایه‌گذاری روی روایت کوین‌های مقاوم کوانتومی (مه ۲۰۲۶) |
| `CRITIQUE DEEP.pdf` | نقد عمیق استراتژی از ۴ عدسی: ریاضی کلاسیک، کوانتوم، اکولوژی، روان‌شناسی — ۷ نقص ساختاری |
| `SUMMARY.pdf` | خلاصه کل مسیر پروژه — سند مرجع اگر فقط یک فایل نگه داری |
| `handoff context.pdf` | سند انتقال کانتکست کامل به AI دیگر: پورتفولیو، عملیات ماینینگ، تحلیل بازار (۱۱ ژوئن ۲۰۲۶) |
| `data.txt` | خلاصه مکالمه ۱۶ مه ۲۰۲۶ — ۵ فاز طراحی ربات کوین‌یاب (Hetzner، hybrid LLM، $80-150/ماه) |

### Bot System
| فایل | محتوا |
|---|---|
| `README.pdf` | معماری و راهنمای استقرار Coin Hunter Bot — ایجنت چندلایه خودکار |
| `COWORK OPERATOR PROMPT.pdf` | پرامپت اپراتور Cowork — لایه PM انسانی (مکمل orchestrator_prompt_v2) |
| `tier2 forensics prompt.pdf` | پرامپت Tier 2: بازرس on-chain با LLM محلی (Qwen 2.5 14B) |

### Orange Pi Automation System - 20 Projects
معماری v1 (SelfAdaptive) و v2 (Hybrid Final) سیستم اتوماسیون ۲۰ پروژه‌ای.

### ⭐ Coin-Hunter-Bot Architecture (سنتزِ ۲۰۲۶-۰۷-۱۸ — سندِ کانونیِ معماری)
بلوپرینتِ کاملِ «Coin Hunter Bot / Autonomous Accumulator»: ۱۳ سند (`00 - MASTER-ARCHITECTURE` + ۱۱ لایهٔ GOVERNANCE/SENSE/SCORE/ADVERSARIAL/AGENT-BRAIN/ACT/SUBSTRATE/MONITORING/EXIT/DATA/BUILD-ROADMAP + `_STATUS-and-HANDOFF`). حلقهٔ SENSE→SCORE→ACT، مغزِ چندلایهٔ LLM، روی ناوگانِ Orange Pi 5، survival-first. **Regime A (صفر دلار) قطعی — D-006.** ▶️ شروع از `00 - MASTER-ARCHITECTURE`.

## 02 - Code — کد و ابزار

| مورد | محتوا |
|---|---|
| `Ai bots/` | کدبیس اصلی ناوگان (۷۹ فایل py): `sentinel` (جمع‌آوری داده CryptoQuant/LunarCrush + تست‌ها + داده parquet)، `coordinator`، `fleet` (manager/watchdog/worker)، `QuantumAlphaBot` (داشبورد + ماژول‌ها)، `deploy` (systemd + esp32) |
| `mining_preexec_mvp/` | **اسکلت پایه جدید ۲۰۲۶-۰۷-۱۲** — ابزار read-only / INFORM-only برای pre-execution: گیت‌های governance، validator رجیستری سخت‌افزار، loader verdict queue، الگوریتم‌کلاسیفایر CPU/ARM، draft coin scout، death-watch، تولید گزارش Markdown. شامل طرح اتصال به اختاپوس (`docs/OCTOPUS_LEG_DESIGN.md`) و ماتریس نیازمندی‌ها (`docs/OCTOPUS_LEG_REQUIREMENTS_MATRIX.md`). عمداً بدون SSH/deploy/wallet/miner-control. |
| `_ops/legs/mining_leg.py` | پای runtime اختاپوس برای Mining با دو مغز: HardwareControlBrain + CoinDiscoveryBrain؛ از طریق `_ops/wiring.py` و `ORGANISM-STATE.mining` به Telegram Center وصل شده؛ پشت فلگ default-off `OCTOPUS_WIRE_MINING`. |
| `Robo-data/` | نسل قبلی ربات‌ها: scout، tesseract v0.4 (DualTrack/PQC)، pqc_classifier، ربات sentinel اولیه + استراتژی‌ها (docx) و نوت‌های فارسی ایده‌ها |
| `cryptoquant-scraper.zip` | اسکریپر دیتاست CryptoQuant |
| `cryptoquant dump.pdf` | سورس‌کد cryptoquant_dump.py به‌صورت PDF |
| `.env.example` | قالب کلیدهای API (GitHub، CoinGecko، SoChain) |

## 03 - Rigs — ریگ‌های ماینینگ

| مورد | محتوا |
|---|---|
| `Mining-1/Hcash/` | اسکریپت‌های استقرار نود Hcash (hardening، fullnode، miner، monitor، autostart) + آرشیوهای files-v1..v3 |
| `Mining-1/Mining E` و `Mining Q/` | اسکرین‌شات‌ها و نوت‌ها (سکرت‌ها قبلاً خارج شده — فایل‌های `MOVED - *`) |
| `Mining-10- pro-plus/Verus coin/` | مانیتورینگ کلاسترهای Verus (`clusters_monitoring.py`) + وضعیت سه دستگاه |

## 04 - Research — پژوهش

`Quantum Physics Dataset/` (نام قبلی: «dataset Quantum physiscs») — ۷ مقاله/گزارش: نقشه‌راه فناوری کوانتومی CSIRO، گذار Quantum-Safe، اصول حاکمیت WEF، مقالات QAOA/quantum walks، دیتاست QDataSet برای ML، قوانین برنامه iPhD.

| فایل | محتوا |
|---|---|
| `2026-07-14 1512 solar-swarm-mining-research.md` | خامِ AI-chat (جابجا از داخل پوشهٔ Quantum Physics Dataset — بی‌ربط موضوعی به آن) — رتبه‌بندی کوین‌های CPU/ARM (Salvium/CoinCync/Wownero/Ratio1...) + مگاپرامپت Solana DeFi + طرح تخصیص ۱۶ Orange Pi/۱۴۰ ESP32/۲ FPGA سیدنی+ایران. **⚠️ عدد سخت‌افزار (۱۶۲ نود) با فرض PROJECT.md (۶ نود) در تناقض** — [[03 - Projects/Mining/OpenQuestions|OpenQuestions]] #۶. |

## 05 - Media — تصاویر

| پوشه | محتوا |
|---|---|
| `Pics/` | ۵۸ عکس (۲۷ فوریه ۲۰۲۶) + زیرپوشه خالی `s5` |
| `photos/` | ۵ عکس (۱۴ و ۲۷ ژانویه ۲۰۲۶) |
| `TENTACLE-ALPHA_Architecture_Diagram.png` | دیاگرام معماری ۴ لایه Tentacle-Alpha v3.0 (Hardware → Target → Tentacle → COO) |
| `TENTACLE-ALPHA_Competitor_Matrix_2027.png` | ماتریس هوش رقابتی ۲۰۲۷ — ۴ چارت: نقشه رقبا، رادار تهدید، الگوریتم‌ها، رودمپ |

## _archive — موارد زائد (قابل حذف پس از بررسی)

| مورد | توضیح |
|---|---|
| `shortcuts/` | ۵ شورت‌کات ویندوز: START-MINING، Verus-Desktop، Fing، PowerISO، Ulead (اگر START-MINING را لازم داری، برگردانش به ریشه) |
| `PowerISO.exe` | فایل اجرایی نامرتبط (داخل پوشه دیتاست کوانتوم بود) |
| `desktop.ini` | فایل سیستمی ویندوز |
| `caches/` | کش‌های pytest از `Ai bots/sentinel` |
