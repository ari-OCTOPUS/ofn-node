---
megaprompt_title: FOUNDATION F1 — REALITY INVENTORY (لپ‌تاپ .191)
version: "1.0"
written_by: "ZCode GLM-5.3 — 2026-08-18 — فرمان مالک: FOUNDATION HARDENING v1، فقط Stage F1"
audience: ایجنت لپ‌تاپ .191 (DESKTOP-KA9RFN5 · F:\backup)
requires: "[[MEGAPROMPT-VERIFIER-00-SHARED-CONTRACT-2026-08-18]] + FOUNDATION HARDENING PROGRAM v1 (مالک، 2026-08-18)"
program: OCTOPUS FOUNDATION HARDENING v1
stage: F1_REALITY_INVENTORY
wave: WAVE0_OBSERVE_ONLY
production: false
autonomy: "بدون تغییر · L2 armed propose-only · autonomy_delta=0"
activation_order: "1/5 — F2 فقط پس از پذیرش کتبی مالک"
---

# SYSTEM NAME: OCTOPUS FOUNDATION — STAGE F1: REALITY INVENTORY (NODE .191)

AGENT ID: `agent://octopus/laptop-brain/main`

run_id: `F1-191-20260818-HHMM` — HHMM را موقع شروع با ساعت محلی پر کن.
همهٔ مهرها: `Get-Date -Format "yyyy-MM-ddTHH:mm:sszzz"` (آفست سیستم‌عامل، نه عدد ثابت).

این متن فقط Stage F1 از برنامهٔ FOUNDATION HARDENING v1 است. در صورت هر تعارضی،
متن کامل برنامهٔ مالک مقدم است. فرمان‌ها PowerShell (ویندوز) هستند؛ اگر در
Git Bash هستی همان فرمان را با `powershell -NoProfile -Command "..."` اجرا کن و
هر جایگزینی را در command-log ثبت کن.

## PRIME DIRECTIVE (F1)

تو گرهٔ لپ‌تاپ (.191) هستی — منبع حقیقت پروژه در `F:\backup`. در این اجرا فقط یک
مأموریت داری: **فهرست‌برداری واقعیت**. نه فیچر، نه ایجنت جدید، نه ارتقای
autonomy، نه هیچ تغییری در سیستم.

- فقط خواندن. تنها نوشتنِ مجاز: پوشهٔ شاهدِ همین اجرا (پایین). حتی git commit ممنوع.
- هر جمله در گزارش = منبع + مهر زمانی.
- چیزی که پیدا نشد = `NOT_FOUND`. هرگز «احتمالاً هست» ننویس.
- «فایل وجود دارد» ≠ «در runtime لود می‌شود» — این دو ستون جدا دارند.
- تناقض را ثبت کن، با حدس حلش نکن.
- درخواست/اقدام خارج از scope = DENY.

## HARD STOPS — توقف فوری و گزارش به مالک

secret در معرض دید، اثر بیرونی غیرمنتظره، مسیر اثر مسلح بدون گیت، دو ادعای
canonical متناقض، شاهدی که گزارش قبلی را رد کند.

## قواعد ثابت .191 (از قرارداد مشترک Verifier — همچنان معتبر)

- پرچم `GITWRITE-FAILED.flag` را پاک یا تغییر نده.
- فرمان `01a00d3d` را ack نکن؛ تگ `pre-deploy-2026-07-25` را force نکن.
- TCB (`4d_system/brain/daemon.py` و `automation.py`) را پچ نکن.
- راز/توکن/bearer را هرگز چاپ یا در فایل شاهد ننویس. فایل‌های راز‌نما
  (`.env`, `*.key`, `*.pem`, `*credential*`, `*token*`) را باز نکن — فقط
  وجود/حجم/mtime ثبت کن (نمونه: `F:\backup\.env` — فقط متادیتا).
- در هر خروجی ثبت‌شده، مقادیر شبیه token/key (الگوی تقریبی:
  `(?i)(token|secret|password|bearer|key=)[^ ]*`) را با `[REDACTED]` جایگزین کن
  و تعداد redactionها را در گزارش بیاور.
- escalate (admin/sudo/runas) ممنوع — دسترسیِ نیافتنی = `PERMISSION_DENIED` ثبت شود.

## SETUP — سه قدم اول

```powershell
$RUN = "F1-191-20260818-" + (Get-Date -Format "HHmm")
$CAP = "F:\backup\06-EVIDENCE\f1-191-$RUN"
New-Item -ItemType Directory -Path $CAP | Out-Null
Set-Content "$CAP\command-log.md" ("started " + (Get-Date -Format "yyyy-MM-ddTHH:mm:sszzz"))
```

از این پس **قبل از هر دستور**، متن دستور + مهر زمانی را به `command-log.md`
اضافه کن؛ خروجی هر دستور با `Out-File -Encoding utf8` داخل `$CAP` بریزد.
خطا هم شاهد است — ثبتش کن، دورش نزن.

## F1.1 — PROCESS_MAP

هدف: هر پروسهٔ زندهٔ مرتبط + مسیر دقیق کد لودشده + پورت + uptime.

```powershell
Get-CimInstance Win32_Process |
  Select-Object ProcessId,ParentProcessId,CreationDate,ExecutablePath,CommandLine |
  ConvertTo-Json -Depth 2 | Out-File "$CAP\01-process-all.json" -Encoding utf8

Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
  Select-Object LocalAddress,LocalPort,OwningProcess | Sort-Object LocalPort |
  Format-Table -AutoSize | Out-File "$CAP\01b-listen-tcp.txt" -Encoding utf8

Get-NetUDPEndpoint -ErrorAction SilentlyContinue |
  Select-Object LocalAddress,LocalPort,OwningProcess | Sort-Object LocalPort |
  Format-Table -AutoSize | Out-File "$CAP\01c-listen-udp.txt" -Encoding utf8
```

در گزارش فقط جدول فیلترشدهٔ موارد مرتبط (کلیدواژه‌ها در مسیر/آرگومان:
`octopus, 4d, backup, heartbeat, bridge, telegram, sensorium, feet, wireguard,
tailscale, ssh, python, node`) با ستون‌ها: PID / ExePath / CommandLine (redact‌شده) /
uptime (ساخت از CreationDate) / پورت مالک (join از 01b/01c روی PID) /
مسیر اسکریپت از CommandLine / `Test-Path` همان فایل.
cwd پروسه در ویندوز بدون ابزار خاص قابل‌خواندن نیست → ستون cwd = `UNKNOWN`
(ثبت کن؛ خالی نگذار). فایل خام کاملِ همهٔ پروسه‌ها در artifact می‌ماند.

## F1.2 — SERVICE_MAP

```powershell
Get-Service | Where-Object {$_.Status -eq 'Running'} |
  Select-Object Name,DisplayName,StartType |
  Out-File "$CAP\02a-services-running.txt" -Encoding utf8

Get-ScheduledTask | Where-Object {$_.State -ne 'Disabled'} |
  Select-Object TaskPath,TaskName,State |
  Out-File "$CAP\02b-scheduled-tasks.txt" -Encoding utf8

Get-CimInstance Win32_StartupCommand |
  Select-Object Name,Command,Location,User |
  Out-File "$CAP\02c-startup.txt" -Encoding utf8
```

در گزارش: فقط موارد مرتبط با OCTOPUS؛ برای هر تسکِ مرتبط، `Get-ScheduledTaskInfo`
(آخرین نتیجه/زمان اجرا) هم ثبت شود. موارد غیرمرتبط فقط در فایل خام می‌مانند.

## F1.3 — STORAGE_MAP (نوشته‌شده در ۳۰ روز اخیر)

scope صادقانه و محدود — **اسکن کل درایو ممنوع**. ریشه‌ها: `F:\backup`
(به‌جز داخل `node_modules` و داخل `.git`؛ ولی حجم کل این دو را جدا یک‌خطی ثبت کن)
+ probe این‌ها و ثبت موجود/NOT_FOUND: `C:\octopus*`, `%USERPROFILE%\.octopus*`.

```powershell
Get-ChildItem "F:\backup" -Recurse -File -ErrorAction SilentlyContinue |
  Where-Object { $_.LastWriteTime -gt (Get-Date).AddDays(-30) -and
                 $_.FullName -notmatch '\\node_modules\\' -and
                 $_.FullName -notmatch '\\\.git\\' } |
  Select-Object @{n='bytes';e={$_.Length}},LastWriteTime,FullName |
  Export-Csv "$CAP\03-storage-30d.csv" -NoTypeInformation -Encoding utf8
```

در گزارش: جدول خلاصه (تعداد/حجم به‌ازای دایرکتوری سطح ۱) + فهرست فایل‌های
صفر‌بایتی (`Length -eq 0` — نگرانی کش شبکه) + متادیتای فایل‌های راز‌نما
بدون بازکردن. محدودهٔ اسکن را صریح بنویس؛ «اسکن کامل درایو انجام نشد» یک
uncertainty است، نه شکست.

## F1.4 — REPO_MAP

```powershell
Get-ChildItem "F:\backup" -Recurse -Directory -Filter ".git" -Depth 4 -Force -ErrorAction SilentlyContinue |
  Select-Object -ExpandProperty FullName | Out-File "$CAP\04a-git-dirs.txt" -Encoding utf8

Get-ChildItem "F:\backup" -Recurse -File -Include *.bundle,*.pack -Depth 4 -ErrorAction SilentlyContinue |
  Select-Object FullName,Length | Out-File "$CAP\04b-bundles.txt" -Encoding utf8
```

برای هر repo کشف‌شده (و برای خود `F:\backup`):

```powershell
foreach ($g in Get-Content "$CAP\04a-git-dirs.txt") {
  $repo = Split-Path $g -Parent
  "=== $repo ===" | Out-File "$CAP\04-repo-map.txt" -Append -Encoding utf8
  git -C $repo rev-parse HEAD 2>&1            | Out-File "$CAP\04-repo-map.txt" -Append -Encoding utf8
  git -C $repo branch --show-current 2>&1     | Out-File "$CAP\04-repo-map.txt" -Append -Encoding utf8
  git -C $repo remote -v 2>&1                 | Out-File "$CAP\04-repo-map.txt" -Append -Encoding utf8
  "dirty_files: " + (git -C $repo status --porcelain=v1 | Measure-Object -Line).Lines |
                                                Out-File "$CAP\04-repo-map.txt" -Append -Encoding utf8
  git -C $repo worktree list 2>&1             | Out-File "$CAP\04-repo-map.txt" -Append -Encoding utf8
  git -C $repo stash list 2>&1                | Out-File "$CAP\04-repo-map.txt" -Append -Encoding utf8
}
```

کپی‌های غیر-git (`_Duplicates`, `_archive-binaries`, `_portable-build`,
`lead-naghshi-portable.zip`, …) فقط **ثبت** شوند. طبقه‌بندی
CANONICAL/MIRROR/ARCHIVE/ORPHAN کار F2 است — اینجا فقط واقعیت.

## F1.5 — NETWORK_MAP

```powershell
Get-NetTCPConnection -State Established -ErrorAction SilentlyContinue |
  Select-Object LocalAddress,LocalPort,RemoteAddress,RemotePort,OwningProcess |
  Out-File "$CAP\05a-established.txt" -Encoding utf8

Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -ne '127.0.0.1'} |
  Select-Object InterfaceAlias,IPAddress | Out-File "$CAP\05b-interfaces.txt" -Encoding utf8

Get-NetAdapter | Select-Object Name,InterfaceDescription,Status |
  Out-File "$CAP\05c-adapters.txt" -Encoding utf8
```

تونل‌ها: از `01-process-all.json` پروسه‌های ssh/wireguard/tailscale/cloudflared
با آرگومان‌های `-L`/`-R` جدا کن (با redact). **هیچ probe یا ارسال شبکهٔ جدید
مجاز نیست** — فقط مشاهدهٔ آنچه همین حالا هست.

## F1.6 — AGENT_MAP

گره‌ها را فقط از شواهد محلی فهرست کن — **بدون هیچ تماس شبکه**:

- mtime فایل‌های `06-EVIDENCE\envelopes\cycle-*.json` (+ `.sha256` کناری)
- لیست و mtime/hجم `_ops\state\` و `_ops\state\handshake\` (فقط متادیتا)
- انتهای `_ops\handshake\CHANGELOG.md` (آخرین seq لپ‌تاپ)
- هر فایل heartbeat در `_ops\state` (متادیتا + آخرین خط اگر متنیِ امن است)

جدول: گره (`.191` / `.182` / `.138` / `.180` و هر گره دیگری که شاهد محلی دارد) /
نقش / وضعیت زندهٔ قابل‌استناد (`DIRECT-FRESH` | `STALE` | `UNKNOWN`) / منبع + mtime.
اگر نقش `.180` از شواهد محلی روشن نیست → `UNKNOWN`، نه حدس.

## SUBSYSTEM_STATUS — جدول کلیدی F1

هر ادعای معماری در اسناد ↔ وضعیت runtime. ستون‌ها:
`زیرسیستم | ادعا در کدام سند | LIVE / PRESENT_UNWIRED / NOT_FOUND | شاهد`

seed حداقلی — با مرور `00-INDEX.md`، `README.md` و جدیدترین یادداشت‌های
`06-EVIDENCE` **کاملش کن**:

- دیمون قلب 4d — `4d_system/brain/daemon.py` (پروسه زنده؟)
- off_heartbeat — `_ops/off_heartbeat.py`
- envelope sidecar — `_ops/handshake/emit_cycle.py` + `envelope.py` (CHANGELOG در حال رشد؟)
- octopus-bridge — `octopus-bridge/` (پروسه/خروجی تازه دارد؟)
- nervous-system — `nervous-system/`
- حافظه — `_memory/` + پچ memory_read/claim_hypothesis (ادعا: آماده، مراسم TCB مانده)
- `GITWRITE-FAILED.flag` — کجاست + mtime (تغییر ممنوع)
- `goal_action_bridge.py` / `wiring.py` / `organism.py` در `_ops/`
- دیمون P3/hourly (یادداشت‌های 2026-08-18)
- **ادعاهای سند شورا ۲۰۲۶-۰۸-۱۸ (ردهٔ ۵ — فقط برای راستی‌آزمایی، نه پذیرش):**
  - «۹ پروسهٔ زنده» و «heartbeat هر ~۶۵–۱۲۸ ثانیه» → شمارش واقعی از F1.1
  - «لجر هش‌زنجیره‌ای با بیش از ۱۱٬۴۰۰ رکورد» → مسیر فایل + شمار رکورد از F1.3
  - «گیت‌های مرکزی WIRED=False، dual-veto خاموش، Viability Loop/Sensorium در کد نیست» → جستجوی کد/پرچم (فایل باشد بدون اثر اجرا = PRESENT_UNWIRED)
  - «سه سیستم حافظهٔ جدا؛ memory.db ۴۵۹ سطری + فایل صفربایتی در مسیر غلط + unconscious.json» → مسیر/حجم/سطرِ هر کدام
  - `FREEZE.flag` و خطای ویندوزی `budget-state.json` → فقط مکان + mtime + متن خطا؛ **پاک‌کردن یا تغییر ممنوع**
  - شل خام `/sh` → مسیر کد + مسلح/غیرمسلح (فقط گزارش)
  - «executor فقط A0/A1 دارد و A2 به BLOCK خورده» → شاهد runtime/لاگ اخیر

قاعدهٔ برچسب: `LIVE` = پروسه یا خروجی تازه (mtime در دورهٔ ادعایی خودش، پیش‌فرض ≤26h)؛
`PRESENT_UNWIRED` = فایل هست ولی اثری از اجرا/مصرف نیست؛ `NOT_FOUND` = نه فایل، نه اثر.

## REPORT — قالب خروجی (عیناً در چت + در `$CAP\00-REPORT.md`)

- run_id, node_id=.191 (laptop-brain), stage=F1, started_at, finished_at
- دستورات اجراشده (ارجاع به command-log.md + تعداد)
- artifactها با SHA-256:
  `Get-ChildItem $CAP -File -Exclude MANIFEST.sha256 | Get-FileHash -Algorithm SHA256 | Format-Table -AutoSize | Out-File "$CAP\MANIFEST.sha256" -Encoding utf8`
- یافته‌ها با شدت (HIGH/MED/LOW/INFO)
- تناقض‌ها (هر مورد: دو منبع + مهرهایشان)
- unknownها — صریح؛ سکوت یعنی قطعیت جعلی
- تصمیم‌های لازم از مالک
- verdict: `PASS | PARTIAL | INSUFFICIENT_EVIDENCE | UNKNOWN_CANONICAL | HALTED_BY_POLICY`

## بستن مرحله

F1 فقط با **پذیرش کتبی مالک** بسته می‌شود. تو پذیرش تولید نمی‌کنی؛ گزارش می‌دهی و
می‌ایستی. F2 را شروع نکن.
