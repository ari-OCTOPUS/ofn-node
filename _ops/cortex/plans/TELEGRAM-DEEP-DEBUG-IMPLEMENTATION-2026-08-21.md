---
type: plan
status: active
tags: [telegram, center, deep-debug, waves-a-f, 2026-08-21]
created: 2026-08-21
updated: 2026-08-21
authority: OWNER EXECUTION ORDER — WRITE AND REPAIR AUTHORIZED (2026-08-21)
---

# TELEGRAM-DEEP-DEBUG-IMPLEMENTATION — 2026-08-21

دستور مالک: مرکز تلگرام و حلقههای وابسته را از componentهای shadow/جعبهسیاه به
runtime قابل مشاهده، قابل بازیابی، idempotent، تستپذیر و پایدار تبدیل کن.
حالت: `ARCHITECT_AND_IMPLEMENT` — read-only لغو شد؛ تعمیر/کد/تست/commit اتمی مجاز.
مرزها: بدون ارسال زنده، بدون webhook، بدون تماس پولی، بدون ادعای verification مستقل.

## ۱. Git baseline و working tree

- شاخه: `equip/g10-cognition-20260816` · HEAD فعلی: `c50327c` (بستهٔ امضای مالک)
- شاخهٔ تعمیر موازی: `repair/organs-suite-reproducible-20260821` (هد `cc267048` —
  فقط organs commit؛ مجزاست، این plan روی شاخهٔ اصلی کار میکند)
- working tree: ~۵۴۶ فایل modified/untracked از ارگانیسم زنده (state/ledger/telemetry).
  **قانون: فقط فایلهای خودِ این plan stage/commit میشوند؛ هرگز `git add -A`.**
- commitهای اخیرِ مرتبط: `bcbc3dd` (bounded state reads)، `a8f2e1a` (DNS worker)،
  `396b1d0` (دو کلاس stall)، `f314cb0` (bounded_io + health-skip). اینها پایهٔ موج C/Bاند.

## ۲. توپولوژی botها

- یک bot تولیدی: `CANONICAL_OWNER_BOT_ID = 7992324219` (process_identity.py) ·
  token از env `TG_CENTER_BOT_TOKEN` (فقط مرکز؛ هرگز لاگ/فایل نمیشود).
- مینیاپ گیتوی (`miniapp_gateway.py`) روی همان bot؛ tunnel جدا (`run-miniapp-tunnel`).
- پل تلگرام دومِ قدیمی (approval_channel / control-plane) متوقف شده (فایلهای
  STOP-TG-HEARTBEAT حذف/منتقل شدند)؛ `tg_poller_lease.py` گارد «یک bot → یک poller».

## ۳. process/launcher/watchdog ownership

- لانچر: `telegram_center/RUN-TG-CENTER.bat` (cmd loop) → `python -X utf8 center.py`.
- سرپرست بیرونی: `_ops/tg-center-watchdog.ps1` — pulse = `state/pulse/tg-center.json`
  (هر iteration مرکز مینویسد)؛ HUNG_AFTER_S=300؛ kill-then-relaunch؛ ضد 409
  (شمارش loop/centre بعد از relaunch).
- داخلی: `stall_probe.py` (پشتهٔ همهٔ نخها زیر آستانهٔ watchdog، ۲۴۰s) ·
  `restart_control.py` · `process_identity.py` (process_id/started_at/git_commit).

## ۴. polling/webhook mode

- فقط **polling** (getUpdates long-poll، timeout=25s، allowed_updates
  message/callback_query). وب‌هوک همیشه OFF (محدودیت مالک؛ بدون activation).
- offset: فقط پس از poll موفق از روی max(update_id)+1 جلو میرود
  (`TgClient.next_offset`)؛ timeout/خطا هرگز offset را جلو نمیبرد.

## ۵. token ownership (بدون افشا)

- token فقط در env فرایند مرکز. `tg_api` URL میسازد (token داخل URL) و URL هرگز
  لاگ نمیشود (`_url_json_post` فقط host `api.telegram.org` را اجازه میدهد).
- leaseها فقط digest یکطرفهٔ token را ذخیره میکنند (`poll_lease._token_digest`).
- این plan هیچ token/secret را نمیخواند، نمیچاپد و commit نمیکند.

## ۶. config/state reader/writer inventory

| مسیر | خواننده | نویسنده | حالت |
|---|---|---|---|
| `state/telegram/center-config.json` | `center._load_config` (bounded cache) | `_save_config` (4-retry+fsync) | LKG + stale؛ این wave → ConfigManager |
| `state/telegram/poll-health.json` | watchdog/human | `health_metrics.record_poll` | کامل (موج A) |
| `state/pulse/tg-center.json` | `tg-center-watchdog.ps1` | مرکز هر iteration | هر iteration نوشته میشود؟ باید اثبات/تست شود |
| `state/telegram/miniapp-hits.jsonl` | miniapp gateway | gateway | append-only |
| `state/tg-send-log.jsonl` | audit | `tg_send_log` | append-only؛ فقط live sender |
| `07 - Knowledge/genome-system/ledger/ledger.jsonl` | genome | genome | append-only |
| `_ops/doctor/state/…` ، `state/cortex/…` | doctor/cortex | doctor/cortex | خارج از scope |
| `_ops/organs/WIRING.json` | organs.flags | sidecar | خروج از scope |
| مستقیم‌خوانهای داغ: `mission._load_state` (read_text مستقیم)، `center.py:823`
  (rfcs.json read_text)، watchdog `state/pulse` | → این wave bounded/بافر میشوند |

## ۷. blocking I/O inventory

1. `Path.read_text` روی state-fileها — قفل byte-range آنتیویروس → `bounded_io` ✓
2. `socket.getaddrinfo` (DNS) در `urllib` — بدون timeout → daemon worker (a8f2e1a)؛
   نخِ گیرکرده **غیرقابل kill** است → موج C: pool باند + مسیر subprocess قابل terminate
3. `sqlite3` (poll-lease) — `timeout=10` ✓
4. `os.replace`/fsync (config write) — retry + bounded ✓
5. `subprocess.run` (transport_subprocess) — hard deadline ✓ (پیشفرض OFF)
6. تلگرام `getUpdates` خودش long-poll — timeout درخواست ✓

## ۸. thread/process ownership

- مرکز: تک-پروسهای؛ `bounded_io` pool سقف ۴ (state I/O)؛ `_bounded_http` یک نخ
  daemon بهازای request (نشتپذیر در DNS stall) → موج C جایگزین میکند.
- lease: `poll_lease.assert_poll_lease` در هر دور (SQLite، PID+boot_id+heartbeat+expiry)
  + `tg_poller_lease.acquire` در شروع پروسه (file lock، pid-alive).
- یک نویسندهٔ واحد برای config (مرکز) و یک poller واحد per token (گارد 409).

## ۹. هفت حلقهٔ تلگرام

| حلقه | trigger | state | decision | action | receipt | reconciliation |
|---|---|---|---|---|---|---|
| L1 poll | beat | offset | wired | getUpdates | poll-health | next_offset |
| L2 durable intent | update | durable_loop | authorize | dispatch | task/run id | readback |
| L3 send queue (C3/C4) | due | rate_limit_queue | admit | SenderBridge | message_id | confirm/defer/DLQ |
| L4 reconciliation | uncertain | DLQ ledger | no-resend | quarantine | DLQ receipt | audit |
| L5 event bridge | pulse/alert | outbox | throttle | push | event receipt | cursor |
| L6 health truth | هر poll | poll-health | healthy? | record | counters | snapshot |
| L7 watchdog | silent>300s | pulse | hung? | kill+relaunch | log | 1+1 prove |

## ۱۰. جعبهسیاهها (فعلی)

- DNS/transport داخل urllib (جزئی از a8f2e1a instrument شده؛ rest ابهام)
- رفتار آنتیویروس روی center-config (مشاهدهای ثبت شد؛ غیرقابل تست مستقیم)
- watchdog بیرونی (فقط log؛ رفتار kill در fixture قابل شبیهسازی نیست)
- مینیاپ tunnel stderr (فایل log جدا)
- مسیر legacy modules (GLM/چتخانههای قدیمی) — خارج از این wave

## ۱۱. فرضیههای root-cause (از incidentهای ۰۸-۲۰/۲۱)

- H1: قفل byte-range آنتیویروس روی center-config → خواندن بیپایان → HUNG.
  پشتوانه: bcbc3dd رفع؛ این wave LKG+stale را رسمی میکند (موج B).
- H2: DNS getaddrinfo بدون timeout در poll_updates → HUNG بیپایان.
  پشتوانه: a8f2e1a؛ موج C نخهای unkillable را با pool باند+subprocess جایگزین میکند.
- H3: دو poller روی یک token (409 خاموش) → بات ساکت. پشتوانه: poll_lease؛ موج D تست race.
- H4: watchdog false-positive: «no updates» با poll سالم اشتباه گرفته شود.
  پشتوانه: health-truth (موج A) — آخرین pollِ کامل = سلامت، نه آخرین update.

## ۱۲. patch waves (هر wave یک commit اتمی)

- W0: plan (این سند) + baseline receipt
- W1 (موج A): گواهی health-truth — تست «poll خالی = progress»، «no-updates=سالم»،
  watchdog-truth؛ اگر pulse هر iteration نوشته میشود (اثبات)، هیچ patch کدی لازم نیست
  جز health snapshot api
- W2 (موج B): `config_manager.py` — boot read، reload فقط با digest تغییر، snapshot
  غیرقابلتغییر، last-known-good + stale، mission/rfcs خواندن bounded؛ center به آن مهاجرت
- W3 (موج C): `transport_pool.py` — max concurrent، hard deadline، cooldown/circuit
  per-bot، subprocess-terminable (هنگام فعال)، replace worker؛ tg_api به آن مهاجرت
- W4 (موج D): تأیید lease در حلقهٔ poll + تست race/409/expiry؛ patch اگر gap
- W5 (موج E): تأیید C3→C4 (sender_bridge/durable_loop) + تست مرزهای restart
  (retry_after-1 / retry_after)، crash after attempt → UNCERTAIN no-resend، کلید تکراری
- W6 (موج F): باتری تست ۱۶ سناریوی دستور + receipt کامل
- W7: شواهد نهایی + وضعیت `IMPLEMENTATION_COMPLETE_VERIFICATION_PENDING`

## ۱۳. تستها

- fixture-only؛ `OCTOPUS_STATE_DIR` ایزوله (harness)؛ صفر شبکه واقعی؛ transport جعلی تزریقی.
- باتری W6: 100 DNS stall · 100 config read stall · 100 config write stall ·
  concurrent poller race · 409 sim · crash before/after attempt · restart at
  retry_after−1 / retry_after · duplicate key · malformed config · stale snapshot ·
  empty long poll · no updates 30min · watchdog false-positive · worker/thread leak.
- هر wave: `registered/executed/passed/failed/skipped/unexecuted` جدا.

## ۱۴. rollback

- هر commit مستقل است: `git revert <sha>` یا checkout فایلهای همان commit.
- migration نیاز نیست (فایلهای state موجود دستنخورده؛ ConfigManager فقط خواندن را
  سازماندهی میکند؛ poll-health schema حفظ میشود).
- اگر waveی suite را بشکند: fail ثبت، rollback آن commit، ادامه از wave قبلی.

## ۱۵. live boundaries

- هیچ ارسال واقعی؛ webhook OFF؛ تماس پولی صفر؛ restart مرکز زنده **فقط** بعد از
  سبز شدن fixtureها + snapshot/rollback آماده + در polling/read-only بررسی؛ هر رفتار
  ناشناخته = توقف + evidence capture.
- attach زندهٔ SenderBridge ممنوع (default-off حفظ میشود).
- وضعیت نهایی فقط یکی از: `IMPLEMENTATION_COMPLETE_VERIFICATION_PENDING` /
  `FAILED_SAFE` / `BLOCKED_OWNER_DECISION`.

## ۱۶. owner decisions still required

- اجرای canary زنده (SIG-IV مستقل + تأیید مجدد)
- فعالسازی transport subprocess بهصورت پیشفرض (فلگ زندهٔ محیطی، owner-locked)
- هرگونه تغییر TCB (watchdog kill-policy، release gates)
