---
type: reference
status: active
tags: [schema, frontmatter]
created: 2026-07-03
updated: 2026-08-03
---

# Property Schema — زبان داده Vault (تک‌منبع حقیقت)

> هر کلید فرانت‌متر که اینجا نیست، **خطا**ست. کلید جدید = ویرایش این نوت + `.obsidian/types.json` در همان جلسه، با تأیید مالک. ایجنت‌ها هرگز کلید اختراع نمی‌کنند.

## ۱. کلیدهای هسته (همه نوت‌ها)

| کلید | نوع | مقادیر مجاز / قالب |
|---|---|---|
| `type` | text | `project` \| `knowledge` \| `log` \| `telegram-log` \| `person` \| `agent` \| `moc` \| `reference` \| `handoff` \| `dashboard` \| `instructions` \| `report` \| `research` \| `prompt` \| `architecture` \| `design` \| `proposal` \| `runbook` \| `tasks` |
| `project` | text | wikilink داخل کوتیشن: `"[[03 - Projects/X/PROJECT]]"` — اگر به پروژه‌ای تعلق ندارد، حذف شود |
| `status` | text | `idea` \| `active` \| `paused` \| `done` \| `archived` \| `inbox` \| `draft` \| `ready` \| `superseded` — حروف کوچک، دقیق (Bases حساس به حروف) |
| `tags` | multitext | فقط موضوعی (painting، crypto، marketing…) — هرگز status/type در تگ |
| `created` | date | `YYYY-MM-DD` |
| `updated` | date | `YYYY-MM-DD` — هر ویرایش، امروز شود |

## ۲. کلیدهای اضافی هر type

| type | کلیدهای اضافی |
|---|---|
| `project` | `kind: project\|area` (area هرگز done نمی‌شود) · `owner: text` · `start: date` · `risk_level: low\|medium\|high\|critical` · `autonomy_level: read-only\|propose-only\|execute-with-verdict\|bounded-auto` (فاز ۱ — manifest؛ تا باز بودن Security Gate همه `read-only`) |
| `knowledge` | `source: text` · اگر ایجنت‌ساخته: `created_by: agent` + `sources: multitext` (≥۲ لینک) |
| `log` / `telegram-log` | بدنه append-only؛ متادیتای هر ورودی داخل متن: `chat_id` / `message_id` / `sender` (کلید dedup: `message_id`) |
| `person` | `org` · `role` · `telegram` · `related: multitext` (wikilink کوتیشن‌دار) |
| `agent` | `model` · `trigger: telegram\|cron\|manual\|loop` · `code: path` (گسترش `loop` 2026-07-06 با verdict مالک — Learning Engine) |
| `handoff` | فقط `updated` — وضعیت مصرفی است، دانش نیست |
| `report` / `research` / `prompt` | `project` (اختیاری — wikilink پروژه مربوط) · چرخه: `inbox`/`draft` → `ready` → `done`؛ نسخه منسوخ = `archived` (گسترش 2026-07-04 با تأیید مالک) |
| `architecture` / `design` | سند طراحی/معماری پروژه (پیش از کد یا هم‌تراز آن) · کلیدهای رابطه: `parent` / `aligns_to` (wikilink به سند بالادست) |
| `proposal` | پیش‌نویس پیش از تصمیم · چرخه: `draft` → `ready` → پذیرش؛ نسخهٔ جایگزین‌شده = `superseded` (+ `superseded_by`) · کلید `extends` (wikilink به سند پایه) |
| `runbook` | رویهٔ عملیاتی گام‌به‌گام (راه‌اندازی/زنده‌سازی یک سیستم) |
| `tasks` | فهرست اقدامِ `- [ ]` یک حوزه/پروژه (تک‌فایل، نه لاگ) |
| نوت‌های حوزه هیپنوتیزم (07) | `epistemic_status: peer-reviewed\|speculative\|fiction-canon` — **اجباری** (فاز ۱)؛ fiction-canon هرگز به‌عنوان evidence در نوت‌های بیزنسی/تصمیمی cite نمی‌شود |

### ۲.۱ کلیدهای رابطه/عملیاتی (اختیاری — هر type؛ گسترش 2026-07-04 با تأیید مالک)

- **لینک بین‌سندی** (wikilink کوتیشن‌دار): `parent` · `aligns_to` · `extends` · `supersedes` · `superseded_by` — نگاشت سلسله‌مراتب و جانشینی اسناد.
- `canon_rank`: text — رتبهٔ canon نوت‌های سنتز/fiction (مثلاً `primary`/`secondary`).
- `depends-on` / `closes` / `target`: نوت‌های `prompt`/عملیاتی — وابستگی، آیتم بسته‌شده، مخاطب.
- `audits` / `result`: text — نوت‌های audit/red-team — موضوع بازرسی و خلاصهٔ یافته.
- `language`: text — زبان سند (مثلاً `bilingual`).
- `salience`: number — اسکور اهمیت ۰–۱ دیجست‌های اسکات (ورودیِ evaporation/TTL ناوگان).

### ۲.۲ کلیدهای capture ِ ماشینی (نوت‌های `telegram-log` ِ Raw — ۲۰۲۶-۰۷-۳۱، رأی capture)

- `message_id`: number — شناسهٔ پیامِ تلگرام؛ کلیدِ dedup در محدودهٔ همان `chat_id` (۲۰۲۶-۰۷-۳۱، رأی capture).
- `chat_id`: number — شناسهٔ چتِ مبدأ پیام (۲۰۲۶-۰۷-۳۱، رأی capture).
- `file_id`: text — شناسهٔ رسانهٔ تلگرام (ویس/عکس) — ثبتِ ارجاع، بدونِ دانلود (۲۰۲۶-۰۷-۳۱، رأی capture).
- `duration`: number — طولِ ویس به ثانیه (۲۰۲۶-۰۷-۳۱، رأی capture).
- `transcribed_by`: text — موتورِ transcribe ِ ویس، مثلاً `faster-whisper` (۲۰۲۶-۰۸-۰۳، رأی مالک).
- `transcript_secs`: number — مدتِ اجرای transcribe به ثانیه (۲۰۲۶-۰۸-۰۳، رأی مالک).

### ۲.۳ فهرستِ ماشین‌خوان — تک‌منبعِ حقیقتِ ابزارها (۲۰۲۶-۰۸-۰۳)

> جدول‌های بالا توضیحِ **انسانی**‌اند؛ بلوکِ زیر چیزی است که **ابزارها** می‌خوانند
> (`04 - Architect System/scripts/validate_frontmatter.py`). قبلاً همان فهرست در
> `KNOWN_KEYS` ِ آن اسکریپت هاردکد بود و بی‌صدا از این سند جدا می‌افتاد — همان
> روز که دو کلیدِ ویس اضافه شد، validator تا ویرایشِ **سومین** جا قرمز ماند.
>
> کلیدِ جدید = یک ردیف این‌جا (+ همان کلید در `.obsidian/types.json`؛ اگر یادت
> برود، خودِ validator دقیقاً می‌گوید کدام کلید کم است). مرزها را دست نزن.

<!-- SCHEMA-MACHINE:BEGIN -->
```yaml
keys:
  type: text
  project: text
  status: text
  tags: multitext
  created: date
  updated: date
  kind: text
  owner: text
  start: date
  source: text
  sources: multitext
  created_by: text
  org: text
  role: text
  telegram: text
  related: multitext
  model: text
  trigger: text
  code: text
  version: text
  aliases: multitext
  risk_level: text
  autonomy_level: text
  epistemic_status: text
  parent: text
  aligns_to: text
  extends: text
  supersedes: text
  superseded_by: text
  canon_rank: text
  depends-on: multitext
  closes: multitext
  target: text
  audits: text
  result: text
  language: text
  salience: number
  message_id: number
  chat_id: number
  file_id: text
  duration: number
  transcribed_by: text
  transcript_secs: number
types: [project, knowledge, log, telegram-log, person, agent, moc, reference, handoff, dashboard, instructions, report, research, prompt, architecture, design, proposal, runbook, tasks]
statuses: [idea, active, paused, done, archived, inbox, draft, ready, superseded]
```
<!-- SCHEMA-MACHINE:END -->

## ۳. قواعد

- کلیدها انگلیسی، حروف کوچک؛ مفرد مگر لیست (`tags`، `sources`، `related`، `aliases`).
- تاریخ‌ها فقط ISO: `YYYY-MM-DD`.
- نوت جدید همیشه از [[_Templates/project|_Templates]] ساخته می‌شود (شش قالب: project / knowledge / log / person / agent / handoff).
- نوع هر کلید در `.obsidian/types.json` ثبت است تا ابسیدین درست نمایش دهد.

<!-- منابع الگو: stephango.com/vault (types.json)، انجمن ابسیدین (Master Property Schema)، مستندات Bases (حساسیت حروف). -->
