# 12_Architecture — نسخه‌یِ کاملِ Architecture.md

محتوایِ کاملِ معماری‌ها (SERVER_ARCHITECTURE، fusion-mvp، Brushline/AiFarm-Lead، infra-control، LANGAR، Silabi-Bot) در فایلِ ریشه `Architecture.md` آمده تا محتوا دوبار نوشته نشود. این‌جا فقط یک تحلیلِ اضافه:

## مقایسه‌یِ عمقِ منبع (شفافیتِ لازم)

| پروژه | نوعِ منبع | می‌توان به جزئیاتش اعتماد کرد؟ |
|---|---|---|
| SERVER_ARCHITECTURE.md | اول‌دست، کامل | بله، ولی احتمالاً **کهنه** نسبت به infra-control واقعی |
| Silabi-Bot | اول‌دست، کامل (کد) | بله، مستقیماً کد دیده شد (و باگ هم پیدا شد) |
| fusion-mvp | دایجستِ فشرده | فقط در حدِ معماریِ کلی؛ جزئیاتِ کد در دسترس نیست |
| Brushline/AiFarm-Lead | دایجستِ فشرده | فقط در حدِ نامِ اجزا و وضعیتِ فاز |
| infra-control | دایجستِ فشرده | فقط تصمیمِ VPS مشخص است |
| LANGAR | دایجستِ فشرده (یک‌خط) | حداقلِ اطمینان از کلِ این پایگاه‌دانش |

## یک الگویِ معماریِ تکرارشونده که در `Architecture.md` نیامد: «هر پروژه یک root-control یا orchestrator دارد»

Silabi-Bot ندارد (تک‌فایل، بدونِ orchestrator) — این خودش قابلِ‌توجه است: تنها پروژه‌ای که این الگو را ندارد، تنها پروژه‌ای است که تک‌کاربره، بدونِ auto-execution، و بدونِ ریسکِ مالی/داده‌ایِ جدی است. یعنی نبودِ orchestrator احتمالاً **آگاهانه** است (over-engineering برایِ یک رباتِ شخصیِ کوچک)، نه یک نقص — سازگار با تصمیمِ صریحِ fusion-mvp دربارهِ IGK-as-kernel-process («فقط اگر threat model عوض شود»).

**اولویت:** هماهنگ‌سازیِ SERVER_ARCHITECTURE.md با وضعیتِ واقعیِ infra-control (`TODO.md` #۱۰).
