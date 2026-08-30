---
type: receipt
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [hw-discovery, ssh, repos, scheduler, board138, board180, board182]
created: 2026-08-30
updated: 2026-08-30
created_by: agent
language: fa
sources:
  - "[[../06-EVIDENCE/BOARD138-RESTORE-2026-08-30/RECEIPT]]"
---

# RECEIPT — کشف سخت‌افزارها + repoها + اسکجولر (2026-08-30، لپ‌تاپ .191)

```text
RUN=LAPTOP_DISCOVERY_RUN=YES (192.168.0.191 = همین لپ‌تاپ)
METHOD=ping + /dev/tcp:22 + ssh BatchMode (بدون هیچ تغییر پیکربندی روی نودها)
ADAPTATION=ping ویندوزی (-n/-w) به‌جای سینتکس لینوکسی طرح اولیه
```

## اتصال (فایل‌های خام: ping-*.log، tcp22-*.log، ssh-*.log، connectivity.txt)

| نود | host | ping | tcp22 | SSH |
|---|---|---|---|---|
| 138 | 192.168.0.138 | OK | باز | **OK با `ari@`** — DietPi |
| 180 | 192.168.0.180 | OK | باز | **OK با `root@`** — hostname: octopus-continuity-180 |
| 182 | 192.168.0.182 | OK | باز | **OK با `root@`** — hostname: sensorium-opi5pro |
| 191 | 192.168.0.191 | OK (self) | بسته | ABSENT — همین لپ‌تاپ است؛ sshd ندارد |

## repoها

**180 — چهار repo (repos-180.txt):**
- `/opt/octopus/lab` @ `76db5162` شاخهٔ `ofn/evolve-20260826-anatomy-180` — **ریسک اصلی:** remote تنظیم‌شده ندارد، **۱ کامیت پوش‌نشده** (`76db516` «Add additive anatomy dispute corrections for board 180» — ۲ فایل، +۲۱۰ خط؛ اثبات با fetch فقط‌خواندنی از برد و مقایسهٔ ancestry با `origin/ofn/evolve-20260826-anatomy-180@36e579e` در گیت‌هاب) + **۷ فایل untracked** (AGENT_HANDOFF_RK35XX_VALIDATION، ARBITER-FEEDBACK-180، BOARD-138-COMMAND-PATH، MEGAPROMPT-QUALITY-BRAIN، QUALITY-DRAFTS-PAINTING، T1_LOCKED_SOAK_ACTIVE، artifacts/.../26_fresh_soak_15min_report.md)
- `/opt/octopus/ofn-l4` @ `08f9155` master، ۱۶ فایل
- `/opt/octopus/a2-lab/sandbox-repo` @ `029dd40` master، ۱ فایل
- `/opt/octopus/lab/llama.cpp-src` @ `f280b26` — آینهٔ upstream ggml-org/llama.cpp

**182 — صفر repo گیت.** `/opt/octopus` + `/opt/octopus-agent` پوشه‌های نسخه‌دارنشده: **۲۳,۳۵۲ فایل** (تازه‌ترین: exchange-ledger.jsonl، REPORTS/daily/2026-08-29.md). کل محتوای Sensorium بدون VCS است.

**لپ‌تاپ — ۹ repo (repos-laptop.txt):** F:\backup (rescue/octopus-live-tree-20260821@ee2ddb5) · F:\ofn-node (main@e459e5f، محلی عقب‌تر از origin) · F:\octopus-wire (ofn/wire@ca038d4) · F:\octopus-phase0-isolated · F:\backup-deploy-lab · F:\backup-SAFE-2026-07-19 · F:\romajan · F:\_______Black Box · C:\Users\Armin (main@a3000f0)

## گیت‌هاب (ls-remote تازه — lsremote-*.txt)

- `backup/board138-20260830` = `c1969bce` (exit-code 0) · `work/truth-record-20260830` = `9bc05ab` — **فقط همین‌ها**؛ برای ۱۸۰/۱۸۲/لپ‌تاپ هیچ branch حفاظتی وجود ندارد
- PRها از `refs/pull/*/head`: ‏**#1**=`d94c42c` (audit/cursor-20260828)، **#2**=`678975b` (audit/zcode-20260828) — هیچ‌کدام از branch حفاظتی نیستند. `gh` نصب نیست (GH_CLI_AVAILABLE=NO)؛ draft/open بودن فقط از UI/API — وجود PR از refs/pull اثبات می‌شود، draft بودن نه.

## اسکجولر (scheduler-*.txt)

- **138:** `octopus-scheduler.timer` زنده، `OnCalendar=*:0/15` (هر ۱۵ دقیقه؛ آخرین شلیک 08:15 AEST) — اما `journalctl -u octopus-scheduler -24h` **صفر خط** برگرداند → هیچ شواهدی از فاز Deep Test. سایر تایمرها: heartbeat، bridge-watchdog، sync-watchdog، budget-monitor.
- **180:** تایمرهای heartbeat/mesh/drain/mirror + cron `node_watchdog.sh`؛ سرویس cognitive-worker در حالت activating. هیچ واحد/لاگ «deep test».
- **182:** تایمرهای witness-worker، obs-autoheal، homeo-feeds، agent-exchange، sentinel، crossnode-probe. هیچ deep test.
- **لپ‌تاپ:** ۱۰ تسک OCTOPUS در Task Scheduler همه Ready (germline-hourly، Observatory Hourly، ۴ Watchdog، doctor-day، …) — هیچ تسک Deep Test. `_ops/logs` فهرست خالی.

## حکم

```text
SCHEDULER_DEEP_TEST_LOGS=NOT_FOUND
HIGH_RISK_UNPUSHED=board180:/opt/octopus/lab (1 commit + 7 untracked, no remote)
UNVERSIONED=board182:/opt/octopus{,-agent} (23,352 files)
PRESERVATION_CANDIDATES=backup/board180-20260830 (از /opt/octopus/lab@76db5162) · اسنپ‌شات /opt/octopus-agent@182
NEXT_PENDING_OWNER=ساخت+push برنچ حفاظتی 180 (یک دستور) · رفع C-055 · Draft PR مرورگری 138
```

source: اجرای مستقیم این session · truth: `MEASURED` (بدون حدس نام repo/remote)
