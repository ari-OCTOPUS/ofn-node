# B6 SOG Integration — گام ۱: Current / Delta / Preserved / Rollback

> تاریخ: 2026-07-16 · وضعیت: **سند + schema منجمد؛ هیچ سیم‌کشی/کدی انجام نشده** · مرجع تصمیم: تحلیل فوگو (گزینه B) + راستی‌آزمایی ۵-ایجنته همین جلسه
> خط قرمز (از تحلیل فوگو، لازم‌الاجرا): **B6 هیچ write authority ندارد** — نه mutation، نه kill، نه self-heal، نه budget write، نه secret access، نه direct ledger write. فقط proposal قابل‌ردشدن تولید می‌کند.

## ۰. تصحیح صادقانهٔ زمینه (قبل از هر چیز)

طرح فوگو (گزینه B) بر این فرض بود که «هیچ داده‌ای از C به F کپی نمی‌شود». ایجنت موازیِ دیگری در همان روز هم‌سطح‌سازی C→F را **اجرا کرد** (۱۱ فایل آپدیت + ۹۷ فایل افزودنی). راستی‌آزمایی مستقل این جلسه نشان داد اجرا سالم بود:

- ۷ فیکس تولیدی F دست‌نخورده (md5 ده فایل با snapshot قبل از sync یکسان)
- ۲۷۵ تست هستهٔ سبز بازتولید شد؛ suite کامل ۴۱۸ سبز + ۴۷ خطای fixture ارثی از repo اصلی nbb_cp (نه محصول sync)
- اسکن secret روی هر ۱۱۱ فایل: صفر مورد

**نتیجهٔ آشتی:** فایل‌های تحلیل‌گر C حالا داخل F زندگی می‌کنند؛ آنچه از گزینه B زنده و لازم‌الاجرا می‌ماند «درخت authority» است، نه «درخت فایل‌ها»: تحلیل‌گر SOG — هرجا اجرا شود — **فقط‌خواندنی و propose-only** است. C دسکتاپ دیگر مرجع نیست (رأی آرشیوش با مالک — [[00 - Inbox/AGENT_QUESTIONS|AGENT_QUESTIONS]]).

## ۱. Current — وضع موجود (راستی‌آزمایی‌شده)

- **F:\backup\4d_system = منبع حقیقت**، داخل مخزن git ‏F:\backup، کامیت checkpoint ‏`5a69f2c` (۱۱۱ فایل، ۹۳۷۵+ خط).
- سه سیستم رویداد هم‌زیست در F:
  1. `brain/events.py` — باسِ داشبورد زنده (SQLite `dashboard_events`؛ emit سهل‌گیر: نام ناشناخته فقط warning می‌گیرد ولی ذخیره می‌شود).
  2. `control_plane/` — لایهٔ حاکمیت افزودنی v1..v5 (observe→shadow→approve→kill→self-heal)؛ همهٔ flagهای زنده default-OFF؛ تنها اجراکنندهٔ خودکار `supervisor.py` است آن هم فقط پشت `CONTROL_PLANE_SELF_HEAL`.
  3. `src/nbb_cp/kernel/events.py` — ledger زنجیرهٔ هش append-only (نصب‌نشده؛ فقط زیر pytest importable).
- دو حلقهٔ بلندمدت مستقل روی ماشین: ارگانیسم vault ‏(`_ops/organism.py`، ۴۰KB) و دیمن 4d ‏(`brain/daemon.py`). **هیچ‌کدام دیگری را supervise نمی‌کند** — پرامپت اولیهٔ فوگو این دو را خلط کرده بود؛ B6 باید آن‌ها را دو ارگان جدا ببیند.

## ۲. Delta — گام ۱ دقیقاً چه چیزی اضافه کرد

فقط دو artifact، صفر سیم‌کشی:

1. همین سند.
2. **schema منجمد:** [`docs/schemas/b6.sog.proposal.v1.json`](schemas/b6.sog.proposal.v1.json) — شامل `model_version` / `anchor_hash` (sha256 لنگرهای E_shadow/Δ_self/identity=0.135073) / `idempotency_key` / `authority: propose-only` سخت‌کد. منجمد یعنی: هر تغییر = فایل نسخهٔ جدید `v2`، هرگز ویرایش این فایل.

هیچ تغییری در `brain/events.py` (VALID_EVENTS)، `control_plane/flags.py`، `registry.yaml` یا `policy.py` انجام **نشد** — این‌ها گام ۲اند و پشت تصمیم باز «انتخاب باس» (بخش ۵).

## ۳. Preserved — چه چیزهایی عمداً دست‌نخورده ماند

- ۷ فیکس تولیدی F (‏events/budget/automation/daemon/self_evolve/autoloop/research_store‏) + ماژول‌های پشتیبان `_io_utils`/`git_watcher`/`kernel_consumer`.
- rename غیرفعال‌سازی `telegram_bot_unified.py.DISABLED-409-FIX` (فیکس 409؛ در checkpoint به‌صورت rename ثبت شد).
- کل نردبان v1..v5 و flagهای default-OFF؛ `restart_after_halt = REQUIRE_APPROVAL` (سطح مالک) طبق policy.
- دکترین‌های vault: ‏[[06 - Architecture Maps/ADR-001 Pulse-Source coupled-not-merged|ADR-001 coupled-not-merged]] و extend-don't-rival — B6 پلین چهارم نمی‌سازد، ledger موازی نمی‌سازد.

## ۴. Rollback — مسیر برگشت هر لایه

| لایه | برگشت |
|---|---|
| این سند + schema | حذف دو فایل (هنوز هیچ‌چیز به آن‌ها wired نیست) — دقیقاً شرط rollback گام ۱ فوگو |
| کل هم‌سطح‌سازی C→F | ‏`git revert 5a69f2c` یا بازگردانی از snapshot فایل‌سیستمی `F:\backup_snapshots\4d_system_20260716_154902` |
| گام ۲ آینده (adapter پشت flag) | خاموش‌کردن flag (default همین حالا OFF خواهد بود) |

## ۵. تصمیم‌های باز (مالک — در [[00 - Inbox/AGENT_QUESTIONS|AGENT_QUESTIONS]] ثبت شد)

1. **انتخاب باس برای گام ۲:** ‏(الف) باس داشبورد `brain/events.py` — کم‌اصطکاک، همین امروز قابل shadow؛ (ب) ledger ‏nbb_cp — طبق منشور `second-brain/agents/B6_AGENTOPS_NBB.md` خانهٔ دکترینیِ B6، ولی نصب/اجرا نشده. توصیه: shadow روی (الف)، مهاجرت به (ب) بعد از نصب nbb_cp با رأی جدا.
2. **نصب nbb_cp** ‏(`pip install -e`) — روی محیط پایتون F اثر می‌گذارد؛ بدون رأی انجام نمی‌شود. (۴۷ خطای fixture ارثی suite کامل مستقل از این نصب است.)
3. **سرنوشت C دسکتاپ** — دیگر مرجع نیست؛ آرشیو طبق قانون «هرگز حذف نکن».

## ۶. گام‌های بعدی (پیش‌نویس گام ۲ و ۳ فوگو، اجرا فقط بعد از رأی باس)

- گام ۲: ‏`B6Adapter` نازک در F پشت `CONTROL_PLANE_B6_SOG=False` — فقط snapshot فقط‌خواندنی + validate خروجی تحلیل‌گر با schema v1؛ ثبت کانال `b6_sog` در `registry.yaml` (وضعیت PARTIAL تا channel_doctor شواهد مثبت ببیند)؛ نگاشت action در `policy.py` (‏propose=SHADOW_LOG، هر apply=REQUIRE_APPROVAL).
- گام ۳: اجرای تحلیل‌گر به‌عنوان process جدا، بدون secret، با `control_plane`/`nbb_cp` غیرفعال، روی replay/dry-run.
