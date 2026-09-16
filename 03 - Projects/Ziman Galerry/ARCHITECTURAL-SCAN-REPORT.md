---
type: report
status: done
tags: [ziman, scan, architecture]
created: 2026-07-12
updated: 2026-07-29
---
# گزارش اسکن معماری — Ziman Gallery

> **تاریخ اسکن:** 2026-07-12  
> **مسیر پروژه:** `F:/backup/03 - Projects/Ziman Galerry/`  
> **نسخه گزارش:** 1.0  
> **حجم کد:** ~2,800 خط پایتون + ۱۱۵ خط YAML  
> **تست‌ها:** ۴۰/۴۰ سبز (T11 VERIFIED)

---

## فهرست

1. [خلاصهٔ اجرایی](#1-خلاصهٔ-اجرایی)
2. [نمای کلی معماری](#2-نمای-کلی-معماری)
3. [مغزِ کنترل — control-brain](#3-مغزِ-کنترل--control-brain)
4. [ایجنت محتوا — ziman-agent](#4-ایجنت-محتوا--ziman-agent)
5. [انسان در حلقه (HITL)](#5-انسان-در-حلقه-hitl)
6. [اتصال به اختاپوس](#6-اتصال-به-اختاپوس)
7. [قراردادها و رابط‌ها](#7-قراردادها-و-رابطها)
8. [سوئیچ‌های ایمنی](#8-سوئیچهای-ایمنی)
9. [بستهٔ تست](#9-بستٔ-تست)
10. [کدها و فایل‌ها](#10-کدها-و-فایلها)
11. [شکاف‌ها و ریسک‌ها](#11-شکافها-و-ریسکها)
12. [توصیه‌ها](#12-توصیهها)

---

## 1. خلاصهٔ اجرایی

**زیمان گالری** یک بیزنس محلی آنلاین در سیدنی است (هدایای دست‌ساز گل‌آرایی مصنوعی). سیستم مولتی‌ایجنتی آن شامل دو لایهٔ اصلی است:

- **control-brain** — کنترل‌پلین RBAC چندکاربره: start/stop/test/status پروژه‌ها با لاگ تغییرناپذیر (hash-chain)
- **ziman-agent** — ورکر تولید محتوای propose-only: draft کپشن/پست/DM با گارد ظرفیت D4 و بودجهٔ API

**وضعیت:** ۴۰/۴۰ تست سبز. T11 ارتقا به VERIFIED. zero execution outward. هیچ فروش واقعی ثبت نشده.

---

## 2. نمای کلی معماری

```text
┌─────────────────────────────────────────────────────────────────────┐
│                         OCTOPUS (Architect)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │ Heart (beat) │  │ SignalHub    │  │ Evolutionary Doctor      │  │
│  │   read-only  │  │ advisory     │  │ RFC sandbox → human-append│  │
│  └──────┬───────┘  └──────┬───────┘  └──────────────────────────┘  │
│         │                 │                                        │
│  ┌──────▼─────────────────▼──────────────────────────────────┐    │
│  │              ZIMAN LIMB (propose-only)                      │    │
│  │  ┌─────────────────┐        ┌─────────────────────────┐   │    │
│  │  │ control-brain   │◄──────►│ ziman-agent (worker.py) │   │    │
│  │  │ RBAC / ledger   │        │ content / product /     │   │    │
│  │  │ start/stop/test │        │ budget / capacity / D4  │   │    │
│  │  └─────────────────┘        └─────────────────────────┘   │    │
│  └────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Telegram Gateway │ (dry-run, NOT live)
                    │  _ops/telegram_center  │
                    └─────────────────┘
```

---

## 3. مغزِ کنترل — control-brain

### 3.1 ماژول‌های هسته

| ماژول | فایل | مسئولیت | خطوط |
|---|---|---|---|
| **Manager** | `core/manager.py` | start/stop/test/status پروژه‌ها + تزریق secret + authz | 108 |
| **Registry** | `core/registry.py` | خواندن `projects.yaml` + مدیریت لیست پروژه‌ها | 42 |
| **Safety** | `core/safety.py` | قفل ایمنی سراسری (فایل STOP + پرچم DB) | 22 |
| **Authz** | `core/authz.py` | RBAC چندکاربره (admin/operator/viewer) + نقش حاکمیت زیمان | 134 |
| **Runner** | `core/runner.py` | اجرای فرایند (spawn/kill/run) با psutil | 60 |
| **Store** | `core/store.py` | SQLite: pid, flags, events, ledger hash-chain, proposals | 229 |
| **Governance** | `core/governance.py` | چرخهٔ propose→decide با نردبان ریسک GREEN→RED | 147 |
| **Shadow** | `core/shadow.py` | گیت propose-only سرتاسری — هیچ اجرای بیرونی تا 10–30 فروش | 125 |
| **Models** | `core/models.py` | dataclassهای Project و ProjectStatus | 38 |

### 3.2 دفتر رویداد تغییرناپذیر (evt.v1)

`Store` یک **دفتر رویداد زنجیره‌ای** دارد (`ledger` table):
- ULID مرتب‌شونده (۲۶ نویسه)
- prev_hash → self_hash
- شناسهٔ تصمیم انسان‌خوان: `ZIM-DEC-YYYYMMDD-NNNN`
- تابع `verify_ledger()` کل زنجیره را بازسازی و بررسی می‌کند

### 3.3 نردبان حاکمیت (Governance)

```
GREEN   → auto (read-only)
YELLOW  → propose → admin/owner approve
ORANGE  → propose → admin/owner approve
RED     → propose → owner (SahebZiman) approve ONLY
```

- **NC-3:** هیچ نقش ایجمنتی (agent/octopus/zimanleg) حق approve/reject/defer ندارد.
- **ShadowGate:** `can_execute()` تا shadow روشن است همیشه `False`.

---

## 4. ایجنت محتوا — ziman-agent

### 4.1 معماری ورکر

`worker.py` — نقطه ورود CLI با حالت‌های:
- `--once` → یک draft
- `--dm N` → N پیام DM بازار گرم
- `--posts N` → N کپشن اینستاگرام
- `--selftest` → خودآزمایی (کد خروجی 0/1)
- `--campaign N` → تست گارد D4
- `--loop` → حلقه زنده (هر 3600s)

### 4.2 ماژول‌های زیرین

| ماژول | فایل | وظیفه | خطوط |
|---|---|---|---|
| **Content** | `ziman/content.py` | تولید draft (live/offline) + DM + پست‌ها | 165 |
| **Product** | `ziman/product.py` | ProductCard, InventorySnapshot, PhotoProductMap | 369 |
| **Capacity** | `ziman/capacity.py` | گارد D4 (ظرفیت اول) — تابع خالص | 40 |
| **Budget** | `ziman/budget.py` | گیت بودجه ماهانه AUD (fail-closed) | 75 |
| **LLM Router** | `ziman/llm_router.py` | Ollama → Anthropic API با budget gate | 77 |
| **Catalog** | `ziman/catalog_loader.py` | بارگذاری کاتالوگ | — |
| **Self Model** | `ziman/self_model.py` | مدل خود ایجنت | — |
| **Steering** | `ziman/steering.py` | هدایت رفتار | — |
| **Telegram** | `ziman/telegram_adapter.py` | آداپتور تلگرام | — |

### 4.3 گاردهای سخت

- **D4:** `check_campaign(requested, ceiling)` — هیچ کمپینی بالاتر از `units_per_week_ceiling` مجاز نیست.
- **Budget:** `can_spend(model, est_in, est_out)` — fail-closed اگر ماهانه تمام شود.
- **Shadow:** هیچ draft منتشر/خرج/ارسال نمی‌شود.
- **Offline fallback:** اگر Ollama و API هردو ناموفق باشند، قالب قطعی تولید می‌شود.

---

## 5. انسان در حلقه (HITL)

### 5.1 نقش‌ها (RBAC)

| نقش | control-plane | حاکمیت زیمان | قدرت تصمیم |
|---|---|---|---|
| **admin** (آری) | همه | owner (SahebZiman) | RED approve |
| **operator** | start/stop/test/status (پروژهٔ خود) | viewer | تا YELLOW |
| **viewer** | status only | — | هیچ |
| **agent** | — | — | هیچ (NC-3) |

### 5.2 verdict انسانی

- انتشار هر پست/کمپین = verdict
- هر خرج/پرداخت = verdict
- تغییر سقف ظرفیت (D4) = verdict
- تغییر صدای برند = verdict

---

## 6. اتصال به اختاپوس

### 6.1 نقشهٔ اتصال

| سطح | مسیر | نقش |
|---|---|---|
| Leg | `_ops/legs/ziman_leg.py` | worker limb اختاپوس |
| Wiring | `_ops/wiring.make_ziman_leg` | flag `OCTOPUS_WIRE_ZIMAN` |
| Biology | `_ops/legs/ziman_biology.py` | heart read-only + SignalHub advisory + Doctor RFC |
| Budget | `_ops/budget/budgets.yaml` | floor AU$1 |
| Telegram | `_ops/telegram_center` | gateway با leg key `ziman` |

### 6.2 قواعد بیولوژی

از `BIOLOGY-CONTRACT.md`:
- Heart = regulator، نه commander
- Nerves = advisory snapshot
- Doctor = propose-only (RFC sandbox)
- Human append = mandatory برای merge/publish/spend
- σ ≤ 1 (اگر >1 → protective mode)
- λ_persist < 0 (بدون خودپایایی)

---

## 7. قراردادها و رابط‌ها

### 7.1 adapter.yaml (read-only)

```yaml
interfaces:
  status  → read
  logs    → read (n آخرین رویداد)
  report  → read (دوره‌ای)
  audit   → read (تاریخچهٔ تصمیمات)

hard_gated_actions:
  - publish any post
  - spend any credit
  - create any public account
  - change capacity ceiling (D4)
  - change brand voice

forbidden:
  - auto-post to any platform
  - auto-spend credits
  - ship perishable hamper outside local area
  - exceed capacity ceiling
```

### 7.2 OCTOPUS-ADAPTER.md

- limb_id: `ziman`
- leg_id: `ziman-gallery`
- organ: `ZIMAN`
- parent: `OCTOPUS`
- authority: `Architect/_ops`
- nbb_cp: `shadow-only`

### 7.3 TELEGRAM-CONTRACT.md (dry-run)

- `/ziman_status` → status_snapshot
- `/ziman_inventory` → inventory_report (proposal only)
- `/ziman_products` → read CATALOG
- `/ziman_experiments` → list experiments
- `/ziman_content` → draft_content (proposal, D4-gated)
- `/ziman_memory` → list pending memory candidates
- `/ziman_decisions` → read VERDICT_QUEUE
- `/halt_ziman` → limb-halt marker (owner only)

---

## 8. سوئیچ‌های ایمنی

| سوئیچ | تریگر | اثر |
|---|---|---|
| **control-brain halt** | `python app.py halt` یا `touch control-brain/HALT` | همه پروژه‌ها refuse to start |
| **capacity D4** | campaign target > units/week ceiling | worker.py رد می‌کند |
| **budget** | credit spend > allocated | video engine halt |
| **shadow gate** | همیشه روشن تا 10–30 فروش | هیچ اجرای بیرونی |
| **STOP file** | `touch STOP` | safety.halt() → همه عملیات مسدود |
| **OCTOPUS_WIRE_ZIMAN=0** | env var | disable full limb seam |

---

## 9. بستهٔ تست

### 9.1 تست‌های control-brain

| فایل تست | چه تست می‌کند | وضعیت |
|---|---|---|
| `test_authz.py` | RBAC roles, ziman_role bridge, permissions | ✅ سبز |
| `test_governance.py` | propose→decide, risk ladder, NC-3 | ✅ سبز |
| `test_manager.py` | start/stop/test/status with authz | ✅ سبز |
| `test_octopus_bridge.py` | adapter contract, read-only | ✅ سبز |
| `test_registry.py` | YAML load, project lookup | ✅ سبز |
| `test_safety.py` | STOP file, halt/resume | ✅ سبز |
| `test_shadow.py` | shadow gate, propose-only, can_execute=False | ✅ سبز |
| `test_ziman_rbac.py` | cross-system RBAC integration | ✅ سبز |
| `test_dashboard.py` | web dashboard | ✅ سبز |
| `test_command_registry.py` | command classification | ✅ سبز |
| `test_smoke_real.py` | smoke test end-to-end | ✅ سبز |

### 9.2 تست‌های ziman-agent

| فایل تست | چه تست می‌کند | وضعیت |
|---|---|---|
| `test_budget.py` | monthly cap, can_spend, record | ✅ سبز |
| `test_catalog_loader.py` | catalog loading | ✅ سبز |
| `test_product.py` | ProductCard, InventorySnapshot, ATP | ✅ سبز |
| `test_self_model.py` | self-awareness | ✅ سبز |
| `test_ziman_registry.py` | agent registry | ✅ سبز |

**جمع:** ۴۰/۴۰ تست سبز (leg 17 + phase2/wiring 23 + smoke)

---

## 10. کدها و فایل‌ها

### 10.1 inventory کد

```
control-brain/
  core/
    __init__.py        (2 خط)
    manager.py         (108 خط)
    registry.py        (42 خط)
    safety.py          (22 خط)
    authz.py           (134 خط)
    runner.py          (60 خط)
    store.py           (229 خط)
    governance.py      (147 خط)
    shadow.py          (125 خط)
    models.py          (38 خط)
  adapters/
    __init__.py
    dashboard.py
    telegram_bot.py
    octopus_bridge.py
  app.py               (183 خط)
  run_tests.py
  tests/               (11 فایل تست)

ziman-agent/
  worker.py            (198 خط)
  ziman/
    __init__.py
    content.py         (165 خط)
    product.py         (369 خط)
    capacity.py        (40 خط)
    budget.py          (75 خط)
    llm_router.py      (77 خط)
    catalog_loader.py
    config.py
    self_model.py
    steering.py
    telegram_adapter.py
    brief.py
  tests/               (5 فایل تست)
```

### 10.2 اسکیمای داده

| schema | فایل | کاربرد |
|---|---|---|
| product_card.v1 | `PRODUCT-CARD-SCHEMA.yaml` | metadata محصول |
| inventory_snapshot.v1 | `INVENTORY-SNAPSHOT-SCHEMA.yaml` | شمارش موجودی |
| photo_product_map.v1 | `PHOTO-PRODUCT-MAP-SCHEMA.yaml` | index تصاویر |

---

## 11. شکاف‌ها و ریسک‌ها

### 11.1 بلوکرهای باز

| # | شکاف | شدت | توضیح |
|---|---|---|---|
| B1 | **عدد ظرفیت ثبت نشده** | 🔴 HIGH | units/week هنوز از production owner گرفته نشده؛ همه برنامه‌ریزی کمپین مسدود |
| B2 | **brand assets incomplete** | 🟡 MEDIUM | چک‌لیست دارایی برند هنوز تکمیل نشده |
| B3 | **telegram not activated** | 🟡 MEDIUM | TELEGRAM_BOT_TOKEN نیازمند تصمیم مالک |
| B4 | **product cards not real** | 🟡 MEDIUM | ۳۰ عکس موجود ولی Product Card واقعی برای هیچ‌کدام ساخته نشده |
| B5 | **3 runtime copies drift** | 🟡 MEDIUM | `_code/`، `_launchpad/ziman-live/`، و root می‌توانند drift کنند |

### 11.2 conflictهای شناسایی‌شده (CF-06..CF-10)

| کد | conflict | وضعیت |
|---|---|---|
| CF-06 | D4 fail-open — گارد ۶/هفته unwired؛ گیت روی ۳۰ approve | 🔴 propose-only |
| CF-07 | درخت ۴م `_launchpad/second-brain-live/` قابلیت SEND واقعی + PII + کلید DeepSeek با برچسب Anthropic | 🔴 propose-only |
| CF-08 | ATP fail-open روی timestamp کهنه/آینده | 🔴 propose-only |
| CF-09 | memory کاملاً paper | 🟡 propose-only |
| CF-10 | — | — |

### 11.3 ریسک‌های معماری

| ریسک | احتمال | اثر | کاهش |
|---|---|---|---|
| Drift بین ۳ کپی runtime | بالا | ناسازگاری | یکی canonical تعیین شود |
| ShadowGate خاموش شود بدون 10–30 فروش | پایین | اجرای زودهنگام | فقط owner حق خاموش‌کردن |
| KeePassXC password interactive | متوسط | اتوماسیون ناقص | رمز در env یا keyfile |
| psutil dependency در runner | متوسط | fail در محیط بدون psutil | graceful fallback |

---

## 12. توصیه‌ها

### 12.1 فوری (P0)

1. **ظرفیت را ثبت کن:** production owner باید units/week واقعی را بدهد تا D4 معنادار شود.
2. **کپی canonical تعیین کن:** فقط یک نسخه runtime معتبر باشد (`_launchpad/ziman-live/` یا root).
3. **CF-06 را ببند:** گارد ۶/هفته را wire کن یا ۳۰ را به "owner-verified" تغییر بده.

### 12.2 کوتاه‌مدت (P1)

4. **Product Card واقعی بساز:** از ۳۰ عکس موجود شروع کن؛ خانوادهٔ ZIM (F1–F4) را به C1–C4 map کن.
5. **تست biology/wiring روی ویندوز اجرا کن:** تست‌های `_ops/tests/test_ziman_biology.py` را run کن.
6. **Telegram gateway فعال‌سازی:** BotFather + owner allowlist + shadow week.

### 12.3 میان‌مدت (P2)

7. **Dashboard auth کامل شود:** ۸ تست RBAC سبز ولی dashboard auth pending است.
8. **Video engine (Higgsfield) را به کاتالوگ متصل کن:** ۱۰ method + credit budget.
9. **Funnel tracker را با دادهٔ واقعی پر کن:** از فروش اول.

---

> **پایان گزارش.**  
> هرگونه تناقض یا ابهام → `⚑ برای معمار`  
> منبع حقیقت: `PROJECT.md` + `MANIFEST.yaml` + `BIOLOGY-CONTRACT.md`
