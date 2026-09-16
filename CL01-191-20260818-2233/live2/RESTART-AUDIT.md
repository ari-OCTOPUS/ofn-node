# RESTART AUDIT — 4D-RESTART-ONE-SHOT (2026-08-18، بدون تغییر رترواکتیو)
launch_attempt_1:
  time: 2026-08-18 ~23:07 +10:00
  command: python -X utf8 brain/daemon.py (از 4d_system، env enforcement=1)
  result: ModuleNotFoundError 'brain' — خطای فراخوانی اپراتور (باید -m بود)
  ticks: 0 · side_effects: 0 · state_touched: NONE — دیمون هرگز شروع نشد
  log: 4d_system/outputs/daemon-launch4.log/.err.log (315B traceback)
launch_attempt_2:
  time: 2026-08-18 23:08 +10:00
  command: python -X utf8 -m brain.daemon (اصلاح‌شده، همان env، همان cwd)
  result: SUCCESS — PID 18020 · preflight هر۴شرط PASS · صفر protective HALT
  interpretation: مصرفِ همان restartِ مجازِ واحد؛ تلاش۱ دیمنِ مصرف‌نشده بود (import-dead)
  log: daemon-launch4b.err.log
تاریخچه عیناً حفظ شد؛ این سند صرفاً ثبت صریح همان واقعیت‌هاست.
