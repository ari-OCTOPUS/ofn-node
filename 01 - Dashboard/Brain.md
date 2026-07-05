---
type: dashboard
status: active
tags: [dashboard, brain]
updated: 2026-07-06
---

# 🧠 مغز زنده — وضعیت لحظه‌ای کل سیستم

> نمای یک‌نگاهیِ **زندهٔ** کل ربات، از دادهٔ واقعیِ Active Contextها. تسک `brain-pulse` هر ۳ ساعت بازنویسی‌اش می‌کند (فقط لینک/state، نه secret). هم‌راستا با [[04 - Architect System/architect/01-Project/BRAIN-UPGRADE-LOOP|BRAIN-UPGRADE-LOOP]] (D-28).
> ⚠️ نوتِ **overwrite-مجاز** — ذیل لیست سفید L3 §۳.۱ [[00 - Inbox/Prompt - منشور استقلال مغز (Autonomy Ladder)|منشور استقلال]] (ratified 2026-07-05). آخرین نبض: **۲۰۲۶-۰۷-۰۶ ~۰۶:۱۰ AEST**.

## ضربان (heartbeat) — سیستم زنده است؟

- **AUTONOMY: on** — [[00 - Inbox/Prompt - منشور استقلال مغز (Autonomy Ladder)|منشور استقلال v1]] ratified. نردبان L0–L3 فعال؛ invariantها قفل. verdict آری اخیر: «سیستم روی maximum risk» (2026-07-06) + LAPTOP-PILOT-30D روز صفر شروع شد.
- **۵/۶ تسک ratified در زمان‌بندِ زنده حاضر و enabled** (brain-focus-board · brain-pulse · mycelial-consolidator · experience-review · fleet-selection). `system-dashboard` این‌بار **کاملاً غایب** است (نه فقط disabled). طبق §۳.۳ منشور غیابِ تسک ratified یعنی restore، ولی این مورد **مبهم** ماند و اقدامی نشد: همان امروز verdict آری («زنده کن کل ساختارو») صریحاً فقط **۵ تسک ratified** را روشن کرد و تنها استثنای عمدیِ ذکرشده لاین‌های selfimprove/bio-synthesis بودند — نه system-dashboard؛ و یک verdict قبلی هنوز روی میز است (بند ۲ دفتر تصمیم‌ها ↓: حذف رسمی از جدول ۶‌تایی یا احیای کامل). مبهم → پلهٔ پایین‌تر (L0 گزارش)، بدون re-create. نبض هر تسک: [[_memory/HEARTBEAT|HEARTBEAT]].
- ✅ **`fleet-selection` دیگر miss نیست** — اولین اجرای واقعی ~۰۰:۰۴ AEST امروز ثبت شد: [[00 - Inbox/scout-digests/fleet-eval|fleet-eval]] (نگرانیِ نبض قبلی برطرف شد).
- `learning-engine-loop` (غیر جزو ۶ ratified، ولی زنده و ساعتی) در حال اجراست — تا این لحظه **صفر جهش** (بدون شاهد کافی در ledger، طبق قاعدهٔ خودش).
- ۱۹ اسکات روزانه + survival-heartbeat اکنون **enabled** (پایلوت ۳۰ روزه)؛ فقط architect-selfimprove + ۶ لاین selfimprove + bio-synthesis-daily عمداً **تاریک** ماندند (محافظ سهمیهٔ تعاملی Max).
- پروژهٔ نو: [[07 - Knowledge/Time-Architecture/PROJECT|Time-Architecture]] امروز (2026-07-06) به `07 - Knowledge` اضافه شد (ingest additive) — هنوز در جدول‌های [[05 - Agents/AGENT_REGISTRY|رجیستری]] ثبت نشده.
- 🆕 [[00 - Inbox/scout-digests/2026-07-06 synthesis|سنتز شبانهٔ 2026-07-06]] (consolidator، منبع ۹ دیجست + experience-review هفتگی #۳) سه خوشهٔ بین‌پروژه‌ای تازه یافت — فقط لینک/state، جزئیات در خودِ سنتز: (۱) همگراییِ ریسکِ زنجیرهٔ‌تأمینِ MCP (security+tools+ai-watch) — پیشنهاد L1 سخت‌سازیِ گارد، اقدامی نشد؛ (۲) امضایِ استاگفلیشنِ ماکرو (markets+world) — AUD ساختاری تحتِ فشار → اثر مستقیم روی هزینهٔ ریستاکِ [[03 - Projects/Mining/PROJECT|Mining]] و P&L دلاراستریلیاییِ [[03 - Projects/Crypto - etoro/PROJECT|Crypto]]؛ (۳) لایهٔ مقرراتیِ FY2026-27 — **Oneflare بسته شد (۳۰ ژوئن، ادغام در Airtasker)**، تمرکز بازار به‌نفعِ hipages → هر نوتِ کانالِ [[03 - Projects/Lead-نقاشی/PROJECT|Lead-نقاشی]] که Oneflare را زنده فرض کرده نیازِ پرچمِ اصلاح دارد (L0 گزارش، ویرایش نشد).

## 🔴 گلوگاه مشترک (مهم‌ترین اتصال بین‌پروژه‌ای)

**تناقض تازه دربارهٔ وضعیت Security Gate — نیاز فوری به رفع ابهام مالک:**
[[ROTATION_CHECKLIST]] هر ۴ ردیف CRITICAL (Monero seed · Bybit · OKX · کلیدهای Anthropic) را **ROTATED** نشان می‌دهد و [[04 - Architect System/architect/ARCHITECT_CHARTER|ARCHITECT_CHARTER]] §Security Gate صراحتاً می‌گوید «وضعیت فعلی (2026-07-05): گیت باز — هر ۴ CRITICAL rotate شد … verdict آری». اما جدیدترین ردیف‌های [[_memory/EXPERIENCE-LEDGER|EXPERIENCE-LEDGER]] (2026-07-06) و state حلقهٔ یادگیری هنوز فرض می‌کنند lift رسمی **معوق** است («ایجنت گیت خودش را برنمی‌دارد») و حتی `learning-engine/LEARNING-STATE.json` در خودش ناهم‌خوان است (`security_gate_status: OPEN` ولی `external_calls_unlock_conditions` هنوز «§Security Gate بسته» را شرط می‌شمارد). این drift اثر عملی دارد: اگر گیت واقعاً باز است، autonomy مؤثر [[03 - Projects/Lead-نقاشی/PROJECT|Lead]] · [[03 - Projects/Mining/PROJECT|Mining]] · [[03 - Projects/Crypto - etoro/PROJECT|Crypto]] · [[04 - Architect System/architect/PROJECT|architect]] دیگر read-only نیست؛ اگر نیست، چند سند سیستم دروغ می‌گویند. **تک منبع حقیقت باید charter باشد ولی این run فقط گزارش می‌دهد، تصمیم نمی‌گیرد** (بند ۱ دفتر تصمیم‌ها ↓). git هنوز init واقعی ندارد (تلاش سندباکس روی .git شکست خورد — کار Windows-side). ۱۹ ردیف غیر-CRITICAL (HIGH/MEDIUM) هنوز OPEN در همان چک‌لیست.

## پروژه‌ها (وضعیت زنده)

| پروژه | تمرکز فعلی | قدم بعد | تصمیم باز | سیگنال |
|---|---|---|---|---|
| [[03 - Projects/Lead-نقاشی/PROJECT\|Lead-نقاشی]] | rotation→ربات→آزمایش#۱ | ۵ کلید + `pytest` + `main.py` | کانال آزمایش#۱ (letterbox/آنلاین/ارجاع؟) | Google LSA در AU نیست→GBP+Ads · 🆕 Oneflare بسته (سنتز 07-06)، تمرکز به hipages |
| [[03 - Projects/Mining/PROJECT\|Mining]] | بازسازی پایه پیش از کوین بعد | چرخش کیف‌پول + رجیستری نودها | کدام نودها سالم‌اند؟ | chain-liveness پیش از ماین · 🆕 استاگفلیشن AUD ساختاری (سنتز 07-06) → هزینهٔ ریستاک بالا |
| [[03 - Projects/Crypto - etoro/PROJECT\|Crypto]] | رجیستری پوزیشن + exit_rules | ورود پوزیشن‌ها + exit_rules + rotation | اجرای خودکار یا alert-only؟ | استک free-API ~$0.01/ماه · 🆕 ضعفِ AUD ساختاری → سودِ P&L دلاراستریلیایی |
| [[03 - Projects/Accounting/PROJECT\|Accounting]] | tenant#1: رجیستر انطباق + حسابدار | ACN/ABN + حسابدار + تست ۱۰ رسید | نرم‌افزار؛ چرخهٔ BAS | ⚠️ instant write-off از 1Jul2026 = $1k |
| [[03 - Projects/Ziman Galerry/PROJECT\|Ziman]] | عدد ظرفیت از production owner | ثبت ظرفیت [Estimate] + چک‌لیست برند | کانال اول (IG محلی/مارکت‌پلیس؟) | تناقض ظرفیت (کد=۳۰ ↔ PROJECT ثبت‌نشده) |
| [[03 - Projects/اونلی فنز/PROJECT\|Project-F]] 🔒 | منتظر G0؛ بلوپرینت معماری آماده | Track B/C desk research (time-box ۱ هفته) | safe-expansion (Track): منجمد یا حذف؟ | STATE-REPORT + verification pass ثبت شد |
| [[07 - Knowledge/هیپنوتیزم  و خودآگاهی/PROJECT\|هیپنوتیزم]] | تفکیک معرفتی (تمرین/تئوری/داستان) | بازبینی [Assumption] + practice logs | O-04 (HRV فقط لپ‌تاپ)؛ n-of-1 | HRV-biofeedback شواهد peer-reviewed |
| [[07 - Knowledge/Time-Architecture/PROJECT\|Time-Architecture]] 🆕 | ثبت اولیهٔ corpus + ساختاردهی falsifiable | E1/L-test/¼-test (falsifiable) | offer مشخصِ money_link هنوز TBD | guard: RABBIT_HOLE_RISK + MONEY_LINK_TBD |
| [[04 - Architect System/architect/PROJECT\|architect]] | فاز۱ اجرا؛ وضعیت Security Gate مبهم (↑) | رفع ابهام گیت → git init → TOP-5 آدیت | ۶ دلتای v3 + منشور MYCOLEDGER-REBUILD (proposal) | MAST: شکست multi-agent ۴۱–۸۷٪ (P7/D-02) |

## دفتر تصمیم‌های باز (اقدام انسانی)

**سیستمی:** ۱) **رفع تناقض وضعیت Security Gate** — charter می‌گوید باز، ledger/learning-state می‌گویند lift معوق؛ کدام درست است + هماهنگ‌سازی `LEARNING-STATE.json` · ۲) **تکلیف نهاییِ `system-dashboard`**: حذف از جدول ۶‌تایی ratified یا احیای کامل + برداشتن بنر جانشین · ۳) 