---
type: runbook
status: ready
tags: [pf_os, project-f, onlyfans, saba, runbook, ops]
created: 2026-07-19
updated: 2026-07-19
---

# 🐙🦶 Project-F OS (pf_os) — Runbook

> یک OS مستقلِ ماژولار برای پا/دامنه‌ی Project-F. مغز = از cortex مرکزی.
> تعامل = رابطِ مستقیم با صبا + REST API. پل = file-based pub/sub به ارگانیسم.
> **همه پشتِ flag (default OFF). بدونِ flag = بایت‌به‌بایتِ امروز.**

---

## ۰) طراحی در یک نگاه

```
   صبا (Telegram)            اپراتور (Telegram)
        │                          │
        ▼                          ▼
   SabaStudio               LangarBot (موجود)
   (با مغزِ pf_os)               │
        │                          │
        ▼                          ▼
   ┌─────────────────────────────────────────┐
   │              pf_os/                      │
   │  brain.py     — BrainCore (LLM-backed)   │
   │  saba_link.py — پلِ من↔صبا                │
   │  learning_bus — ThompsonBandit reuse     │
   │  loop.py      — tick مستقل               │
   │  api.py       — REST :8780               │──► cortex مرکزی :8772
   │  bridge.py    — writer به organism       │    (POST /ask, organ PROJECT_F)
   │  bridge_beat  — consumer (organism side) │
   │  singleton    — PID lockfile + Exclusive │
   └─────────────────────────────────────────┘
        │
        ▼
   _ops/state/saba-bridge.jsonl  →  organism می‌خواند
```

---

## ۱) Flagها (همه default-OFF)

| Flag | نقش | روشن کن با |
|------|-----|-----------|
| `OCTOPUS_WIRE_PROJECTF_CORTEX` | فراخوانیِ واقعیِ cortex (در غیر اینصورت heuristic-only) | `set OCTOPUS_WIRE_PROJECTF_CORTEX=1` |
| `OCTOPUS_WIRE_PROJECTF_LOOP` | حلقه‌ی tick مستقل (هر ۵ دقیقه) | `set OCTOPUS_WIRE_PROJECTF_LOOP=1` |
| `OCTOPUS_WIRE_PROJECTF_API` | REST API روی :8780 | `set OCTOPUS_WIRE_PROJECTF_API=1` |
| `OCTOPUS_WIRE_SABA_BRIDGE` | consumer-side در organism (bridge_beat) | `set OCTOPUS_WIRE_SABA_BRIDGE=1` |

**توصیه‌ی راه‌اندازیِ گام‌به‌گام (هرکدام مستقل):**
1. اول `OCTOPUS_WIRE_PROJECTF_CORTEX=1` اگر cortex online است.
2. بعد `OCTOPUS_WIRE_PROJECTF_API=1` برای داشتنِ dashboard.
3. بعد `OCTOPUS_WIRE_PROJECTF_LOOP=1` برای tick دوره‌ای.
4. در organism (وقتی لینِ قلب تمام شد): `OCTOPUS_WIRE_SABA_BRIDGE=1`.

---

## ۲) Token برای رابطِ صبا (LIVE)

`SabaStudio` از قبل می‌داند چطور با یا بدونِ token کار کند:
- **بدونِ token** → shadow-mode (stdin/stdout، برای تست/دیباگ)
- **با token** → live به تلگرام long-poll می‌زند

برای LIVE:
```cmd
:: ۱) ربات را در @BotFather بساز (operator یا creator، دستِ انسان)
:: ۲) chat_id creator را از @userinfobot بگیر
set TELEGRAM_SABA_BOT_TOKEN=<token_from_botfather>
set TELEGRAM_SABA_CHAT_ID=<saba_chat_id>
:: ۳) اجرا
python -m pf_os.run_saba
```

**Singleton-guard**: اگر قبلاً در حالِ اجراست، دومین instance با پیام «🔴» خارج می‌شود (نه 409 تلگرام).

---

## ۳) حالت‌های اجرا

### ۳.۱ Shadow (تست، $0، بدون token)
```bash
python -m pf_os.run_saba
```
با stdin تعامل کن (مثلاً «قیمت؟»، «خسته شدم»). مغز پاسخ می‌دهد.

### ۳.۲ Live (صبا واقعی)
```bash
set TELEGRAM_SABA_BOT_TOKEN=... && set TELEGRAM_SABA_CHAT_ID=...
python -m pf_os.run_saba
```

### ۳.۳ REST API به‌تنهایی
```bash
set OCTOPUS_WIRE_PROJECTF_API=1
python -m pf_os.api
# حالا: http://127.0.0.1:8780/api/health
```

### ۳.۴ Tick loop
```bash
set OCTOPUS_WIRE_PROJECTF_LOOP=1
python -m pf_os.loop
```

### ۳.۵ تست bridge_beat (موقت، تا integration در organism)
```bash
set OCTOPUS_WIRE_SABA_BRIDGE=1
python -m pf_os.bridge_beat
```

---

## ۴) REST API endpoints

| Method | Path | توضیح |
|--------|------|-------|
| GET | `/` | HTML landing (RTL) |
| GET | `/api/health` | beat، uptime، brain، saba، bridge |
| GET | `/api/brain/thoughts` | آخرین thoughts |
| POST | `/api/brain/ask` | `{task, prompt}` → brain response |
| GET | `/api/store/{fan,vault,kpi}` | snapshot از DataSpine |
| POST | `/api/draft/submit` | `{title}` → queued (propose-only) |
| GET | `/api/octopus/bridge` | وضعیتِ پل |
| GET | `/api/learning` | وضعیتِ learning bus |
| GET | `/api/saba` | وضعیتِ پلِ صبا |
| GET | `/api/capabilities` | registry |

**Auth** (اختیاری): `set PF_OS_API_TOKEN=<secret>` سپس `Authorization: Basic ...:<token>`.

---

## ۵) تست‌ها

```bash
cd "03 - Projects/اونلی فنز"
python -m pytest -q           # همه — باید 328+ سبز
python -m pytest pf_os/ -q    # فقط pf_os
```

---

## ۶) نقاطِ تماس با ارگانیسم

| جهت | مکانیزم | فایل |
|------|---------|------|
| pf_os → organism | `saba-bridge.jsonl` (append-only) | `_ops/state/saba-bridge.jsonl` |
| organism → pf_os | `bridge_beat.py` (cursor+lock) | بعد از لینِ قلب در wiring.py |
| مغز pf_os → cortex | `POST :8772/ask` (organ PROJECT_F) | `cortex_client.py` |
| پول | `organ_gate.reserve("PROJECT_F")` | در cortex call (آینده) |

**هرگز دست نزن** (طبقِ LANE-RULES):
- `_ops/heart/*` · `_ops/cortex/local_llm.py` · `_ops/cortex/model_router.py`
- `_ops/telegram_center/approval_store.py`
- بلوکِ `allocation` در `_ops/budget/budgets.yaml` (PROJECT_F satellite بماند)

---

## ۷) عیب‌یابی

| نشانه | علت احتمالی | رفع |
|-------|-------------|-----|
| API port 8780 refuse | flag off یا port گرفته | `set OCTOPUS_WIRE_PROJECTF_API=1`، check port |
| brain همیشه fallback | cortex flag off یا cortex پایین | `set OCTOPUS_WIRE_PROJECTF_CORTEX=1`، cortex را start کن |
| Saba «🔴 در حال اجراست» | singleton قفل گرفته | lock file در `pf_os_state/` را پاک کن (یا ۱۲۰s صبر) |
| bridge events consumed نمی‌شوند | bridge_beat flag off یا cursor ffwd | `set OCTOPUS_WIRE_SABA_BRIDGE=1` |
| respond_to_saba = None | PII در متن (scrub reject) | عادی — intent دست‌نیافتنی، fallback |

---

## ۸) نامتغیرها (هرگز نقض)

1. **PII هرگز**: هیچ نام/شهر/محتوا به cortex یا bridge نمی‌رود. scrub در ۳ لایه.
2. **propose-only**: هیچ publish/send/pay خودکار نیست. همه‌چیز تأییدِ انسان.
3. **flag-off = بایت‌به‌بایت**: بدونِ flag، pf_os هیچ ساید-افکتی ندارد.
4. **stdlib-only**: صفر dependency بیرونی.
5. **$0 آفلاین**: در shadow-mode بدونِ LLM/token کار می‌کند.
