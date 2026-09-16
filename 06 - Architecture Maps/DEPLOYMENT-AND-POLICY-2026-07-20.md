---
type: architecture
status: active
tags: [architecture, deployment, telegram, policy, safety, owner-gated]
created: 2026-07-20
updated: 2026-07-20
---

# T6 استقرار + معماریِ پروسه‌ی تلگرام · T7 شکاف‌های سیاست (Sol mission)

> سندِ **طراحی/سیاست**، نه اجرا. صفر تغییرِ launcher/watchdog/process/flag/STOP. تصمیم‌ها
> owner-gated می‌مانند. baseline `f2f500d`.

## T6-A · Deployment manifest — نگاشتِ commitِ canonical به هر launcher/watchdog
مشکلِ ریشه‌ای (ممیزیِ Sol، F-LAUNCHER-LIVE-TREE): کدِ canonical روی `f2f500d`
(`F:\octopus-integration` = master = germline) است، ولی همهٔ launcher/watchdogها به
درختِ **زنده**ی کهنه (`F:\backup` @ `a2183c3`) اشاره دارند که این کد را ندارد.

| مؤلفه | launcher/watchdog | مسیرِ فعلی | مشکل |
|---|---|---|---|
| organism (8771) | `RUN-ORGANISM.bat` / organism-watchdog | `F:\backup\_ops` | درختِ زنده = a2183c3 (فاقدِ کار) |
| cortex (8772) | `RUN-CORTEX.bat` | `F:\backup\_ops` | زنده (pid 8140) از همین‌جا |
| cockpit (8773) | `live/server.py` launcher | `F:\backup\_ops` | زنده (pid 9620) از همین‌جا |
| TG Center | `RUN-TG-CENTER.bat:11,16` + `tg-center-watchdog.ps1:19` | `F:\backup\_ops` | حتی اگر اجرا شود، center.pyِ کهنه را لانچ می‌کند |
| approval bot | thread داخلِ organism (`organism.py:263`) | تابعِ organism | با organism خاموش، DOWN |

**استقرارِ درست (owner-gated، رأیِ نهایی):** یا (الف) `F:\backup` را به master بیاور
(`git -C F:\backup merge --ff-only master` در پنجرهٔ organism-off) سپس restart؛ یا (ب)
launcherها را به درختِ canonical بازنشانی کن. **هیچ‌کدام این جلسه انجام نشد** (فریز).

## T6-B · معماریِ پروسه‌ی تلگرام — تصمیمِ طراحی (نه runtime)
دو گزینه:
- **الف) embedded (فعلی):** poll داخلِ organism (`organism.py:263`). سادگی، ولی **با
  خاموشیِ organism تلگرام هم می‌میرد** → مالک نمی‌تواند از تلگرام STOP/status بگیرد وقتی
  ارگانیسم خاموش است.
- **ب) gatewayِ مستقلِ supervised (پیشنهادِ Sol):** یک پروسهٔ جدا (مثلِ TG Center) که
  مستقل از organism زنده می‌ماند.

**ناوردیِ ایمنیِ مطلوب (رأیِ Sol، برای طراحیِ آینده):** تلگرام باید **STOP/status را
حتی با organismِ خاموش در دسترس نگه دارد**، ولی **هیچ اقتداری برای حذفِ STOP یا فعال‌سازیِ
اثرِ بیرونی نداشته باشد**. یعنی: gateway می‌تواند STOP بگذارد/وضعیت بدهد، ولی نه STOP بردارد
نه پول/ارسال فعال کند (آن‌ها رأیِ مستقلِ مالک). **این فقط تصمیمِ طراحی است؛ جابه‌جاییِ پروسه
این جلسه ممنوع (فریز).**

## T7 · شکاف‌های سیاست (تصمیمِ مالک لازم)
1. **`ps_writeback` = OUTWARD side-effect (F-PSWRITEBACK-OUTWARD).** تنها سطحِ پایی که به
   سیستمِ بیرونی (PocketSmith) می‌نویسد **بدونِ رأیِ per-item** — سه‌فلگ‌گیت، فقط `labels`.
   **سؤالِ مالک:** آیا هر نوشت رأیِ item-level بخواهد؟ (تا رأی نیامده، سیاست عوض نمی‌شود؛
   پیش‌فرض = flag-off می‌ماند.)
2. **گاردِ drawdownِ مالی = پیش‌نیازِ سختِ هر فعال‌سازیِ پول (F-DRAWDOWN-ABSENT).** روی
   master غایب؛ برنچِ منبع un-mergeable (۳.۷M حذف). re-implementِ تازه لازم است، ولی
   **آستانهٔ spike = سیاستِ مالیِ مالک**. هیچ مسیرِ پولی نباید بدونِ این فعال شود.
3. **`human_append_guard` پیش‌فرض fail-OPEN (F-HUMANGUARD-FAILOPEN).** یکپارچگیِ رأیِ
   انسانی روی `unified_bus.publish` تا `HH_HUMAN_GUARD_STRICT=1` نباشد enforce نمی‌شود.
   **آیتمِ تصمیمِ امنیتی:** آیا strict پیش‌فرض شود؟ (تغییرِ رفتار → رأیِ مالک.)

## آنچه Sol T1–T5 این جلسه بست (روی canonical، flag-off، تست‌دار)
- T0 evidence manifest · T1 Menu v2 reachable · T2 verdict→durable outcome · T3 fence
  bypass-guard · T4 spine دو-دامنه · T5 تصحیحِ کامنتِ ziman_biology.
- **staged (owner-gated):** wiring.py decompose · Mutation Chamber · fencedکردنِ per-callerِ
  bypassهای `.complete` · گسترشِ spine به accounting/ziman/doctor · re-implementِ drawdown ·
  استقرار/فعال‌سازی (حذف STOP + restart).

مرجع‌ها: `06 - Architecture Maps/EVIDENCE-MANIFEST-2026-07-20.json` · [[UNIFICATION-SPINE-STATUS-2026-07-20]]
