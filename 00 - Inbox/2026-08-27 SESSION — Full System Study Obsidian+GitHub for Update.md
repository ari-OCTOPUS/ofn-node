---
type: session-note
created: 2026-08-27
agent: "ZCode (GLM-5.3) — مأموریت مالک: کامل ابسیدین + گیت‌هاب بخوان، همه‌چیز یاد بگیر، آمادهٔ آپدیت شو"
scope: "read-only study؛ هیچ فایل زنده/TCB دست نخورد؛ فقط همین نوت additive نوشته شد"
status: verified (منابع با مسیر فایل)
next: "انتخاب مالک: کدام آپدیت اول (گزینه‌ها در §۶)"
---

# مطالعهٔ کامل سیستم — 2026-08-27 (پیش از آپدیت)

> مالک: «هرچی تا الان ساختیم پره از جعبه سیاه / قاطی‌پاتی — همه‌چیو یاد بگیر، می‌خوایم آپدیتش کنیم».
> این نوت خروجی آن مطالعه است: نقشهٔ واقعی سیستم + کاتالوگ جعبه‌های سیاه + گزینه‌های آپدیت.

## ۱. سه لایهٔ حقیقت (منبع اصلی «قاطی‌پاتی»)

1. **درخت زندهٔ `F:\backup`** — ارگانیسم واقعی. همین الان ۶ پروسهٔ پایتون بالا: `organism.py` (8771) · `cortex/cortex.py` (8772) · `live/server.py` (8773) · `telegram_center/center.py` (بات ۲) · `miniapp_gateway.py` (8774) · extract_graph. beat 52218، خرج ماه AU$1.07، پروفایل `live` همهٔ wireها روشن. شاخهٔ git: `rescue/octopus-live-tree-20260821` — **۳۰۲ کامیت جلوتر از master** و ~۱۱۴۹ تغییر کامیت‌نشده (بیشترش state runtime در `_ops/state`).
2. **گیت‌هاب `ari322` (۳ مخزن خصوصی) — همه کهنه:**
   - `langar`: آخرین تغییر **2026-06-28** — بات سلامت/HRV شخصی (bot.py 1916 خط، ۲۳ جدول SQLite، CORE شناختی، brain providers، researcher). با «langar» داخل والت (`03 - Projects/اونلی فنز/langar/langar_bot.py` = کاکپیت Project-F) **کاملاً متفاوت** است — دو پروژهٔ هم‌نام.
   - `ofn-node`: آخرین تغییر **2026-08-04** — هستهٔ kernel/adapters/packs برای Orange Pi. نسخهٔ زندهٔ واقعی روی Board2 (138) شاخهٔ `ofn/cockpit-v2-20260827` است، **بدون upstream گیت‌هاب**.
   - `Armin`: **2026-06-30** — فقط دو فایل AI Farm؛ سند «سیستم-همیشه-روشن» = داستان پیدایش LANGAR (بات HRV تک‌کاربره با /log /trend /halt /resume).
   - نتیجه: **گیت‌هاب آینهٔ کهنه است نه منبع حقیقت.** ریموت واقعی: `E:/germline/octopus.git`.
3. **بردها:** Board2=DietPi 192.168.0.138 (پاهای کسب‌وکار: 8791 Ziman، 8792 Painting/lead، 8793 Studio، 8796 bridge، 8895 hypno-fugu) · 180 (qwen3-0.6b) · 182 (sensoriom، بدون LLM). وضعیت امروز: `06-EVIDENCE/OCTOPUS-OWNER-BOARD-2026-08-27/LIVE-TRUTH.md`.

## ۲. معماری در یک نگاه (همان که واقعاً می‌چرخد)

- **لایه‌ها:** قانون (CLAUDE.md/TCB امضاشده) → حافظه (Obsidian+git+ledger ژنوم 14,168 رکورد) → پاها (Ziman/Painting/Studio/…) → ارگانیسم `_ops` (~700 ماژول: heart, cortex, budget, neural, epistemics, events, governor) → فرابرین (Architect/Doctor/Prime) → حکمرانی (مالک + ۲ بات).
- **دو بات زنده:** `@Robo2725_bot` (approval درون‌ارگانیسم) + `@intergrade2725_Bot` (Center، center.py ~400KB/6212خط). ۸ بات دیگر در `_ops/BOTS-REGISTRY.md` خواب/مرده.
- **LLM:** fugu روی 138:8895 (حجم) · qwen روی 180 (لوکال) · deepseek-v4-flash فقط collab_chat لپ‌تاپ (پرچم paid خاموش).
- **TCB:** ۱۵ فایل Ed25519 امضاشده، enforce=1 — ویرایش = halt واقعی runtime.

## ۳. جعبه‌های سیاه کشف‌شده (خلاصهٔ کامل برای آپدیت)

**در langar (گیت‌هاب):** پوشهٔ `_verify/` کپی‌های کهنهٔ db/migrations (schema v3 در برابر v8) با رفتار واگرا؛ کد researcher بین langar و langar-pro سه‌نسخه‌ای (synthesizer پرو با امضای فراخوان ناسازگار)؛ BrainRouter و ACELoop و CoachAgent و search_semantic و Contract.allows همه **ساخته‌شده ولی هرگز وصل‌نشده**؛ نام «armin» و مدل claude هاردکد؛ دو بانک سؤال تکراری با کلیدهای متفاوت.

**در ofn-node (گیت‌هاب):** `hmac_variants()` موقتیِ جامانده؛ گیت `partner_precondition` در pack هست ولی در `base_closed_gates` نیست (بسته‌بودنش فقط در تست hardcode شده)؛ سهم quota ها ۱٫۰ سرِ_POINTER و اضافه‌شدن mining می‌شکند؛ `__version__` پایتون 0.1.0 در برابر v0.8.0 مستندات؛ outbox فرستندهٔ واقعی ندارد (عمدی).

**در والت/درخت زنده:** center.py تک‌فایل ۴۰۱KB (WORKLOCK)؛ governor.py زنده ولی untracked (خطر git clean)؛ ۱۶ تناقض باز C-016..C-054 (کلیدها: C-037 B1 بدون امضا، C-042 rounding، C-045 temporal skew، C-041 بدهی frontmatter 345/740)؛ درخت کاری ۱۱۴۹ فایل کامیت‌نشده؛ full-loop تلگرام ورودی هنوز BLOCKED (A18 فقط canary narrow)؛ MIniApp بدون URL عمومی؛ SIG-IV منتظر راستی‌آزمای مستقل.

## ۴. قواعد طلایی که آپدیت باید رعایت کند

`git add -A` هرگز · حذف ممنوع فقط move · پوش فقط با کلمهٔ مالک · `run_all.py` کورکورانه نه · اسرار هرزش · پیش از ادعا نردبان شواهد · WORKLOCK چهار فایل · `.cmd`/`.bat` با ادیتور متن نه.

## ۵. سلامت امروز لپ‌تاپ

RAM 94.5٪ پر (firefox/Grok Bot/Cursor/llama-server بزرگ‌ترین‌ها) — برای هر آپدیت سنگین، اول فضا آزاد کن. بقیه: index.lock غایب، FREEZE/HALT فقط شواهد کهن.

## ۶. گزینه‌های آپدیت (منتظر انتخاب مالک)

- **A — یکپارچه‌سازی سه‌مخزنی** (پیشنهاد سند مالک): قرارداد مشترک octopus-contracts + event spine + inbox/outbox استاندارد؛ شاخهٔ `feat/octopus-unified-spine`.
- **B — همگام‌سازی گیت‌هاب:** ارگانیسم زنده/OFN زنده را به مخازن ari322 برگردان (الان ۳ هفته تا ۲ ماه عقب‌اند).
- **C — بهداشت درخت زنده:** کامیت‌کردن ۱۱۴۹ تغییر (تفکیک state از evidence)، merge شاخهٔ rescue به master، رهانیدن governor.py.
- **D — بستن جعبه‌های سیاه کد:** حذف/وصل dead-code های langar، رفع گیت studio، شکستن center.py.
- **E — بستن حلقهٔ تلگرام / SIG-IV** (کار در جریان موجود).

---
*منابع کلیدی: گزارش‌های full-read سه مخزن (کلون در F:\tmp\github-study) · `OCTOPUS/CURRENT-TRUTH.md` · `_ops/BOTS-REGISTRY.md` · `01 - Dashboard/HANDOFF.md` · `06-EVIDENCE/OCTOPUS-OWNER-BOARD-2026-08-27/*` · `01-TRUTH/CONTRADICTIONS.md`.*
