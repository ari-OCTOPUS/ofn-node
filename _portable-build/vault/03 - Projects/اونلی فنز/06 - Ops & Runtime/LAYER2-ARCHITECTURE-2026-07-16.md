# 🏗 Layer 2 Architecture — Project-F (2026-07-16)

> چهار قابلیتِ رقبای ۲۰۲۷ آورده شد داخل پروژه، روی یک **data spine** مشترک.
> ۱۰۰ → ۱۴۸ تست سبز (+۴۸). همهٔ safety netهای لایهٔ ۱ دست‌نخورده.

---

## معماری: DataSpine

به‌جای چهار جزیرهٔ جدا، یک منبعِ حقیقت یکپارچه در `brain/store.py`:

```
brain/store.py (DataSpine)
   ├── FanDB        → langar/fan_db.json     (segments, LTV, tags, last-contact)
   ├── VaultBank    → langar/vault.json      (content assets, fair rotation, metrics)
   ├── KPIRollup    → langar/kpi.json        (bucket هفتگی، trend)
   └── OctopusState → langar/octopus.json    (heartbeat، tick، isolated fallback)

      ▲                ▲                ▲                ▲
      │                │                │                │
  fan_admin       acquisition_pipe   /kpi real       /octopus bridge
  /fan_*          (seeds از vault)   /kpi_record     /octopus_tick
                                    + FAQ engine     (faq_engine.py)
```

---

## قابلیت‌های جدید

### ۱) Fan CRM (پایهٔ همه‌چیز)
- **فایل‌ها:** `brain/store.py` (FanDB) + `langar/fan_admin.py`
- **دستورها:** `/fan_add` `/fan_list [seg]` `/fan_buy <alias> <usd> [kind]` `/fan_tag` `/fan_stats`
- **segments خودکار:** vip (LTV≥$50) / regular / lurker / churned
- **صفر PII:** fan_id = sha1(alias)[:12] — نام واقعی هرگز ذخیره نمی‌شود

### ۲) Vault (content bank)
- **فایل‌ها:** `brain/store.py` (VaultBank) + `langar/vault_admin.py`
- **دستورها:** `/vault_add <tag> <hook> [channel]` `/vault_list [tag]` `/vault_metric <id> <up> [com] [unl]`
- **wire به acquisition:** `acquisition_pipeline._seeds()` حالا اول از vault می‌خونه (fair rotation)، fallback به brain، سپس _SAFE_HOOKS
- `finalize()` خودکار `vault.mark_used()` صدا می‌زنه

### ۳) KPI واقعی (`/kpi` دیگر disabled نیست)
- **فایل‌ها:** `brain/store.py` (KPIRollup)
- **دستورها:** `/kpi` (نمایش) + `/kpi_record <usd> <ppv> [posts] [rate]` (ثبت جمعه)
- **منبع:** KPIRollup + FanDB.summary → اعداد واقعی، نه template
- اگه داده نیست، صفر صادقانه نشان می‌دهد (هرگز fabricated)
- `/report` هم به KPI واقعی وصل شد

### ۴) Octopus bridge (واقعی، نه تزئینی)
- **فایل‌ها:** `langar/langar_bot.py` (`_octopus_card`, `_octopus_tick`) + `brain/store.py` (OctopusState)
- **دستورها:** `/octopus` (status) + `/octopus_tick` (یک tick advisory)
- **صادقانه:** اگه `orchestrator.py` یا `_ops/neural` غایب باشد → «isolated heartbeat» (دروغ نمی‌گوید)
- اگه موجود باشد (که audit نشون داد هست) → tick واقعی اجرا، beat/pain/messages ثبت
- این اولین اتصالِ واقعی لنگر به orchestrator (قبلاً فقط User-Agent string بود)

### ۵) FAQ auto-draft (HITL + auto)
- **فایل‌ها:** `brain/faq_engine.py`
- **دستور:** `/dm_inbox <incoming text>`
- **pattern matching:** price/custom/welcome/winback → draft سریع با [placeholders]
- **مرز سخت:** هیچ‌چیز autonomous ارسال نمی‌شه — فقط draft auto-z'd می‌شه، آری هنوز `/dm_ok` لازمه
- این «FAQ auto» یعنی اولین draft سریع‌تر میاد، نه ارسال خودکار

### ۶) Studio dead buttons اصلاح شد
- `s:trend` / `s:ppv` / `s:stats` در ADVANCED_MENU بودن ولی unreachable
- حالا: دکمهٔ «⚙️ بیشتر» در MAIN_MENU → به ADVANCED می‌ره
- labels از «🔒 brain/engine» (غلط) به truthful تغییر کرد

---

## چه چیزی آورده نشد (عمداً)

| قابلیت | چرا نه |
|---|---|
| **Autonomous AI chat** (مثل Izzy/SuperCreator) | نقض ToS OF → ban. legal risk ۲۰۲۷ |
| **AI voice cloning** | NO FAKES Act (فدرال) — تا $۷۵۰K جریمه |
| **Mass DM بدون HITL** | ban همه پلتفرم‌ها |

این‌ها رقبا دارن می‌سازن ولی ۲۰۲۷ ممنوع می‌شن. ما صبا (انسان واقعی) رو داریم — این مزیت‌مونه.

---

## migration safety

- همهٔ state files در `langar/` (کنار state موجود) — یک پایش‌گاه
- atomic write (.tmp → rename) — restart-safe
- fail-soft: فایل خراب = default خالی، نه crash
- backward-compat: اگه vault/fan/kpi غایب باشند، pipeline مثل قبل کار می‌کنه

---

## تست‌ها (۱۴۸ سبز)

| فایل | تعداد | چه تست می‌کند |
|---|---|---|
| `tests/test_store.py` | ۲۴ | DataSpine + ۴ کلاس |
| `tests/test_layer2_integration.py` | ۲۴ | fan/vault/faq/octopus/pipeline-vault |
| (لایهٔ ۱) test_warmup/dm/warning | ۳۸ | safety nets (دست‌نخورده) |
| (موجود) بقیه | ۶۲ | brain/langar/studio/pipeline |

---

## دستورهای جدید در لنگر (۱۳ تا)

```
Fan:    /fan_add /fan_list /fan_buy /fan_tag /fan_stats
Vault:  /vault_add /vault_list /vault_metric
KPI:    /kpi /kpi_record
Octopus: /octopus /octopus_tick
FAQ:    /dm_inbox
```

---

## جمع‌بندی

| قبل (لایهٔ ۱) | بعد (لایهٔ ۲) |
|---|---|
| ۳ safety net | ۳ safety net (دست‌نخورده) |
| DM HITL فقط | DM HITL + FAQ auto-draft |
| `/kpi` disabled | `/kpi` واقعی |
| هوک‌های نمونه | Vault bank |
| بدون CRM | Fan CRM |
| Octopus تزئینی | Octopus bridge واقعی |
| ۳ dead button | ۰ dead button |
| ۱۰۰ تست | ۱۴۸ تست |
