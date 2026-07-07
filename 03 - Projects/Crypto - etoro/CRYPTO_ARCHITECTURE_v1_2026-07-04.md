---
type: architecture
project: "[[03 - Projects/Crypto - etoro/PROJECT]]"
status: active
tags: [crypto, architecture, tenant, aligned-blueprint-v2]
version: 1.0
created: 2026-07-04
updated: 2026-07-04
aligns_to: "[[04 - Architect System/architect/01-Project/SYSTEM-BLUEPRINT-v2]]"
---

# 🏗️ CRYPTO ARCHITECTURE v1 — «Crypto-etoro» Tenant

> اولین نسخهٔ معماریِ واقعی، هم‌تراز با `SYSTEM-BLUEPRINT-v2` (لایهٔ مادر) و `ARCHITECT_CHARTER`. قانونِ حلِ تناقض: **کد واقعی > سند جدیدتر > قدیمی‌تر**.

---

## 1. Quick Summary — چیست و چه می‌گیری؟

کریپتو یک **standalone system نیست** — یک **Tenant** درونِ اکوسیستمِ Architect (langar) است. Control plane (Telegram، Brain/Router، Safety Kernel، Memory) را از مادر **می‌گیرد، بازنمی‌سازد**؛ و خودش فقط لایهٔ دامنه (data→signal→scout→portfolio→fleet) + یک **read-only adapter** + ایجنتِ **propose-only** `crypto-watcher` را می‌آورد.

**حکم:** معماری = «tenant لاغر روی مادرِ موجود»، نه یک برجِ جدا. این با P7 (بودجهٔ ۵-جزئیِ مادر) و اصلِ reuse هم‌خوان است و کمترین سطحِ حمله را دارد.

---

## 2. کجای مسیرِ بحرانی هستیم؟ (§4.2)

| گام | وضعیت | چرا بلاک |
|---|---|---|
| **1. Rotation** | 🔴 **همین‌جاییم** | §Security Gate بسته — ۴ CRITICAL باز (Monero seed · Bybit · OKX · Anthropic keys) → autonomyِ همه = read-only |
| 2. Refresh data | ⏳ منتظر | کلیدها تا rotate نشوند scrapers خاموش |
| 3. Fill Registry | ⏳ | خالی = صفر autonomy |
| 4. Wire EdgeClassifier | ⏳ | `edge_present=[]` → همه gate را رد می‌کنند |
| 5. Deploy fleet | ⏳ | بعد از rotation + TOP-5 audit + Phase-4 prompt + verdict |
| 6. Ledger + kill-switch | ⏳ | Anchor Ledger هنوز کد ندارد (charter §۴) |
| 7. paper → live | ⏳ | فقط بعد از اعتبارسنجی + verdict |

**نتیجه:** این سند یک معماریِ **کاغذی/paper** است. تا گیت باز نشود هیچ‌چیز live نمی‌رود — و این feature است، نه محدودیت.

---

## 3. Analysis

**Problem:** پرتفوی overweight high-beta، دیتای کهنه، fleet ساخته ولی deploy/ledger ندارد، و باید همه‌چیز زیرِ حاکمیتِ سختِ مادر بماند.

**Constraints (از blueprint، غیرقابل مذاکره):** P1 human-gate روی هر action برگشت‌ناپذیر · P2 fail-closed (kill-switch قبل از هر action و هر round) · P3 constraintها خارج از prompt (جدولِ `action_policy`) · P7 بودجهٔ ۵-جزئی · P10 هیچ private key روی ماشینِ agentic · P11 هیچ LLM در مسیرِ فرمان · Non-goal: **اجرای trade خودکار = HARD_STOP**.

**Risks:** (a) نشتِ کلید (تا rotation کامل) · (b) error compounding در pipelineِ چندمرحله‌ای (0.95¹⁰≈۶۰٪ — دفاع: checkpointهای میانی) · (c) Goodhart روی scoreِ کیواژه‌ای · (d) fleet single-point-of-failure روی OPi5+ (دفاع: RPi3B watchdog).

**Assumptions:** `[Assumption]` eToro retail API معاملاتی ندارد → اجرا دستی · `[Assumption]` OPi5 Pro = 16GB (نیازِ confirm) · `[Assumption]` مادر روی VPS + لپ‌تاپ اجرا می‌شود (D-12: لپ‌تاپ اول).

---

## 4. Architecture

### 4.1 — دو Plane

**Control plane = مادر (langar، reuse):** Telegram bot (owner_only + intent-router rule-based + step-up passphrase) · Brain/Router (Haiku 70 / Sonnet 25 / Opus 5) · Safety Kernel (constitution + kill-switch + `action_policy` + Anchor Ledger) · Memory (SQLite→Postgres+pgvector).

**Crypto plane = این tenant:** L1 داده → L2 سیگنال → L3 scout → L4 portfolio/risk → L7 fleet؛ به‌علاوهٔ **adapter** (خواندنی) و **`crypto-watcher`** (propose-only).

### 4.2 — لایه‌ها (L0–L9)

| L | مسئولیت | تکنولوژی | کجا اجرا | failure mode |
|---|---|---|---|---|
| **L0** | Tenant integration + charter/gate/ledger | `projects.yaml` + adapter contract | مادر (VPS) | گیت بسته → read-only (درست) |
| L1 | Data ingestion | scrapers (JS+py proxy)، LunarCrush/CryptoQuant/Coinalyze | OPi5+ / VPS | `429` → backoff؛ کلید نبود → skip |
| L2 | Signal fusion | `Sentinel/signal_fusion.py` (macro+social) | OPi5+ | divergence نویز → flag |
| L3 | Scouting | `QuantumAlphaBot` (GemHunter→Forensics→Veto→LLM→Kelly) + Tier-1 local LLM | OPi5+ + workers | EdgeClassifier unwired → `edge=[]` |
| L4 | Portfolio & risk | barbell · Kelly · 2% cap · Registry | OPi5+ | thesis کهنه → invalidation |
| L5 | Agent | `Coordinator` (confluence) + `crypto-watcher` (adapter agent) | OPi5+ | همه propose-only |
| L6 | Governance & ledger | Registry `exit_rules` · Anchor Ledger · gate | مادر | ledger کد ندارد (Phase 4) |
| L7 | Mining/compute fleet | `Fleet Manager` :7700 + worker_agent + watchdog + MQTT | LAN (۱۶ OPi5 Pro، ESP32، FPGA) | OPi5+ down → RPi3B restart |
| L8 | Memory/knowledge | vault notes + DB cache | vault + OPi5+ | conflict → انسان برنده |
| L9 | Cross-cutting | budget sub-cap · monitoring · testing · DR | همه‌جا | > سقف → auto-halt |

### 4.3 — Tenant Adapter contract (درزِ اتصال به مادر)

ثبت در `projects.yaml`: `name: crypto-etoro · repo: … · autonomy_floor: INFORM · budget_subcap: $0.50/day (Normal) · adapter: crypto_adapter`.
Adapter فقط این interfaceِ **read-only** را expose می‌کند (creds جدا، enforced): `status()` · `logs(n)` · `report(period)` · `audit()`. هر write فقط از مسیرِ deploy pipelineِ گیت‌شده (D-20). **کلید هیچ‌جا (P10).**
`crypto-watcher`: `exit_rules` را پایش می‌کند، evidence می‌سازد، پیشنهاد به Chief Orchestrator می‌دهد → تلگرام → verdictِ آری. **هرگز مستقیم اجرا نمی‌کند.**

### 4.4 — استقرارِ فیزیکی

| نود | IP | نقش |
|---|---|---|
| OPi5+ (brain) | 192.168.1.100 | QuantumAlphaBot + Sentinel + Coordinator + Fleet Manager |
| ۱۶× OPi5 Pro | .101–.116 | worker_agent (yespower ~1500 H/s هرکدام) |
| ESP32 ×140 | .120+ | MicroPython، sensor/heartbeat via MQTT |
| RPi 3B | .110 | watchdog (restart OPi5+ اگر down) |
| FPGA A7-Lite-200T ×2 | USB/UART | lattice/PQC + entropy |
| VPS (Hetzner CX22) | — | مادر langar + adapter endpoint + Telegram |

### 4.5 — جریان

data (L1) → signal (L2) → QuantumAlphaBot scout هر ۶h → `paper_ledger.jsonl` → Coordinator +۳۰min (confluence QA×0.45+Sent×0.55، ۶ gate) → `decisions.jsonl` → **adapter.report()** → Chief Orchestrator → **Telegram** → verdictِ آری → اجرای **دستیِ** eToro. Mining: ENERGY edge → Fleet Manager → workers (INFORM only، D-10).

---

## 5. Tech Stack (pricing · alternative · lock-in)

| جزء | انتخاب | pricing | alternative | lock-in |
|---|---|---|---|---|
| LLM | Claude (Opus $5/$25 · Sonnet $3/$15 · Haiku) | usage | DeepSeek batch $0.14/$0.28 · local Qwen/Llama | متوسط (کاهش با fallback provider) |
| Local triage | Qwen2.5/Llama3.1 via Ollama | رایگان (برق) | Groq | صفر |
| VPS | Hetzner CX22 4GB | ~€4.35/mo | Oracle Free ARM | پایین |
| Message bus | Mosquitto MQTT | رایگان self-host | Redis pub/sub | صفر |
| DB | SQLite → Postgres+pgvector | رایگان | TimescaleDB/DuckDB | پایین |
| Data APIs | LunarCrush · CryptoQuant · Coinalyze | freemium | Glassnode · Santiment | متوسط (abstraction layer) |
| Fleet mgmt | REST :7700 (custom) | رایگان | Prometheus+Grafana | پایین |
| Orchestration | Docker Compose → k3s/Nomad | رایگان | Swarm | پایین |

---

## 6. Governance & Budget alignment

- **§Security Gate** (charter): بسته → autonomyِ همه read-only. باز شدن فقط با verdictِ آری + ثبت در ledger.
- **Kill-switch (D-06):** fleet و adapter به flag `halted` (DB) + فایلِ `STOP` احترام می‌گذارند؛ چک در ابتدای هر cycle؛ fail-closed.
- **Anchor Ledger:** هر verdict/اجرا/تغییرِ گیت append-only؛ نوشتن فقط از API (Phase 4، BACKLOG).
- **Budget (D-25):** زیرسقفِ Mining/تحلیل **$0.50/روز (Normal)** / $2 (Growth با passphrase)؛ ماهانه در سقفِ $60 مادر؛ alert 50/80٪ + auto-halt.
- **Keys (P10/D-11):** exchange + wallet seed **off-box، zero LLM، human co-sign**.
- **No LLM in command path (P11):** intent-router مادر rule-based؛ کریپتو فقط پیشنهاد می‌دهد.

---

## 7. Trade-offs (score 1–10؛ بالاتر=بهتر)

| تصمیم | Cost | Complexity | Scalability | Maintainability | Security | Time | حکم |
|---|---|---|---|---|---|---|---|
| Tenant لاغر روی مادر (vs standalone) | 9 | 8 | 7 | 8 | 9 | 8 | ✅ بالاترین ROI — reuse + کمترین attack surface |
| Local-LLM triage → API فقط برای عمق | 9 | 6 | 7 | 7 | 8 | 6 | ✅ بودجه را در سقف نگه می‌دارد |
| Fleet روی OPi LAN (vs cloud GPU) | 8 | 5 | 6 | 6 | 7 | 5 | ✅ solar/cheap؛ ولی SPOF → watchdog لازم |
| SQLite حالا → Postgres بعداً | 9 | 8 | 5 | 7 | 6 | 9 | ✅ measure-first (P6)؛ مهاجرت phase-gated |
| Anchor Ledger الان (vs Phase 4) | 4 | 4 | — | — | 9 | 3 | ⚠️ امنیت بالا ولی زمان‌بر → همان Phase 4 بماند |

---

## 8. Roadmap (نگاشت به فازهای blueprint)

| فاز | کریپتو | معیارِ «تمام» |
|---|---|---|
| **MVP (فاز ۰، ۱–۲ هفته)** | Rotation ۴ CRITICAL · scrapers خاموش بماند · Registry اسکلت | گیت قابلِ باز شدن؛ صفر secret در repo (gitleaks پاس) |
| **v1 (۳–۶ هفته)** | adapter `crypto_adapter` (read-only) + `action_policy` + budget sub-cap + wire EdgeClassifier | adapter فقط read؛ فرمانِ مخرب بدون passphrase reject |
| **v2 (۲–۳ ماه)** | onboard tenant کامل (INFORM only) + paper-trading زنده + first bounded-auto SELL/TRIM (بعد از گیت) | cross-tenant read → fail؛ یک cycle کامل paper با evidence |

---

## 9. Next steps (فوری)

1. **Rotation:** ۴ کلیدِ CRITICAL را باطل/نوسازی کن (`ROTATION_CHECKLIST`) — تنها کارِ معنادارِ الان.
2. **Registry skeleton:** یک بلوکِ نمونهٔ پوزیشن با `exit_rules` خالی بساز تا قالب آماده باشد (autonomy صفر می‌ماند تا آری تأیید کند).
3. **Confirm:** RAMِ OPi5 Pro (8/16GB) + مکانِ اجرای مادر (VPS/لپ‌تاپ) — تا L7/L0 قطعی شود.

---

## Sources (vault، read-only)

`SYSTEM-BLUEPRINT-v2` (§۲ tenant adapter، P1–P11، budget) · `ARCHITECT_CHARTER` (§Security Gate، §Trading Autonomy، D-06/10/11/13/20/25) · `SYSTEM_MAP` · `AGENT_REGISTRY` (crypto-watcher) · `Ai bots/ARCHITECTURE.md` (fleet، pipeline، IPها) · `ROTATION_CHECKLIST` · `MASTER_ARCHITECTURE_PROMPT_2026-07-04.md`.

## مرتبط

<!-- Tier A · CONNECTIONS-MAP (_memory) · اعمال 2026-07-04 -->
- [[04 - Architect System/architect/ARCHITECT_CHARTER|ARCHITECT_CHARTER]]
- [[05 - Agents/AGENT_REGISTRY|AGENT_REGISTRY]]
- [[06 - Architecture Maps/SYSTEM_MAP|SYSTEM_MAP]]
