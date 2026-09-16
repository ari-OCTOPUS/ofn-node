---
type: proposal
project: "[[04 - Architect System/architect/PROJECT]]"
status: draft
tags: [octopus, crm, wave-2, plan, ops-studio, cockpit]
created: 2026-08-02
updated: 2026-08-02
created_by: agent
sources:
  - "[[06 - Architecture Maps/OCTOPUS-INTEGRATION-STATUS]]"
  - "[[06 - Architecture Maps/OCTOPUS-DECISION-LOG]]"
---

# Wave-2 CRM — Plan

<!-- BEGIN GENERATED: vault-docs lane, 2026-08-02. ویرایشِ انسانی زیرِ «Owner notes». -->

> # ⛔ PLAN ONLY — هیچ‌چیز ساخته نشده
>
> این سند **طرح** است. در این جلسه هیچ جدولی، هیچ actionی، هیچ تبی و هیچ تستی نوشته نشد.
> اجرا **منتظرِ حکمِ صریحِ مالک** است. اگر جلسه‌ای این سند را خواند و فرض کرد چیزی از آن
> live است، اشتباه می‌کند — وضعیتِ سنجیده‌شده در
> [[06 - Architecture Maps/OCTOPUS-INTEGRATION-STATUS|OCTOPUS-INTEGRATION-STATUS]] است.

## پایهٔ موجود (سنجیده‌شده، نه فرض‌شده)

قبل از هر طراحی، آنچه **امروز واقعاً هست** — `_ops/agi2027_control/ops_actions.py`:

- **۴ جدول:** `leads`, `lead_notes`, `tasks`, `value_events`
  (در `_ops/agi2027_runtime/octopus_ops.sqlite3`، WAL، `synchronous=NORMAL`).
- **۶ actionِ allowlist‌شده:** `lead.create`, `lead.add_note`, **`lead.update_stage`**,
  `task.create`, `task.done`, `value.record_event`.
- **گیت:** `execute()` اولین شرطش `actor["is_owner"]` است.
- **idempotency:** `IdempotencyStore.begin(key)` قبل از هر نوشتن؛ کلیدِ پیش‌فرض
  `f"ops:{action}:{stable_hash(payload)}"`؛ تکرار ⇒ `DUPLICATE` بی‌اثر.
- **audit:** `AuditLog.append` در پایانِ **هر** فراخوانی — عبور یا رد.
- **مرزِ بیرونی:** `BLOCKED_PREFIXES` (۷ پیشوند) **قبل از** allowlist چک می‌شود.
- **پاک‌سازی:** `clean()` روی هر ورودی — توکن و ایمیل redact می‌شوند.

### ⚠️ تصحیحِ طرح

طرحی که به این lane رسید `lead.update_stage` را جزوِ actionهای **جدیدِ** Wave-2 آورده بود.
**غلط است — این action از قبل ساخته شده و در `ALLOWED_ACTIONS` هست.** Wave-2 فقط شش
actionِ واقعاً نو دارد. اگر کسی آن را «جدید» پیاده کند، یا کارِ موجود را دوباره می‌نویسد
یا بدتر، نسخهٔ دومی می‌سازد که گیت/idempotency ِ خودش را دارد.

## Schema — چهار جدولِ پیشنهادی

همه با همان سبکِ موجود: `id TEXT PRIMARY KEY`، زمان‌ها `REAL`، آرایه‌ها `*_json TEXT`،
`CREATE TABLE IF NOT EXISTS` در `init_schema` (additive — هیچ جدولی drop یا alter نمی‌شود).

### `campaigns`
| ستون | نوع | یادداشت |
|---|---|---|
| `id` | TEXT PK | `camp_<slug>` از `make_id` |
| `name` | TEXT NOT NULL | |
| `objective` | TEXT | متنِ آزادِ کوتاه |
| `status` | TEXT NOT NULL | `draft \| active \| paused \| done \| archived` — **هم‌راستا با §۶ منشور** |
| `channel` | TEXT | `manual` پیش‌فرض. **هرگز** کانالی که اتوماسیونِ پلتفرمِ بیرونی لازم دارد |
| `tags_json` | TEXT NOT NULL | |
| `notes` | TEXT | |
| `created_at` / `updated_at` | REAL NOT NULL | |

### `content_items`
| ستون | نوع | یادداشت |
|---|---|---|
| `id` | TEXT PK | `content_<slug>` |
| `campaign_id` | TEXT | FK منطقی به `campaigns.id` (بدونِ FK سختِ SQLite، مثلِ `lead_notes`) |
| `title` | TEXT NOT NULL | |
| `kind` | TEXT NOT NULL | `post \| message \| image \| video \| caption` |
| `status` | TEXT NOT NULL | `draft \| ready \| used \| archived` |
| `asset_path` | TEXT | مسیرِ نسبی داخلِ vault (`08 - Assets/…`) — **نه** باینری در DB |
| `body` | TEXT | از `clean()` رد می‌شود |
| `created_at` / `updated_at` | REAL NOT NULL | |

### `manual_send_queue`
صفِ **یادآوری برای انسان**. هیچ فرستنده‌ای ندارد و نباید داشته باشد.

| ستون | نوع | یادداشت |
|---|---|---|
| `id` | TEXT PK | `msend_<slug>` |
| `lead_id` | TEXT NOT NULL | |
| `content_id` | TEXT | |
| `status` | TEXT NOT NULL | `queued \| sent_manual \| skipped \| expired` |
| `sent_at` | REAL | فقط با `outbound.mark_sent_manual` پر می‌شود |
| `sent_by` | TEXT | همیشه `owner_manual` |
| `notes` | TEXT | |
| `created_at` / `updated_at` | REAL NOT NULL | |

> **مرزِ سخت:** این جدول یک **دفترچه** است، نه صف کار. هیچ workerی از آن نمی‌خواند.
> `status="sent_manual"` یعنی «مالک خودش، بیرونِ این سیستم، فرستاد و بعد ثبت کرد».
> این‌جا هرگز تحویلِ خودکار اضافه نمی‌شود — D-5.

### `money_events`
| ستون | نوع | یادداشت |
|---|---|---|
| `id` | TEXT PK | `money_<slug>` |
| `lead_id` | TEXT | اختیاری |
| `campaign_id` | TEXT | اختیاری |
| `direction` | TEXT NOT NULL | `in \| out` |
| `amount` | REAL NOT NULL | |
| `currency` | TEXT NOT NULL | پیش‌فرض `AUD` |
| `occurred_at` | REAL NOT NULL | زمانِ **رویداد**، جدا از `created_at` (ساعتِ ثبت) |
| `source` | TEXT NOT NULL | همیشه `manual_owner_entry` در Wave-2 |
| `metadata_json` | TEXT NOT NULL | |
| `created_at` | REAL NOT NULL | |

> **`money_events` حساب‌داری نیست.** برچسب‌زدن است. هیچ اتصالِ بانکی، هیچ تراکنش،
> هیچ محاسبهٔ مالیاتی. ورودیِ دستیِ مالک، فقط برای دیده‌شدن.

## Actions — شش تای نو

همه از **همان** `OpsActionEngine.execute` رد می‌شوند: همان گیتِ owner، همان
idempotency، همان audit. **هیچ مسیرِ دومی ساخته نمی‌شود.**

| action | ورودیِ لازم | خروجی | نکته |
|---|---|---|---|
| `campaign.create` | `name` | `campaign_id` | `status` پیش‌فرض `draft` |
| `campaign.update_status` | `campaign_id`, `status` | `previous_status`, `status` | statusِ نامعتبر ⇒ `BLOCKED invalid_status` + `allowed` |
| `content.create` | `title`, `kind` | `content_id` | `status` پیش‌فرض `draft` |
| `content.mark_ready` | `content_id` | `previous_status` → `ready` | فقط از `draft` |
| `money.record_manual` | `direction`, `amount` | `money_event_id` | `amount` عددِ متناهی؛ منفی ⇒ `BLOCKED` (جهت با `direction` است) |
| `outbound.mark_sent_manual` | `queue_id` | `previous_status` → `sent_manual` | **فقط ثبت.** هیچ پیامی فرستاده نمی‌شود |

و **`lead.update_stage` که از قبل هست** — دوباره پیاده نمی‌شود.

### قواعدِ الزامیِ پیاده‌سازی
1. هر actionِ نو به `ALLOWED_ACTIONS` اضافه می‌شود؛ dispatch در همان زنجیرهٔ `if/elif`.
2. `BLOCKED_PREFIXES` **دست‌نخورده** می‌ماند و همچنان قبل از allowlist چک می‌شود.
3. هیچ فراخوانیِ شبکه، هیچ SDK پلتفرم، هیچ کوکی، هیچ credential.
4. هر رشتهٔ ورودی از `clean()` رد می‌شود.
5. فلگِ نو (اگر لازم شد) پیش‌فرض خاموش و **بیرونِ** `wiring.PAPER_FULL_FLAGS` — D-10.
6. جدول‌ها فقط `CREATE TABLE IF NOT EXISTS`. مهاجرتِ مخرب ممنوع؛ «هرگز حذف نکن».

## UI tabs — پیشنهاد

پایه: امروز `_ops/telegram_center/miniapp/index.html` **۸ تب** دارد
(`home, studio, outbound, approvals, legs, value, registry, truth`). Wave-2 سه تا اضافه
می‌کند و ساختار/نام‌گذاریِ موجود را حفظ می‌کند.

| تب | `data-tab` | محتوا | نوشتن؟ |
|---|---|---|---|
| Campaigns | `campaigns` | فهرست + وضعیت؛ فرمِ ساخت؛ تغییرِ وضعیت | بله، owner-gated |
| Content | `content` | فهرست بر اساسِ campaign؛ ساخت؛ `mark ready` | بله، owner-gated |
| Money | `money` | رویدادهای دستی + جمعِ ساده | بله، owner-gated |
| Studio (موجود) | `studio` | + بلوکِ صفِ ارسالِ دستی با دکمهٔ «ثبتِ ارسال» | بله، owner-gated |

**قواعدِ frontend:** هر دکمه‌ی نوشتن وقتی `auth_status !== "configured"` است `disabled`
می‌شود (همان الگوی `renderStudio`)؛ همهٔ فراخوانی‌ها از `apiPost` با هدرِ
`X-Tg-Init-Data`؛ صفر secret در frontend؛ خروجیِ متنی از `esc()` رد شود.

> **پیش‌نیازِ ناخوشایند:** رشته‌های فارسیِ `app.js` امروز mojibake اند (R-6/N-5).
> تبِ نو **بعد از** آن فیکس نوشته شود، وگرنه خرابی تکثیر می‌شود.

## Tests — پنج ناوردا

main-style (D-13): `harness.setup()` اول، توابعِ `t_*`، `harness.run(checks)`, `sys.exit`.
الگو: `_ops/tests/test_tg_poll_health.py`. **نامِ فایل گزارش می‌شود؛ `run_all.py` را این
lane ویرایش نمی‌کند** (D-14).

| # | ناوردا | باید بسنجد | جهشی که باید بکُشدش |
|---|---|---|---|
| T-1 | **owner required** | هر شش actionِ نو با `{"is_owner": False}` ⇒ `DENIED owner_gate_failed` و **صفر ردیف** در DB | گیتِ owner را بردار ⇒ تست قرمز شود |
| T-2 | **idempotency** | همان action با همان payload دوبار ⇒ بارِ دوم `DUPLICATE` و شمارشِ ردیف **تغییر نکند** | `begin()` را دور بزن ⇒ قرمز |
| T-3 | **audit log** | هر فراخوانی — چه `APPLIED` چه `DENIED` چه `BLOCKED` — دقیقاً یک خط در audit بنویسد | ثبت را به شاخهٔ موفق محدود کن ⇒ قرمز («ثبت همیشه» D-6) |
| T-4 | **blocked external automation** | `onlyfans.send_dm`, `fansly.login`, `platform.scrape`, `mass_message`, `cookie_import`, `reverse_api.x` ⇒ همه `BLOCKED external_platform_automation_forbidden` | یک پیشوند را از `BLOCKED_PREFIXES` بردار ⇒ قرمز |
| T-5 | **no secret leak** | payload با توکنِ ساختگی و ایمیل ⇒ نه در DB، نه در audit، نه در پاسخِ `/api/ops` عینِ رشته پیدا شود | `clean()` را از یک مسیر بردار ⇒ قرمز |

**قواعدِ سنجش (از اشتباهاتِ ثبت‌شدهٔ همین سیستم):**
- هر گارد یک جهشِ **یکتا-لنگر** لازم دارد. `replace(..., 1)` به اولین وقوع می‌خورد که
  معمولاً تابعِ خواهر است.
- بینِ اجراها `__pycache__` را پاک کن — بایت‌کدِ کهنه قبلاً یک جهش را بی‌صدا رد کرد.
- پایهٔ تست باید **زیرِ** سطحِ هدف باشد؛ وگرنه جهش سبز می‌ماند چون از اول همان نتیجه می‌آمد.
- T-4 و T-5 باید روی DBِ **موقت** بدوند (`OCTOPUS_OPS_DB_PATH` / `OCTOPUS_OPS_AUDIT_PATH` /
  `OCTOPUS_OPS_IDEMPOTENCY_PATH` هر سه env-محورند) — هرگز روی
  `_ops/agi2027_runtime/octopus_ops.sqlite3` ِ زنده.
- «نبودِ خطا» سبز نیست. شمارِ صریحِ pass/fail یا exit code.

## خارج از دامنه — برای همیشه

اتوماسیونِ لاگینِ OnlyFans/Fansly · scraping · APIهای مهندسی‌معکوس‌شده · auto-DM ·
mass messaging · cookie import.

Wave-2 عمداً **فقط دفترچهٔ محلی** است: چیزی را برنامه‌ریزی می‌کنی، مالک خودش بیرونِ
سیستم انجام می‌دهد، بعد این‌جا ثبت می‌شود. اگر ردیفی از این طرح به تحویلِ خودکار نیاز
داشت، آن ردیف **حذف** می‌شود، نه گیتش.

<!-- END GENERATED -->

## Owner notes

<!-- دستِ مالک. حکمِ «بساز» یا «نساز» این‌جا ثبت شود. -->
