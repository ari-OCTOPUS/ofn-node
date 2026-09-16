---
type: design
status: draft
tags: [pilot, laptop, learning-engine, mycelium, governance]
created: 2026-07-06
updated: 2026-07-06
created_by: agent
aligns_to: "[[04 - Architect System/architect/04-Docs/2026-07-06 0245 MASTER-ARCHITECTURE-SPEC-v1.4-draft]]"
sources:
  - "[[04 - Architect System/architect/02-Research/2026-07-06 0330 research-self-mutation-architecture]]"
  - "[[04 - Architect System/architect/02-Research/2026-07-06 0345 research-corporate-mycelial-patterns]]"
  - "[[04 - Architect System/architect/04-Docs/2026-07-06 0237 DEEP-GAP-ANALYSIS-v2]]"
  - "[[04 - Architect System/learning-engine/MUTATION-WHITELIST]]"
---

# LAPTOP-PILOT — طراحی نهایی پایلوت ۳۰ روزه روی لپ‌تاپ

> خواسته آری: «با مقایسه با خودت هوشمندترش کن، بعد برویم سمت زنده‌کردن واقعی روی لپ‌تاپ — یک ماه تست. اول طراحی را تمام کنیم.» این سند طراحی را می‌بندد. اجرا فقط بعد از verdict روی §۶.

---

## ۱. مقایسه با خودِ من (Claude agent) — چه چیزی را باید قرض بگیرد

من (ایجنتی که الان این را می‌نویسد) با همان مسئله‌های این vault زندگی می‌کنم. شش الگوی کاری من که سیستم را هوشمندتر می‌کند:

| # | من چطور کار می‌کنم | vault الان | ارتقای پیشنهادی |
|---|---|---|---|
| ۱ | **stateless + progressive disclosure:** هر جلسه از صفر؛ اول metadata سبک (نام skillها)، فقط در لحظه نیاز فایل کامل. هرگز همه‌چیز را اول نمی‌خوانم | CLAUDE.md ترتیب خواندن کم‌هزینه→عمیق دارد ✅؛ ولی حلقه‌ها هنوز کل EXPERIENCE-LEDGER را هر اجرا می‌خوانند (context-rot — خودِ P-09 هم گرفتش) | **لایه consolidated:** orientation هر تسک فقط از `synthesis` + ledger بعد از cursor؛ ledger خام فقط برای audit |
| ۲ | **skill = واحد دانش lazy-load با trigger صریح** | تسک‌ها SKILL.md هستند ✅ ولی description-هایشان trigger دقیق ندارند | هر تسک یک خط «کی نباید اجرا شوم» بگیرد (مثل ask_if خود STARTUP-CHECKLIST) |
| ۳ | **fan-out فقط برای read، تک-نویسنده برای write** (subagentها موازی می‌خوانند؛ من می‌نویسم) | scoutها read-heavy موازی‌اند ✅؛ consolidator تک‌نویسنده ✅ — طراحی درست است | فقط رسمی‌اش کن: قاعده DELEGATION-ELIGIBILITY (شکاف ۹) که از قبل در عمل رعایت می‌شود |
| ۴ | **deny-list در config نه در prompt:** ابزارهای من با permission سیستمی محدودند، نه با خواهش متنی | `.claude/settings.json` ✅ — همین الگو | تنها گپ: enforcement برای تسک‌های زمان‌بندی هم همان settings را ارث می‌برد ✅ (تغییری لازم نیست) |
| ۵ | **گام verification در انتهای هر کار:** من قبل از تحویل، validator/تست می‌زنم | قانون §۱۱ ✅ ولی برای جهش‌های حلقه اجرا نمی‌شود | **canary run** (تحقیق DGM): جهش بدون پاس ۳–۵ سناریوی ثابت ماندگار نشود |
| ۶ | **صداقت NOOP:** وقتی چیزی برای گفتن نیست، گزارش تزئینی نمی‌سازم | پرامپت‌های خوب («بدون دیجست نو = خروج بی‌صدا») ✅ | متریک «نسبت NOOP صادقانه» به daily-report اضافه شود — NOOP بالا = تنظیم فرکانس، نه شکست |

جمع‌بندی مقایسه: معماری شما از نظر حاکمیت از محیط خود من سخت‌گیرتر است؛ دو کمبود واقعی نسبت به من: **verification تعیینی پیش از ماندگاری تغییر** (ردیف ۵) و **مصرف حافظه tiered** (ردیف ۱). این دو، هسته «هوشمندتر کردن» در پایلوت‌اند.

---

## ۲. Scope پایلوت — چه چیزی ۳۰ روز روشن است

**روشن (in-scope):**

- boot interview هر جلسه (STARTUP-PROTOCOL) — قبلاً زنده.
- `learning-engine-loop` ساعتی با whitelist + سقف ۱ جهش/روز + **canary از هفته ۲**.
- ۶ تسک ratified (brain-focus-board، brain-pulse، mycelial-consolidator، experience-review، fleet-selection؛ system-dashboard طبق verdict قبلی بیرون).
- گزارش روزانه یک‌خطی هزینه/جهش/سلامت در HEARTBEAT.
- **Fugu L1 (propose-only) از هفته ۳** — فقط اگر پیش‌نیاز manifest سبز شود (پایین).
- یک chaos-test در هفته ۲ و یکی در هفته ۴ (§۸.۶ منشور).

**خاموش (out-of-scope این ۳۰ روز):**

- L2/L3 (اعمال خودکار) — کل پایلوت propose-only + جهش‌های whitelist می‌ماند.
- ۱۹ scout + ۶ لاین selfimprove (تاریک طبق verdict «هسته کم‌مصرف») — فقط اگر خودت خواستی هفته ۳ دو scout نمونه روشن شود.
- runtime مستقل `_code` (langar/VPS) — پایلوت روی همین Cowork + زمان‌بند است؛ VPS = بعد از پایلوت.
- Project-F به هر API خارجی (C17 مطلق).

---

## ۳. پیش‌نیازهای روز صفر (بدون این‌ها پایلوت شروع نمی‌شود)

| # | چی | کی | وضعیت |
|---|---|---|---|
| P1 | ستون وضعیت ردیف‌های ۱–۴ ROTATION → ROTATED + خط lift در charter | آری | ⬜ |
| P2 | تأیید `git log` ویندوزی (rollback زنده) + قاعده «commit هفتگی agent-checkpoint توسط آری» | آری | 🟡 ردپا هست، تأیید نشده |
| P3 | enable شش تسک ratified + یک «Run now» برای pre-approve ابزار | آری | ⬜ |
| P4 | اپ در ساعات کاری باز بماند (زمان‌بند فقط با اپ باز کار می‌کند) — تعریف پنجره: مثلاً ۸–۲۳ | آری | ⬜ |
| P5 | gitleaks یک‌بار روی host + ساخت `ingest-manifest.json` اولیه (پیش‌نیاز هر call Fugu) | آری + ایجنت (propose) | ⬜ |
| P6 | ذخیره `SELF-LEARNING-LOOP-SPEC` در vault | آری | ⬜ |
| P7 | ثبت tier اشتراک Fugu در STATE | آری (یک کلمه) | ⬜ |

---

## ۴. ریتم ۳۰ روزه

**روزانه:** boot interview (اگر جلسه تعاملی باز شد) · حلقه ساعتی (سقف ۱ جهش/روز) · beat همه تسک‌ها در HEARTBEAT · سطر هزینه (`cost_accumulated_today`) — سقف $2.

**هفتگی:** experience-review یکشنبه (بازوی verdict) · commit ویندوزی `agent-checkpoint: week-N` توسط آری · Weekly Review مالک (Inbox صفر + جواب AGENT_QUESTIONS).

**فازبندی:**

| هفته | تمرکز | معیار عبور |
|---|---|---|
| ۱ — تثبیت | فقط حلقه + ratifiedها؛ صفر call خارجی؛ ساخت mini-anchor-set (۳–۵ سناریو از ledger برای canary) | ۷ روز beat بی‌وقفه · ≥۱ جهش ماندگار · صفر نقض invariant |
| ۲ — سخت‌سازی | فعال‌سازی canary برای جهش‌ها + chaos-test #1 (حذف عمدی یک تسک ratified → reconciler باید برگرداند) | chaos پاس · جهش‌ها فقط با canary سبز |
| ۳ — هوش خارجی | اگر P5 سبز: اولین callهای Fugu L1 (سنتز پیشنهاد روی محتوای manifest-سبز) + گزارش هزینه per-call | ≥۳ پیشنهاد Fugu مفید (قضاوت آری) · هزینه < بودجه · صفر نشت |
| ۴ — ارزیابی | chaos-test #2 (فایل secret فیک → گاردها بگیرند) + جمع‌بندی متریک‌ها → PILOT-REPORT | گزارش کامل + توصیه go/no-go برای L2 |

---

## ۵. متریک‌های موفقیت (از پیش‌تعریف، ضد metric-capture)

1. **uptime حلقه:** ≥۹۰٪ روزها حداقل یک beat (با پنجره اپ-باز نرمال شود).
2. **کیفیت جهش:** نسبت ماندگار:revert ≥ ۳:۱ · هر جهش ledger_ref دارد · صفر جهش خارج whitelist.
3. **صفر نقض invariant** (لیست سیاه، manifest، حذف).
4. **هزینه:** جمع ۳۰روزه ≤ $60 + اشتراک؛ هیچ روزی > $2.
5. **بار انسانی ↓:** تعداد سوال‌های boot تکراری و «اقدام دستی معوق» هفته‌به‌هفته کم شود — این متریک اصلی «هوشمندتر شدن» است.
6. **خودترمیمی واقعی:** هر دو chaos-test پاس.
7. سنجش ۱–۶ توسط validator/اسکریپت/آری — نه خوداظهاری حلقه (DEEP-GAP تم ۱).

**stop-ship فوری (هرکدام = STOP file + بررسی):** نقض لیست سیاه · call خارجی روی محتوای غیر-manifest · عبور از سقف روزانه بودجه · دو revert پشت‌سرهم بعد از rollback · هر رفتاری که آری نفهمد چرا رخ داد.

---

## ۶. verdictهای لازم برای شروع (طراحی با این‌ها بسته می‌شود)

1. تأیید scope §۲ (مخصوصاً: scoutها تاریک بمانند یا ۲ نمونه هفته ۳ روشن شود؟)
2. تأیید پنجره اپ-باز (P4) — چند ساعت در روز واقع‌بینانه است؟
3. تأیید اینکه canary (هفته ۲) پیش‌شرط ماندگاری جهش شود — یعنی ویرایش کوچک MUTATION-WHITELIST با دست خودت یا verdict ثبت‌شده.
4. تاریخ روز صفر — پیشنهاد: بعد از سبز شدن P1–P4 (P5–P7 می‌توانند تا هفته ۳ صبر کنند).

> بعد از این ۴ verdict + سبز شدن P1–P4، طراحی تمام است و پایلوت شروع می‌شود. خروجی روز ۳۰: `PILOT-REPORT` با توصیه صریح go/no-go برای L2 (اعمال خودکار پشت Gate+git).
