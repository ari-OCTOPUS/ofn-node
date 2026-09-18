# LANE-REPORT — OCTOPUS-BRAIN-WIRING-SCAN-20260918 (ساخت مگاپرامپت + اجرای کامل)

GOV_VERSION=V8 · LADDER=L2 · runtime فقط‌خواندنی (فقط دو نوشتن: seed + receipt روی ۱۳۸)

## جواب سه سؤال (عدد، نه روایت)

**۱) چند مغز؟ → ۳۲ مغز.** تفکیک: ۵ provider بیرونی (deepseek-flash پیش‌فرض با ۲۸ فراخوان، sakana-fugu، gpt-5.6-terra، claude-sonnet-5، gemini-3.8-flash) + ۱ مسیر محلی رایگان (`local-insufficient`) + ۱۷ لایهٔ decision-code (ops_agent، owner_reply/ask، action_executor، proposal_intake، money_*, revenue_state، deep_scan، glass، imap/reply_alert، b2b_discovery، coding-worker، fleet-scheduler، think_pool، self-model، cognition_factory) + **۶ سرویس دائمی لایهٔ mesh** (`/home/ari/octopus-mesh/bin`: router، supervisor، control-router، cycle-settler، verify-dispatcher، bridge + کیت ۹‌ماژولی octomesh) + ۳ دفتر حافظه.
> کشف اصلی: **دو ارگانیسم موازی** — `ofn/` (تایمری) و `octopus-mesh/` (دیمن‌های دائم). دومی هیچ رسیدی در `state/receipts` ندارد (BW-05).

**۲) سیم‌کشی کامل است؟ → نه: ۲۱ یال از ۵۰ (۴۲٪) تاریک یا شکسته.**
`WIRED-LIVE 24 · WIRED-DARK 15 · DANGLING 5 · MISSING 4 · ORPHAN 2`
سه یال DANGLING که دردناک‌اند (همه با شاهد grep=0): `painting_call_log` (جدول CRM که #248 merge کرد **هیچ خواننده‌ای ندارد**)، `v_account_last_call` (وضعیت تماس هرگز روی کارت به‌روز نمی‌شود)، `AUTO_DISCOVERY_TAG`.
پنج ناحیهٔ state **مرده‌اند**: cognition (۰۹-۱۵)، durability (۰۹-۱۵)، glass (۰۹-۱۶)، fleet-memory (۰۹-۱۶)، fleet-nodes (۰۹-۱۶)، of-draft-queue (۰۹-۱۶).

**۳) ۷ برد کد لازم دارند؟ → مشکل «کمبود برد» نیست، «توزیع کار» است.**
| برد | بار | خوانش |
|---|---|---|
| 100 | 0.02 | **عملاً کاملاً بیکار** (۸ هسته، ۴۸G آزاد) |
| 114 / 160 / 193 | 0.39 / 0.34 / 0.47 | سبک — ۱۱۴ و ۱۶۰ units آمادهٔ نصب‌نشده دارند (F-003) |
| 180 | 1.26 | متوسط |
| 182 | 1.68 | پرکار (۲۷ سرویس؛ وظیفهٔ شاهد) |
| 138 | ~1.0–1.5 | اشباع (revenue + batch روی یک برد) |
→ ۲۰ آیتم `THROUGHPUT-PLAN.md`؛ ترتیب پیشنهادی: TP-14 → TP-10 → TP-01 → TP-04 → TP-02 → TP-03 → TP-15 (همه Class A سبک، بدون رأی مالک).

## تحویل‌دادنی‌ها
`BRAIN-CENSUS.json` (۳۲ مغز با caller/calls-per-day/هزینه/شاهد) · `WIRING-MATRIX.csv` (۵۰ یال با شاهد) · `BOARD-CAPACITY.md` (۷/۷ برد) · `THROUGHPUT-PLAN.md` (۲۰ آیتم) · `GAP-REGISTER.json` (۱۵ شکاف BW-01..15) · مگاپرامپت · تزریق لجر با رسید.

## انحراف صادقانه از معیار پایان
- **یال‌ها: ۵۰ در برابر هدف ≥۶۰.** عدد را برای سبز شدن نساختم؛ ۱۰ یال باقی‌مانده (سیم‌کشی داخلی ماژول‌های mesh و readers ناشناختهٔ self-model/fleet-memory) نیاز به trace عمیق‌تر دارند و در `GAP-REGISTER` به‌عنوان کار باقی‌مانده ثبت‌اند.
- یک شاهد UNVERIFIED ماند: `think_pool` (BW-04) — grep مصرف‌کننده نتیجهٔ متناقض داد؛ نیازمند re-probe.

## شاهدهای پایه (اندازه‌گیری همین جلسه)
- دفتر بودجه ۱۳۸ (۸۹ ردیف، ۵ provider)، inventory ماژول‌ها با mtime، جدول state-tier، grep‌های مصرف‌کننده، probe هفت برد از لپ‌تاپ (۱۳۸ با alias جدا probe نشد؛ بارش از heartbeat).
- تزریق: `seed_imported=15` → نمای زنده **۶۰۳ ردیف، ۱۵ ردیف BW** · رسید `138:state/receipts/BRAINWIRING-SEED-*.json`.

## rollback
additive: حذف پوشه + revert کامیت؛ روی ۱۳۸ فقط seed + receipt (بدون حذف ردیف).
