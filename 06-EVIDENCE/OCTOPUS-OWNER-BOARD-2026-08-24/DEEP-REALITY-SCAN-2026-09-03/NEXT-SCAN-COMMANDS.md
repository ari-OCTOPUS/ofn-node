# NEXT-SCAN-COMMANDS — فقط فقط‌خواندنی

## PowerShell (لپ‌تاپ)
```powershell
# CWD و cmdline کامل پروسه‌های 877x
Get-CimInstance Win32_Process | Where-Object {$_.CommandLine -match 'organism|cortex|live\\server|telegram_center'} | Select ProcessId,ParentProcessId,CommandLine | Format-List
# وضعیت زندهٔ orphan-watchdog
Get-Content 'F:\backup\state\orphan-watchdog\receipts.jsonl' -Tail 5
# تایمرهای ویندوزی مرتبط
Get-ScheduledTask | Where-Object {$_.TaskName -match 'OCTOPUS'} | Select TaskName,State
# وضعیت WAL (مسیر رسمی فقط-خواندنی)
Get-ChildItem 'F:\backup\_ops\state' -Filter '*wal*' -Recurse -ErrorAction SilentlyContinue | Select FullName,Length,LastWriteTime
```

## Bash روی 138 (ssh ari@192.168.0.138)
```bash
# هویت سرویس‌ها: کدام فایل را اجرا می‌کنند
for u in heartbeat doctor witness absence selfmodel mesh-drain imap quote scheduler budget-monitor; do echo "== $u"; systemctl cat octopus-$u.service 2>/dev/null | grep -E 'ExecStart|WorkingDirectory'; done
# رسید تایمرها بدون journal (ملاک: LastTrigger)
systemctl list-timers --all --no-pager | grep octopus
# صف‌های مش با تاریخچه
for d in ~/octopus-mesh/{outbox,inbox,state,rejected,receipts}; do echo "$d=$(ls $d 2>/dev/null|wc -l) last=$(ls -t $d 2>/dev/null|head -1)"; done
# شمارش inbox واقعی
sqlite3 -readonly ~/.local/share/ofn/inbox.sqlite "SELECT COUNT(*) FROM marketing_inbox;"
# دکتر 138: کجا گزارش می‌نویسد
systemctl cat octopus-doctor.service | grep -E 'ExecStart'; ls -la ~/ofn/state 2>/dev/null
```

## GitHub
```bash
cd /f/ofn-node
gh pr list --state open --json number,title,mergeable,headRefOid --jq '.[]|"\(.number) \(.mergeable) \(.headRefOid[0:8]) \(.title[0:60])"'
gh api repos/ari-OCTOPUS/ofn-node/commits/main --jq '.sha[0:8]+" "+.commit.message[0:60]'
```

## از 138 به 182/180 (کلید آن‌سو؛ در صورت وجود)
```bash
ssh <182> 'hostname; ss -tlnp | grep -E "4222|879"; systemctl --failed --no-legend; du -sh ~/.local/share/*/events.jsonl 2>/dev/null'
```
