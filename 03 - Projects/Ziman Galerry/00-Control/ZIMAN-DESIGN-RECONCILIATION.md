---
type: control-reconciliation
project: ZIMAN
status: authoritative
version: 1
updated: 2026-07-12
note: "Normative layer: overrides FOUNDATION-DESIGN and TELEGRAM-GOVERNANCE on any conflict"
---

# سند ج — لایهٔ آشتی (Reconciliation Layer)

> **اولویتِ نرماتیو:** این سند بر متنِ درون‌بخشیِ سند الف (فوندیشن) و سند ب (حکمرانیِ تلگرام) اولویت دارد. هر جا تعارض باشد، مقدارِ این‌جا معتبر است و متنِ آن دو `SUPERSEDED`. دکترین: IMPROVE, DON'T REWRITE. خروجیِ بازرسِ سازگاری (۱۵ مورد) این‌جا حل شده.

## R0 — تصحیح‌های الزام‌آورِ حقیقت

| # | مکان | نادرست | معتبر | دلیل |
|---|---|---|---|---|
| F1 | A1 §2-4 + baseline پرچم۱ | «۱۰ محصولِ F4» فاسدشدنی | **۱۱ محصولِ F4** (ZIM-F4-01..11) همه فاسدشدنی → «فقط تحویل محلی» | جمع ۱۸+۲+۴+۱۱=۳۵؛ عددِ ۱۰ یک محصول (ZIM-F4-11) را از قانونِ محلی می‌گریزاند (ریسکِ قانونی). |
| F2 | B3 پیام‌های نمونه | «۰.۸ از ۱۵ AUD» به‌عنوان واقعی | `[نمونهٔ نمایشی] <spend>/15.00 AUD` | هیچ عددِ مصرفِ واقعی وجود ندارد؛ نباید MEASURED جا بزند. |
| F3 | B3 پیام A-3 | «۳۵ محصولِ فعال» | «۳۵ محصولِ **عکاسی‌شده — هنوز غیرقابلِ فروش**» | فروش=۰، price=null، سیاستِ variant/الکل/لایسنس باز. |
| F4 | A1 §4 جدول | IMG_2812 → ZIM-F1-18 قطعی | IMG_2812 ↔ F1-18 = `[Inference / needs_owner_confirm]` | baseline فقط IMG_3378=F1-13 را گراند کرده؛ بقیه استنتاج. |
| F5 | B3 سرصفحه + A2 مقدمه | «control-plane / Product Agentِ اثبات‌شده» | «کدِ زیمان: ۲۱ تست **reported-not-rerun**» | نباید به «کدِ تأییدشده» نزدیک شود. |
| C9 | A2 EXP-A + A1 | کالکشنِ handbag-basket بی‌subtag | subtagِ `handbag-basket` رسماً به **ZIM-F1-09/10/12/13** اختصاص می‌یابد | تا EXP-A پشتوانه داشته باشد. |

## R1 — رجیستریِ واحدِ فرمان (حل O1/C3)

یک whitelistِ واحد؛ فرمان‌های دادهٔ A3 رسماً افزوده و پشتِ RBAC/escalation قرار می‌گیرند. فرمانِ خارج از این فهرست → `E_UNKNOWN_COMMAND`.

```yaml
command_registry:
  read_status:   # OCTOPUS/VIEWER · GREEN · خودکار
    [ /status, /summary, /health, /risks, /projects, /queue, /incidents, /focus ]
  data_catalog:  # propose-only · YELLOW · لاگ+خلاصه
    [ /product <id>, /photo <map>, /variant <confirm>, /reconcile, /catalog ]
  control:       # ORANGE · نیازمند approval
    [ /policy <change>, /pause <module>, /resume <module>, /mode <m> ]
  approval:      # SahebZiman only · گیتِ RED
    [ /approve <ZIM-DEC-id>, /reject <ZIM-DEC-id>, /defer <ZIM-DEC-id>, /rollback <rel>, /halt_ziman ]
```

## R2 — طرحِ واحدِ شناسه و نحوِ تأیید (حل C4)

```text
decision_id : ZIM-DEC-YYYYMMDD-NNNN     # مثال ZIM-DEC-20260712-0001
experiment  : ZIM-EXP-NN     product : ZIM-Fx-NN     verdict : ZIM-V<n>
approval syntax (canonical): /approve ZIM-DEC-20260712-0001 [scope] [artifact_hash]
```
همهٔ پیام‌های B3 و regexِ پارسرِ B2 با همین فرمت هم‌تراز می‌شوند (اسلش + خانوادهٔ ZIM). فرمتِ قدیمیِ `DZ-…` حذف.

## R3 — ساختارِ واحدِ topic (حل C2)

طرحِ شماره‌ایِ B1 **canonical** است؛ هشتگ‌های موضوعیِ A3 فقط alias:

| هشتگِ A3 | topicِ canonical |
|---|---|
| #catalog / #photos / #variants | **11 — Products & Inventory** |
| #policy | **14 — Operations** |
| #reconcile | **10 — Executive** (تصمیم) + **01 — Verdicts** (رأی) |

topicهای پایه: `00 Control · 01 Verdicts · 02 Incidents · 03 Reports · 10 Executive · 11 Products&Inventory · 12 Market · 13 Experiments · 14 Operations · 15 Memory · 16 Content · 17 Incidents · 18 Reports`.

## R4 — اسکیمای واحدِ Event Ledger (حل C5)

یک `evt.v1` که hash-chainِ auditِ B2 را در خود دارد؛ رکوردهای audit = رویداد با `event_type: audit.*`.

```yaml
evt.v1:
  seq:            integer      # یکنواختِ صعودی (منبعِ ترتیب، از audit_log ب)
  event_id:       ulid         # شناسهٔ جهانی (از A3)
  prev_hash:      sha256       # زنجیرهٔ یکپارچگی (از B2)
  self_hash:      sha256       # هشِ خودِ رکورد
  content_hash:   sha256       # هشِ محتوا (dedup)
  idempotency_key: string
  schema_version: 1
  tenant_id:      "ZIMAN"
  occurred_at:    ts;  recorded_at: ts
  actor_type:     enum [human, agent, system]
  actor_id:       string       # SahebZiman | OCTOPUS | role_id
  entity_id:      string       # product_id | decision_id | experiment_id
  event_type:     string       # product_catalogued | photo_mapped | variant_confirmed | approval_granted | audit.access ...
  evidence_pointer: string
  confidence:     number;  privacy_class: enum;  status: enum
  correlation_id: string;  causation_id: string
```
طرحِ ID واحد: `seq` = ترتیب، `event_id(ULID)` = ارجاعِ جهانی؛ هر دو، نه دو مدلِ رقیب.

## R5 — مدلِ واحدِ نقش (حل C6)

```text
SahebZiman  = مالکِ انسانی (L0) — اقتدارِ نهایی، تنها تأییدکنندهٔ RED.
OCTOPUS     = ادمینِ ایجنتیِ فنی (L2) — propose-only؛ هرگز proposal→decision نمی‌کند (NC-3).
ADMIN/VIEWER= صندلی‌های انسانیِ آتی (نه OCTOPUS). اگر ADMINِ انسانی approve_upto_YELLOW بگیرد، این یک انسان است، نه لایهٔ ایجنت.
قاعده: هیچ نقشِ ایجنتی (از جمله OCTOPUS) اختیارِ approve ندارد.
```

## R6 — نردبانِ واحدِ ریسک (حل C7)

استانداردِ چهارطبقه **GREEN / YELLOW / ORANGE / RED**. نگاشت‌ها:
```text
AMBER (B3)      → {YELLOW ∪ ORANGE}
health states   : healthy→GREEN · degraded→ORANGE · down→RED
«L0–L5» (B3)    → حذف؛ همه‌جا فقط چهار رنگ.
```

## R7 — enumِ واحدِ mode (حل C8)

```yaml
mode:
  verbosity:  [ quiet, normal, intense ]        # پیش‌فرض quiet
  control:    [ copilot, paused, telegram-only, degraded, freeze-all ]
# «autopilot» حذف شد (با propose-only ناسازگار است). copilot = propose-then-approve.
```

## R8 — رفعِ تضادِ اختیارِ qualified (حل C1)

Product Agentِ `qualified` هم برای **هر خروجیِ روبه‌مشتری** از گیتِ RED در سند ب عبور می‌کند. «خروجیِ مستقیم برای دسته‌های سبز» فقط به معنیِ **draft/تحلیلِ داخلی** است، نه ارسال. `send_DM`/`publish` همیشه RED = تأییدِ SahebZiman.

---

**اثر:** ۶ تصحیحِ حقیقت + ۸ یکپارچه‌سازیِ معماری. هیچ verdict جدیدی باز نشد؛ هیچ حقیقتِ baseline نقض نشد. سند الف و ب با این لایه، یک سیستمِ منسجم‌اند.
