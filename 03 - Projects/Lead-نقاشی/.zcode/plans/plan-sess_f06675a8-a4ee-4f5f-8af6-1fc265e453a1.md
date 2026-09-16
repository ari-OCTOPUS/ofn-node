## هدف
یک سند Markdown جدید به نام `Synthesis_Revised_2026-07-12.md` در ریشهٔ پروژهٔ `Lead-نقاشی` می‌سازم که سنتز قبلی spider/octopus را **بر اساس اعتبارسنجی واقعی کد** اصلاح می‌کند. هیچ فایل موجودی تغییر نمی‌یابد؛ فقط یک فایل جدید افزوده می‌شود.

## چیزی که سند خواهد گفت (بر اساس واقعیت تأییدشده)

### بخش ۱ — نگاشت زیست‌شناسی عنکبوت (فقط قسمت‌های واقعی)
- **قلب / LANGAR ledger** = `src/audit.py` — SHA-256 hash-chained، append-only، با `_append_lock` (خط ۲۵)، `_sanitise_payload` (PII → hash ref، خط ۲۸-۳۸)، `verify_chain` (خط ۱۰۷-۱۴۷). **تأیید شد.**
- **مغز / GWT hub** = `src/orchestrator.py` + `src/queue.py` — ولی **synchronous**، نه asyncio-based. فراخوانی inline روی call stack.
- **شش پا** = `src/agents/{asset,audience,channel,content,lead_capture,researcher}.py` — بدون BaseAgent/Protocol/ABC. **E25 تأیید شد.**
- **عصب‌کشی / I/O boundary** = `کاریابی/bot/telegram_bot.py` + harvesters — `main.py` از asyncio برای Telegram polling استفاده می‌کند، ولی `_is_authorized()` روی هر ۸ handler اعمال می‌شود (خط ۴۸-۵۸). **E24 رد شد.**
- **دکتر / recovery** = `src/resilience.py` — synchronous retry با exponential backoff + jitter، `before_attempt` governance hook (خط ۷۲-۷۳)، idempotency keys. نه event loop مشترک. **E15 رد شد.**

### بخش ۲ — حفره‌های واقعی (۳ مورد تأییدشده)
| حفره | فایل | وضعیت |
|------|------|-------|
| **E25** | `src/agents/*.py` | ✅ تأیید — شش کلاس بدون base/protocol/ABC |
| **E23** | `کاریابی/bot/harvesters/` + `db.py:110` | ⚠️ نیمه‌تأیید — provenance پایه داریم ولی quarantine/schema-validation نداریم |
| **E-new** | `harvesters/keywords.py` (مفقود) | 🆕 کشف‌شده — هر سه harvester از آن import می‌کنند ولی فایل در repo نیست |

### بخش ۳ — ادعاهای ساختگی که حذف می‌شوند (با توضیح صادقانه)
| ادعا | چرا غلط بود | منبع |
|------|------------|------|
| **E15** (shared event loop) | کد کاملاً synchronous است؛ `main.py` فقط برای Telegram I/O از asyncio استفاده می‌کند | `resilience.py` با `for` + `time.sleep` |
| **E16** (`is_human=1` column) | چنین ستونی وجود ندارد؛ schema واقعی: `id, prev_hash, entry_hash, event_type, entity_id, payload, timestamp` | `audit.py:93-98` |
| **E24** (bot بدون auth) | `_is_authorized()` روی هر ۸ handler اعمال می‌شود | `telegram_bot.py:48-58` |

### بخش ۴ — ۷ ایدهٔ spider-inspired (بررسی مجدد)
از ۷ ایدهٔ قبلی فقط آن‌هایی را نگه می‌دارم که روی حفرهٔ واقعی سوارند:
- **Neuromere Contract** (برای E25) — BaseAgent protocol
- **Slit Sensilla Quarantine** (برای E23) — quarantine table قبل از `save_lead`
- ایدهٔ **Pheromone Audit** را تبدیل می‌کنم به "external HMAC on hash chain" چون نقطه‌ضعف واقعی audit (نه `is_human`) همین است: زنجیره خودارجاعی است و بدون کلید خارجی از rewrite کامل در امان نیست
- ایده‌های Web Rebuilding Portfolio، Test Pluck Gateway، Supercontraction، Molting را حذف یا mark می‌کنم چون روی ادعاهای غلط سوار بودند

### بخش ۵ — متا-پرامپت برای ایجنت بعدی
فقط روی ۳ حفرهٔ واقعی، بدون ادعای غلط. نام‌ها provisional، حق veto با Ari.

## فایل‌ای که ساخته می‌شود
- **جدید:** `F:\backup\03 - Projects\Lead-نقاشی\Synthesis_Revised_2026-07-12.md`
- **تغییر فایل موجود:** هیچ
- **حذف:** هیچ

## چرا فقط فایل جدید
قانون اساسی OLP-1: «additive evolution over destructive rewrite». سنتز قبلی را بازنویسی نمی‌کنم (دسترسی هم ندارم چون در sandbox ایجنت دیگر است)؛ یک سند جدید می‌سازم که خودش را به‌عنوان "نسخهٔ اصلاح‌شده بر اساس deep-read کد واقعی" معرفی می‌کند.