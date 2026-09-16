---
type: evidence
task: C-047
tags: [incident, organism-gap, restart, marker, directive-10]
created: 2026-08-20T16:00+10:00
created_by: agent B (ZCode) — lease 4cc7c79f
severity: high (availability) · crashes: 0 · availability_incidents: 1
---

# INCIDENT — شکاف ~۴ دقیقه‌ای organism در ریاستارت مارکری (2026-08-20)

## خط زمانی (همه +10:00 محلی)

| زمان | رخداد | شاهد |
|---|---|---|
| 14:32:53 | baseline ریاستارت ثبت شد (beat 42940, PID 7096, spine_rows 7266) | `_ops/state/pulse/restart-baseline-t49.json` |
| ~14:33 | مارکرهای STOP-ORGANISM + RESTART-REQUESTED ساخته شد (توسط همین پروتکل) | لاگ جلسه |
| ~14:33–34 | organism با خروج تمیز HALT(STOP) بست (marker check ابتدای تیک) | organism.py:531-537 |
| 14:33–14:36 | **شکاف — organism پایین**؛ supervisor واقعی (cmd از ۱۱:۴۷، `cmd /c RUN-ORGANISM.bat`) همراه فرزند خارج شده بود و هیچ‌کس مارکرها را پاک/relaunch نکرد | اسکن‌های دوره‌ای جلسه (PID خالی، STOP-present) |
| 14:36:09 | relaunch دستی: مارکرهای خود پاک شد + `RUN-ORGANISM.bat` (همان مسیر watchdog) Start-Process شد → PID جدید 19736 | لاگ جلسه؛ CreationDate پروسه |
| 14:36:17 | بوت جدید؛ beat از 42942 ادامه یافت | ORGANISM-STATE / بریفینگ |
| بعد از 14:45 | همهٔ اسکن‌های نگهبان OK؛ beat جلو می‌رود؛ memread OK | OCTOPUS-WATCH-2026-08-20.md |

- beat قبل: 42940 · بعد: 42942 (دو beat در پنجرهٔ بوت).
- **kill-switch مالک نبود:** پیش از ساخت مارکرها organism زنده و می‌تپید (PID 7096
  در STATE-RECHECK ثبت شده)؛ STOP-ORGANISM ساختهٔ همین پروتکل بود و پاک‌شدنش
  نقض حریم مالک نیست (launcher طبق P2 هرگز STOP مالک را پاک نمی‌کند — درست).
- crashes = 0 (خروج تمیز، نه crash)؛ **availability_incidents = 1** — این دو از
  اینجا جدا گزارش می‌شوند تا ادعای «بدون اختلال» ساخته نشود (دستور #۱۰ §۱).

## ریشه

مسیر ریاستارت مارکری (STOP+RESTART-REQUESTED ← پاک‌سازی و loop دوبارهٔ bat)
فرض می‌کرد instance فعلی زیر حلقهٔ `:loop` همین bat است. نمونهٔ ۱۱:۴۷ با
`cmd /c` (یک‌باراجرا) بالا آمده بود → بعد از خروج python، cmd هم تمام شد.

## پروتکل اصلاح‌شده C-047 (از این پس الزامی)

```text
پیش از هر ریاستارت مارکری:
  ۱) parent PID پروسهٔ organism را بگیر (Win32_Process.ParentProcessId)
  ۲) parent باید زنده باشد و command-line آن RUN-ORGANISM.bat باشد
     (حلقهٔ :loop — نه cmd /c یک‌باره)
  ۳) نبود/مبهم → ABORT ریاستارت؛ فقط ثبت و اطلاع مالک
  ۴) پس از ریاستارت: ظرف ≤۹۰ ثانیه PID جدید + پورت 8771 + beat جلو رونده
     احراز شود؛ وگرنه CRITICAL و بازیافت دست مالک
```

## سرپرست‌های شناخته‌شده (مستندسازی §۱)

| پروسه | سرپرست | روش راه‌اندازی | بازیافت |
|---|---|---|---|
| organism.py | `cmd /c ""F:\backup\_ops\RUN-ORGANISM.bat"` (حلقهٔ :loop، هر ۱۰s) | Start-Process RUN-ORGANISM.bat | خودِ bat + watchdog (پورت 8771، ۵ دقیقه‌ای) |
| brain.daemon | `cmd /c outputs\launch5.cmd` (یک‌باراجرا + append به `4d_system/outputs/daemon-launch5.err.log`) | دستی/سکشن 4d | **نامشخص** — تا بسته‌شدن C-047 ریاستارت ممنوع (دستور #۱۰ §۳)؛ فایل launch5.cmd فاقد حلقه است |

## الحاقیه — شکاف دوم و ریشهٔ نهایی (همان روز، ~15:06–15:08)

حین اجرای ریاستارتِ «اصلاح‌شده»، همان خطا تکرار شد (این بار ~۱۰۰ ثانیه):
**ریشهٔ نهایی:** کامنت سرِ RUN-ORGANISM.bat پروتکل قدیمی «STOP+RESTART هر دو
پاک می‌شوند» را توصیف می‌کند؛ ولی کد P2 فقط RESTART-REQUESTED را پاک می‌کند
و اگر STOP موجود باشد به `:stopped` می‌رود و launcher برای همیشه تمام می‌شود.
**پروتکل صحیح ریاستارت مارکری = فقط RESTART-REQUESTED** (organism همان‌جا
clean-exit می‌کند؛ launcher مارکر را پاک و loop می‌کند).
اقدام اصلاحی باقی‌مانده (پیشنهاد): کامنت سرِ فایل bat + هر کد داشبورد/کاکپیت
که هنوز جفت‌مارکر می‌سازد باید تصحیح شود (فایل داغ — دست مالک).
availability_incidents امروز = 2 (هر دو همین ریشه) · crashes = 0.
