---
type: evidence
task: directive-11
tags: [allowlist, c047-fix, flip-gate, phase2-card, t54, directive-11]
created: 2026-08-20T16:30+10:00
created_by: agent B (ZCode) — lease 62d056a9
paid_calls: 0/0 · executable_true_unexpected: 0 · GAP-001: OPEN
---

# گزارش دستور مالک #۱۱ — ایجنت B

```text
EXECUTABLE ALLOWLIST : DONE · allowlisted=5 · unexpected=0 ✓
                       (_ops/safety/EXECUTABLE-ALLOWLIST.md + دو تست AST-محور سبز
                       — اسکنر AST است، پس docstringها هرگز سایت حساب نمی‌شوند)
C-047                : CLOSED_WITH_FIX ✓
                       کامنت bat → پروتکل تک‌مارکری (فقط RESTART-REQUESTED)؛
                       منطق اجرایی launcher دست‌نخورده؛
                       preflight بلند در organism: restart+STOP ⇒
                       ABORT_RESTART_STOP_PRESENT + رویداد spine governance؛
                       تست ۵/۵ (منطق + رشتهٔ preflight + متن bat).
T54 CLOCK PRECISION  : precision=1s (در کد producer از امروز) ·
                       skew_median=n/a · skew_n=0 (هنوز هیچ رویداد server_created —
                       daemon کد قدیم، organism منتظر اولین فراخوان روتر)
                       semantics created: UNKNOWN (دریافت درخواست یا پایان تولید؟) —
                       حدس نزده شد؛ پروب تعریف شد: با اولین رویدادها، فاصلهٔ
                       created−request_ts در برابر created−receipt_ts مقایسه و
                       کوتاه‌ترین، معنا را تعیین و مستند می‌کند.
PRODUCER_2           : n=0 (معلق به پیام‌های تلگرامی شما — §۷-۲)
SERVER_CREATED       : first_event=— · n=0
LIVE-B               : BLOCKED (طبق تأیید خودتان؛ سه شرط صدور از گزارش #۱۰ پابرجاست)
FLIP-RATE GATE       : added_to_cards=2 ✓
                       (PRE-REG-ABLATION §۴ + PRE-REG-FULL-LOOP-FLASH yaml)
PHASE2 CARD          : AWAITING_SIGNATURE ✓
                       (02-DECISIONS/PRE-REG-JUDGE-BIAS-PHASE2-2026-08-20.md —
                       متن دقیق کارت شما + مبنای هزینه از T35 + رأی‌نامه)
availability_incidents: 0 جدید (امروز مجموع ۲ — هر دو ریشهٔ C-047 که الان بسته شد)
paid calls / AUD     : 0 / 0 · crashes: 0
lease held           : 62d056a9 ✓ (در پایان گزارش آزاد می‌شود)
GAP-001              : OPEN
commit / branch      : commit همین گزارش · equip/g10-cognition-20260816
```

## یادداشت فنی T54 (دستور §۵)

- `time_precision` مسیر `provider_server_created` از ابتدای پیاده‌سازی T52
  برابر `1s` ثبت شده بود (کد امروز) — مطابق تصحیح شما ✓.
- گیت LIVE-B بازنویسی شد تا معیار «کدام ساعت؟» مقدم بر «چه پراکندگی؟» باشد:
  `independent_external_clock_sources >= 1` (تلگرام یا server_created) و
  `delay_bearing_sources >= 2` — stdev صرفاً گزارشی است.
- تلگرام: دقت ۱s ⇒ برای late-arriving واقعی، پیام‌ها با فاصلهٔ چند دقیقه‌ای
  لازم است (به §۷-۲ شماضافه شد در نامهٔ سؤالات).

## سه جملهٔ پایانی

مهم‌ترین فهم امروز: سه «تخفیف به‌ظاهر-قاعده» امروز در واقع تصحیح قاعده بودند —
allowlist رفلکس محافظ، گیت flip-rate، و تک‌مارکری شدن ریاستارت؛ هر سه از
جنس «قاعدهٔ بد-نوشته را درست بنویس» نه «مرز را پایین بیاور». مهم‌ترین
ندانسته: معنای واقعی فیلد `created` (دریافت درخواست یا پایان تولید پاسخ) —
تا اولین رویدادها نیایند قابل تعیین نیست و تعیینش بر تفسیر skew اثر
مستقیم دارد. خطرناک‌ترین باور فعلی: «کارت فاز ۲ با ۴۸۰ فراخوان، تصویر کامل
سوگیری داور می‌دهد» — با دو داور هم‌خانواده و بدون برچسب طلایی، خروجی
confounder-دار است؛ ارزش اصلی فاز ۲ فقط با برچسب‌گذاری شما (§۷-۵) کامل می‌شود.
