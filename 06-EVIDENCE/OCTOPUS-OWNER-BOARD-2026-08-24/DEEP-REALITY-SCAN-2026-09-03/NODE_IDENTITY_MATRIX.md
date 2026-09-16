# NODE_IDENTITY_MATRIX — 2026-09-03 07:22-07:55 UTC

## laptop — DESKTOP-KA9RFN5 (درایو F:)
- OS: Windows 10.0.26200 (26200.0) · TZ: AUS Eastern · time 17:22:34+10:00 · NTP: time.windows.com، آخرین سینک 13:47 همان روز (سالم)
- ران‌تایم زنده (پورت‌های 8771-8777، همه python 3.13):
  | پورت | pid | cmdline (نسبی!) | parent | شروع |
  |---|---|---|---|---|
  | 8771+8777 | 22936 | `python -X utf8 organism.py` | 17764 | 09:22 |
  | 8772 | 22584 | `cortex\cortex.py` | 13268 | 09:19 |
  | 8773 | 11992 | `live\server.py` | 11388 | 09:13 |
  | 8774 | 19176 | `F:\backup\_ops\telegram_center\miniapp_gateway.py` (absolute!) | 16408 | 09:18 |
  | 8776 | 25636 | `telegram_center\center.py` | 28216 | 16:32 |
- **cwd هر پنج پروسه ثبت نشد (محدودیت ابزار)؛ سه‌تای آنها مسیر نسبی می‌گیرند → وابسته به CWD راه‌انداز = ریسک PATH_MISMATCH.** شاهد غیرمستقیم: memory پرسشنشست «ارگانیسم والت از F:\backup\_ops».
- git: ofn-node=fix/demand-harvest@34e63a0 dirty=33 · F:\backup=rescue/octopus-live-tree-20260821@8d8be71 **dirty=400** · دو worktree لین تمیز.
- orphan-watchdog: state/orphan-watchdog/receipts.jsonl زنده (ts امروز)؛ restarts=0.

## board138 — DietPi (Sydney)
- time 07:23:37 UTC · **NTPSynchronized=yes**
- تایمرها (۱۰): budget-monitor(3min)·imap(8)·quote(23)·scheduler(8)·absence·doctor·heartbeat·mesh-drain·selfmodel·witness(هر چهار 23min تا نوبت 08:00Z) — همه ACTIVE.
- پورت‌ها: 127.0.0.1:8791-8794 (یک python3 pid 2574033) · 8796 (pid 589802). **بدون 8090/8081/4222.**
- git ~/ofn: main@60dce961، dirty=5.
- ~/octopus-mesh: outbox=0 · inbox=0 · **state=15** (صف retry) + receipts/rejected/rollback/snapshots.
- sqlite: outbox=111 · ledger=210 · painting_quotes=1. inbox جدول marketing_inbox (شمارش این پاس در نیامد — فرمان جدول-متغیر غلط بود؛ UNVERIFIED این بار).
- journalctl برای ari فقط پیام‌های خودش را می‌بیند («Users in groups adm/systemd-journal…») → رسید تایمرها فقط از list-timers/فایل‌ها.

## node182 (sensorium-opi5pro) — از لپ‌تاپ UNVERIFIED
- ssh: `Permission denied (publickey)` — کلیدی از این نود نداریم. داده‌ها فقط از رسیدهای نشست موازی (MISSING-WIRING-50 + mesh quickref): NATS 4222 روی LAN، outbox شاهد دیروز 21/21 درین شد، ۴ بدهی عملیاتی (miniscientist failed، world-model hang، 52% RAM، events.jsonl 29MB).

## node180 (octopus-continuity-180) — از لپ‌تاپ UNVERIFIED
- ssh: `Permission denied`. رسید موازی: مغز مش؛ outbox ۲۸ پیام بی‌ارسال؛ drain فقط retry-با-state؛ آینه‌ی 15min rsync fail rc=255.

## GitHub (repo ari-OCTOPUS/ofn-node)
- main = 6e2bfd50 «feat(agents): repair_api — the board's self-healing pharmacy» (pushed 2026-09-03T07:11:52Z)
- 8 PR باز؛ ۶ مورد MERGEABLE (کلاس kernel-pure P1)؛ #113 PARKED؛ #71 CONFLICTING.
