---
type: evidence
session: owner-authorized restart, follow-up to memory/learning absence report
agent: Claude Sonnet 5 (Claude Code)
created: 2026-08-17 ~21:08
mode: single owner-approved action (explicit yes in chat) — no flags changed, no TCB edit
---

# 4d daemon restart — 2026-08-17 ~21:08

## چرا
گزارشِ حافظه/یادگیری (`00 - Inbox/...` یا فایلِ ارسالی به مالک، `OCTOPUS-MEMORY-LEARNING-REPORT-2026-08-17.md`) کشف کرد دیمونِ 4d (`python -m brain.daemon`, pid قدیمی 27164) از `2026-08-16T15:39:45` بی‌صدا متوقف بوده — ۲۹ ساعت، بدون آلارم. مالک صریحاً در چت ریاستارت را تأیید کرد.

## چرا هیچ اسکریپتِ رسمی نبود
`_ops/RESTART-PROCESS.ps1`ِ `$cfg` فقط `center`/`cortex`/`live` (+ مسیرِ جداگانهٔ `organism`) را پوشش می‌دهد — دیمونِ 4d اصلاً یکی از پنج عضوِ ارگانیسم نیست، یک پروسهٔ کاملاً جدا است. `4d_system/RUNBOOK.md` هم سندِ کهنه‌ایست («ممنوع: starting daemon») که با عملِ واقعیِ روزهای اخیر (۹ نسل ریاستارت) در تضاد است. پس روالِ دستیِ زیر، با همان درسِ DEEP-TEST-1H («فلگ در فرایندها زنده است نه فایل — لانچر باید از flags.cmd تغذیه شود») ساخته شد.

## روال اجراشده [A]
```powershell
$envLines = cmd.exe /c 'call "F:\backup\_ops\OCTOPUS-flags.cmd" >nul 2>&1 && set'
foreach ($line in $envLines) { if ($line -match '^([^=]+)=(.*)$') {
    [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process") } }
Start-Process -FilePath python -ArgumentList "-m","brain.daemon" `
    -WorkingDirectory "F:\backup\4d_system" `
    -RedirectStandardOutput "outputs\daemon-launch4.log" -RedirectStandardError "outputs\daemon-launch4.err.log" `
    -WindowStyle Hidden -PassThru
```
۴۳۵ متغیر از `flags.cmd` قبل از لانچ بارگذاری شد (نه صدازدنِ python از یک شلِ خام).

## راستی‌آزمایی [A]
| بررسی | قبل (halted) | بعد (pid نو) |
|---|---|---|
| pid | 27164 (مرده) | **24588** |
| `resumed_at` | — | 2026-08-17T21:08:26 |
| `kernel.integrity_ok` | **false** | **true** |
| tick اول | — | 21:08:38، introspect کامل: 242 فایل·745 تابع·1190 فرضیه·5 تجربه |
| env در پروسهٔ واقعی (`psutil.Process(24588).environ()`) | — | `OCTOPUS_TCB_MANIFEST_ENFORCE=1` · `SELF_CODE_ENABLED=1` |
| errors_this_run | — | 0 |

نکته: `kernel.integrity_ok` از `false` به `true` رفت چون این ریاستارت manifest امضاشدهٔ دیروز (شاملِ فیکسِ C-033، `core/model.py` در digest-map) را برای اولین‌بار لود کرد — پروسهٔ قدیمیِ متوقف‌شده هرگز آن را ندید.

یک هشدارِ شناخته‌شده و بی‌خطر در لاگ: `REFERENCE_DIR='./' به ریشهٔ پروژه resolve شد — مرزِ نامعتبر (C-013)؛ fallback به SYSTEM_ROOT/'4D'` — همان چیزی که در حلِّ C-013 مستندشده، بی‌اثر روی حفاظتِ TCB.

## کارِ باز
- هیچ آلارمِ خودکاری برای «دیمون بیش از X ساعت بی‌تیک» هنوز وجود ندارد (مالک این گزینه را در همین دور رد کرد — یادداشت برای بعد).
- روالِ بالا دستی است؛ اگر تکرار شود، یک `RESTART-4D-DAEMON.ps1` رسمی (هم‌الگو با `RESTART-PROCESS.ps1`) ارزشش را دارد.
