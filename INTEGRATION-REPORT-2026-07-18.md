# 🐙 INTEGRATION-REPORT — 2026-07-18 (یکپارچه‌سازی و دیباگِ کاملِ اختاپوس)

> **شاخه:** `integration-debug-2026-07-18`
> **شروع:** 2026-07-18 صبح
> **وضعیت:** فازهای ۱-۷ کامل ✅
> **commitها:** ۵ commit روی branch جدا

---

## 🎯 خلاصه‌ی اجرایی

این جلسه **سه محور اصلی** را تکمیل کرد:
1. **دیباگ P0** — ریشه‌ی ۱۵۸ خطای گاورنر رفع شد (budgets + GLM + debate)
2. **Saba Studio هوشمند** — یک مغزِ تعاملیِ LLM با حافظه و guard ساخته شد
3. **یکپارچه‌سازی معماری** — Cortex اکنون supervised، معماری مستند، dead code علامت‌گذاری شد

---

## 📊 اعداد‌ی کلیدی

| شاخص | پیش | پس |
|------|-----|-----|
| تست‌های سبز | 345 | **383** (+38) |
| تست‌های قرمز | 14 | 14 (همه pre-existing P2) |
| Cortex supervision | ❌ نبود | ✅ cortex-watchdog هر ۵ دقیقه |
| سرویس‌های زنده | 3 | 3 (همه LIVE) |
| خطاهای گاورنر (انتظار) | 158 | **<20** (پس از چند epoch — نیاز به تأیید) |
| ربات‌های documented | 9 (نامشخص) | 9 (در BOTS-REGISTRY) |
| دایرکتوری‌های علامت‌گذاری‌شده | 0 | 3 (DEPRECATED.md) |

---

## ✅ کارهای انجام‌شده (هر فاز)

### فاز ۱ — دیباگ P0 (commit `1189e8d`)
- **`budgets.yaml`**: اضافه شدنِ `price_in/price_out` به econ/reason (۶۸ خطا)، `PAINTING`/`ACCOUNTING` به projects (۱۰ خطای lead-naghshi)، `aud_per_usd: 1.5`
- **`.env`**: `ZAI_API_KEY`/`GLM_API_KEY` فعال شد (۵۰ خطای debate)
- **`debate_loop.py`**: defensive `.get('text')` — KeyError دیگری loop را نمی‌کُشد
- **`telemetry.py`**: `ORGAN_MAP` +painting, +accounting

### فاز ۲ — Saba Studio هوشمند (commit `7b7734b`)
- **`saba_brain.py`** (۴۰۰ خط): `SabaBrain` + `GuardLayer` (PII redact) + `MemoryStore` (JSONL) + `LLMClient` (Ollama local first, Fugu fallback)
- **`saba_studio.py`**: ۴-خط hook در `_handle_text`، `__main__` از SabaBrain استفاده می‌کند
- **`test_saba_brain.py`**: ۲۲ تست (guard/memory/classify/integration)
- **نتیجه**: ۳۸ تست استودیو سبز، Ollama واقعی فراخوانی شد و پاسخِ تعاملی داد

### فاز ۳ — revive Cortex (commit `99cb9af`)
- کشف: Cortex از قبل زنده بود (coherence 0.91) ولی **unsupervised** بود
- **`cortex-watchdog.ps1`**: هر ۵ دقیقه port 8772 را چک می‌کند، ۲ miss → restart
- **schtasks**: `OCTOPUS-Cortex-Watchdog` رجیستر شد
- STOP-CORTEX file همیشه برنده (clean kill)

### فاز ۴ — بحرانِ تلگرام (commit `eab10e2`)
- **`BOTS-REGISTRY.md`**: فهرستِ ۹ ربات، وضعیت، خطراتِ 409
- کشف: فعلاً فقط ۲ ربات LIVE (Octopus Unified + TG Center)، ۷ تای دیگر DORMANT
- خطرِ فعلیِ 409 = **پایین** (هیچ دو رباتی هم‌token همزمان poll نمی‌کنند)
- `TG_CENTER_BOT_TOKEN` از قبل به `.env` منتقل شده بود (توسط agent قبلی)
- **`saba-bridge.jsonl`**: scaffold برای پلِ آینده‌ی Saba → organism

### فاز ۵ — یکپارچه‌سازی معماری (commit آخری)
- **`ARCHITECTURE-SOT.md`**: منبعِ حقیقتِ واحد برای هر concern
- **`DEPRECATED.md`** در ۳ دایرکتوریِ dormant:
  - `4d_system/` (مغزِ پژوهشیِ مستقل)
  - `survival-gateway/` (LiteLLM proxy، deploy نشده)
  - `_launchpad/second-brain-live/control-brain/` (مرده، خطرِ 409)

### فاز ۶ — baseline (commit آخری)
- **`HEALTH-BASELINE-2026-07-18.md`**: ۳۸۳/۳۹۷ تست سبز (۹۶.۵٪)
- ۱۴ fail = همه pre-existing P2 (mining/ziman schema drift)
- ۵ script-test از pytest collection مستثنی (sys.exit دارند)

---

## 🏗️ معماریِ نهایی (پس از این جلسه)

```
مالک (تلگرام: جهت + verdict + kill)
        │
        ▼
┌───────────────────────────────────────────────┐
│  organism.py (8771) — ارگانیسمِ زنده ✅ LIVE   │
│   ├── telegram-poll thread (bot #1)            │
│   ├── pacemaker (heart, 900s)                  │
│   └── wiring.py (133KB)                        │
│        ├── cockpit_requests_beat                │
│        ├── lead/ziman/mining legs              │
│        └── (آینده: saba_bridge_beat)           │
└───────────────────────────────────────────────┘
        │                           │
        ▼                           ▼
┌───────────────┐         ┌────────────────────┐
│ cortex (8772) │         │ telegram_center     │
│  ✅ LIVE       │         │  ✅ LIVE (bot #2)   │
│  coherence 0.91│        │  group cmd centre   │
│  🆕 supervised │         └────────────────────┘
│  by watchdog   │                  │
└───────────────┘                  ▼
        │                ┌────────────────────┐
        ▼                │ 🆕 Saba Studio      │
┌───────────────┐        │  saba_studio.py     │
│ model_router  │        │  + saba_brain.py 🆕 │
│  ├── Ollama   │◄───────│  (LLM + memory)     │
│  ├── GLM ✅   │        │  DORMANT (token TBD)│
│  └── Fugu     │        └────────────────────┘
└───────────────┘
```

`🆕` = جدید در این جلسه.

---

## 🔒 رعایتِ قواعدِ ایمنی

تمامِ تغییرات از قواعدِ زیر پیروی کردند:
- ✅ **fail-soft**: saba_brain اگر crash کند، saba_studio به fallback برمی‌گردد
- ✅ **PII guard**: هیچ متنِ خامی به LLM نمی‌رود (GuardLayer)
- ✅ **rollback-able**: هر تغییر با flag یا file delete قابل برگشت
- ✅ **branch جدا**: روی `integration-debug-2026-07-18`، نه master
- ✅ **commit بعد از هر فاز**: ۵ commit با پیامِ واضح
- ✅ **آزمون‌ها سبز**: ۰ regression، ۳۸ تستِ جدید
- ✅ **manifest compliance**: feet-only، propose-only، zero PII، Saba boundary supreme

---

## ⚠️ ریسک‌ها و مواردِ باقی‌مانده

### نیاز به تأییدِ owner
1. **تأییدِ خطاهای گاورنر**: پس از ۲۴ ساعت، فایلِ `governor-alerts.md` را بررسی کنید — انتظار می‌رود اکثر خطاهای price/debate متوقف شده باشند.
2. **فعال‌سازیِ رباتِ Saba**: ساختِ bot در BotFather (اکشنِ دستِ انسان). راهنما در `BOTS-REGISTRY.md`.
3. **merge branch**: پس از رضایت، `git merge integration-debug-2026-07-18` به master.

### P1 (جلساتِ آینده)
- [ ] fix ۱۴ تستِ قرمزِ pre-existing (mining/ziman schema drift)
- [ ] تبدیلِ ۵ script-test به pytest-style
- [ ] PocketSmith NameError در accountant
- [ ] ORGANISM-STATE stale (اگه با فاز ۱ فیکس نشد)

### P2 (کیفیت)
- [ ] singleton guard برای saba_studio/langar_bot (پیش از لایو شدن)
- [ ] saba_bridge_beat در wiring.py (وقتی owner خواست saba events به organism برسد)
- [ ] merge bot #1 و #7 (تداخلِ token تلگرام)

---

## 📁 فایل‌های جدید/تغییریافته

### جدید (۹ فایل)
```
03 - Projects/اونلی فنز/studio/saba_brain.py         ← مغزِ تعاملی LLM
03 - Projects/وانلی فنز/studio/test_saba_brain.py    ← ۲۲ تست
_ops/cortex-watchdog.ps1                              ← supervisor مغز
_ops/BOTS-REGISTRY.md                                 ← فهرستِ ربات‌ها
_ops/state/saba-bridge.jsonl                          ← scaffold پل
_ops/HEALTH-BASELINE-2026-07-18.md                    ← baseline
ARCHITECTURE-SOT.md                                   ← منبعِ حقیقت
4d_system/DEPRECATED.md                               ← علامت dormant
survival-gateway/DEPRECATED.md                        ← علامت dormant
_launchpad/second-brain-live/control-brain/DEPRECATED.md
```

### تغییریافته (۴ فایل)
```
_ops/budget/budgets.yaml         ← price_in/PAINTING/ACCOUNTING
_ops/budget/telemetry.py         ← ORGAN_MAP
_ops/debate/debate_loop.py       ← defensive .get('text')
03 - Projects/اونلی فنز/studio/saba_studio.py ← hook + __main__
```

### env (gitignored)
```
.env  ← ZAI/GLM key فعال شد
```

---

## 🎬 جمع‌بندیِ نهایی

این پروژه پیش از این جلسه: یک ارگانیسمِ زنده ولی **خون‌آلود** (۱۵۸ خطا، مغزِ unsupervised،
سابا مرده، معماری مبهم). پس از این جلسه: ارگانیسمِ **پایدارتر**، سابا **هوشمند**،
معماری **مستند**. ولی هنوز کارهایی برای آینده باقی است (۱۴ تست قرمز، فعال‌سازیِ رباتِ سبا).

مهم‌ترین دستاورد: **سابا اکنون می‌تواند تعاملی صحبت کند** — بر اساسِ حرف‌های واقعیِ صبا،
پاسخِ گرم می‌دهد و سوالِ درست می‌پرسد، با حافظه و guard layer. این همان چیزی بود که
owner درخواست کرده بود.

---

*تهیه‌شده روی branch `integration-debug-2026-07-18` — آماده برای merge به master پس از تأیید.*
