---
type: report
status: done
tags: [architecture, cowork, agents, skills, strategy]
created: 2026-07-06
updated: 2026-07-06
language: persian
---

# 🎛 استراتژی Master Project — Cowork روی «مغز دوم»

> پاسخ ساخت‌یافته به پرامپت «Nexus Architect 2027» آری — با یک تفاوت صادقانه: هیچ قابلیت خیالی فرض نشده. هر جزءِ خواسته‌شده به primitive **واقعیِ** همین محیط Cowork و همین vault نگاشت شده است. سند لینک می‌دهد، کپی نمی‌کند.

## ۱) نگاشت لایه‌های «Nexus» به واقعیت

| لایهٔ خواسته‌شده | primitive واقعی | محل/قرارداد |
|---|---|---|
| Perfect memory | vault + پروتکل جلسه | [[01 - Dashboard/HANDOFF\|HANDOFF]] (حافظهٔ کاری) · PROJECT.md هر پروژه (per-project) · [[_memory/EXPERIENCE-LEDGER\|ledger]] (درس‌ها، append-only) · [[05 - Agents/RATIFIED-TASKS\|RATIFIED-TASKS]] (تک‌منبع بازسازی ناوگان) |
| Multi-agent team | Agent tool (subagent) | Explore = جستجوی موازی read-only · Plan = معمار · general-purpose = اجرای چندگامی · اجرای موازی = چند subagent در یک پیام |
| Plugins/Tools | skillها + MCPها | skillهای لوکال (docx/pptx/xlsx/pdf، engineering:*، skill-creator، schedule…) همیشه کار می‌کنند؛ MCPهای marketplace فقط بعد از اتصال/auth توسط آری وجود دارند |
| Artifacts | live artifact های Cowork | کاک‌پیت واحد `second-brain-master-cockpit` (جلسه ۱۸) — گسترش همان، نه ساخت آرتیفکت نو |
| Runtime دائمی | scheduled tasks | زمان‌بند الان **۰ تسک فعال** (verdict خاموشی کامل، جلسه ۱۷) — هر روشن‌کردنی verdict آری می‌خواهد |
| Self-improving loop | ledger + experience-review + skill-creator | §۵ همین سند |

## ۲) ماتریس انتخاب ابزار (کار ← ابزار)

| نوع کار | ابزار اول | قاعده |
|---|---|---|
| جستجوی گستردهٔ vault | Explore subagent | چند پرسش هم‌زمان؛ خروجی «نتیجه» است نه dump فایل‌ها |
| تصمیم/طرح معماری | Plan subagent یا skill ‏engineering:architecture | خروجی = spec/ADR در Inbox؛ اجرا جدا و بعد از verdict |
| کدنویسی چندفایلی | فازبندی با تأیید (الگوی موفق جلسه ۱۸) | هر فاز: build ← test ← گزارش ← verdict |
| بازبینی کد | skill ‏engineering:code-review | قبل از commit ویندوزی |
| دیباگ | skill ‏engineering:debug | با traceback و reproduce شروع کن |
| تحقیق وب | WebSearch؛ tavily/exa اگر متصل شد | سنتز با sources به Inbox، طبق درخت تصمیم قانون اساسی |
| سند تحویلی (docx/pptx/xlsx/pdf) | skill هم‌نام | فقط **بعد** از اتمام تحقیق/محتوا |
| داشبورد/نمای زنده | live artifact | اول ابزار را در چت probe کن، بعد بساز |
| کار تکرارشونده (بریف روزانه…) | scheduled task | فقط با verdict آری + یک‌بار «Run now» برای pre-approve ابزارها |

## ۳) زنجیرهٔ استاندارد هر مأموریت

خواندن HANDOFF/PROJECT.md ← تحقیق (Explore/وب) ← طرح (Plan + verdict آری) ← ساخت فازبندی‌شده با تست هر فاز ← وریفای (code-review + validatorها) ← ثبت (PROJECT.md لمس‌شده + HANDOFF + ledger).

قاعدهٔ طلایی: **هیچ «ساخت»ی بدون گام «ثبت» تمام نیست** — حافظهٔ بین‌جلسه‌ای دقیقاً همین است، نه چیز جادویی.

## ۴) قواعد سخت محیط (خلاصه — مرجع کامل: [[_PROJECT_INSTRUCTIONS|قانون اساسی]])

- git از سندباکس فقط read؛ commit ویندوزی یا الگوی tmp←copy←verify (درس جلسه ۱۷).
- فایلِ همین‌جلسه ویندوز-ویرایش‌شده را از مانت سندباکس اجرا/verify نکن (**stale-view**) — وریفای با Read مستقیم یا snippet-compile در fs داخلی سندباکس (الگوی جلسه ۱۹).
- `.agentignore` مطلق است؛ secret هرگز در چت/نوت/HANDOFF/لاگ.
- دیتای Project-F هرگز به Fugu نمی‌رود (گارد privacy، فاز ۴ v2).
- MCP بدون auth = ناموجود فرض شود؛ اتصال به تصمیم آری و به‌قدر نیاز — **اقتصاد کانتکست:** هر پلاگین/اسکیل اضافه یعنی کانتکست کم‌تر برای کار واقعی؛ مجموعهٔ نصب‌شدهٔ فعلی کاندید هرس است.
- Inbox-اول برای هر خروجی نو؛ نام‌گذاری ماشینی `YYYY-MM-DD HHmm slug`.

## ۵) حلقهٔ خودبهبودی (عملی، نه شعاری)

۱. هر درس/regress حین کار ← append به [[_memory/EXPERIENCE-LEDGER|ledger]].
۲. الگوی ۳+ بار تکرارشده ← تبدیل به skill شخصی با skill-creator. سه کاندید آماده از همین تاریخچه: «وریفای ضد-stale-view»، «پروتکل پایان جلسه (HANDOFF+PROJECT+validator)»، «فازبندی build-test-verdict».
۳. مرور هفتگی experience-review (الان خاموش) pendingها را برای verdict می‌آورد — بازگشتش تصمیم آری است.

## ۶) verdictهای باز برای آری

۱. اتصال MCPها: پیشنهاد فعلاً هیچ — skillهای لوکال + WebSearch کفایت می‌کنند؛ اولین کاندید واقعی بعداً: جستجوی قوی‌تر (tavily/exa).
۲. بازگشت حداقلی زمان‌بند: فقط `perception-refresh` یا همچنان صفر؟
۳. کدام‌یک از ۳ skill شخصی §۵ اول ساخته شود؟
۴. جای دائمی این سند: ماندن در Inbox یا انتقال به `04 - Architect System`؟

## منابع

[[_PROJECT_INSTRUCTIONS]] · [[01 - Dashboard/HANDOFF]] · [[04 - Architect System/MYCELIAL-MASTER-SPEC]] · [[00 - Inbox/ARCHITECTURE-PATTERNS-DEEP-V2-2026-07-06]] · [[_memory/TWO-BRAIN-CONTROL-BLUEPRINT]] · [[_memory/EXPERIENCE-LEDGER]]
