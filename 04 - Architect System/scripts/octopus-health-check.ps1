# octopus-health-check.ps1 - READ ONLY. Changes nothing, starts nothing, stops nothing.
# Answers: "is anything running that should not be, and what is eating the laptop?"
#
#   powershell -ExecutionPolicy Bypass -File "F:\backup\04 - Architect System\scripts\octopus-health-check.ps1"
#
# Copy the whole output back to Claude.

$ErrorActionPreference = "SilentlyContinue"
function H($t) { Write-Host ""; Write-Host "=== $t ===" -ForegroundColor Cyan }

Write-Host ""
Write-Host "OCTOPUS HEALTH CHECK  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  (read-only)"

H "1. disk space"
Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" |
    Select-Object DeviceID,
        @{n='SizeGB';   e={[math]::Round($_.Size/1GB,1)}},
        @{n='FreeGB';   e={[math]::Round($_.FreeSpace/1GB,1)}},
        @{n='Free%';    e={ if($_.Size){[math]::Round(100*$_.FreeSpace/$_.Size,1)}else{0} }} |
    Format-Table -AutoSize | Out-String | Write-Host

H "2. top 12 processes by RAM"
Get-Process | Sort-Object WS -Descending | Select-Object -First 12 `
    Id, ProcessName,
    @{n='RAM_MB'; e={[math]::Round($_.WS/1MB,1)}},
    @{n='CPU_sec';e={ if($_.CPU){[math]::Round($_.CPU,0)}else{0} }} |
    Format-Table -AutoSize | Out-String | Write-Host

H "3. top 12 processes by CPU time consumed since they started"
Get-Process | Where-Object { $_.CPU } | Sort-Object CPU -Descending | Select-Object -First 12 `
    Id, ProcessName,
    @{n='CPU_sec'; e={[math]::Round($_.CPU,0)}},
    @{n='RAM_MB';  e={[math]::Round($_.WS/1MB,1)}},
    @{n='Started'; e={ if($_.StartTime){$_.StartTime.ToString('MM-dd HH:mm')}else{'?'} }} |
    Format-Table -AutoSize | Out-String | Write-Host

H "4. python / powershell / git instances (duplicates = a restart loop)"
$procs = Get-CimInstance Win32_Process |
    Where-Object { $_.Name -match '^(python|pythonw|powershell|pwsh|git|node)\.exe$' }
Write-Host ("  total matching processes: {0}" -f @($procs).Count)
$procs | Group-Object Name | Sort-Object Count -Descending |
    ForEach-Object { Write-Host ("    {0,-16} x{1}" -f $_.Name, $_.Count) }
Write-Host ""
Write-Host "  command lines (trimmed to 150 chars):"
$procs | Sort-Object Name, ProcessId | ForEach-Object {
    $cl = "$($_.CommandLine)"
    if ($cl.Length -gt 150) { $cl = $cl.Substring(0,150) + '...' }
    Write-Host ("    [{0,6}] {1}" -f $_.ProcessId, $cl)
}

H "5. the organism's three ports (8771 organism / 8772 cortex / 8773 live)"
foreach ($p in 8771,8772,8773,8790) {
    $c = @(Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue)
    if ($c.Count -eq 0) { Write-Host ("    {0}  not listening" -f $p) }
    else {
        foreach ($x in $c) {
            $nm = (Get-Process -Id $x.OwningProcess -ErrorAction SilentlyContinue).ProcessName
            Write-Host ("    {0}  LISTEN  pid {1} ({2})" -f $p, $x.OwningProcess, $nm)
        }
        if ($c.Count -gt 1) { Write-Host ("    ^^ WARNING: {0} listeners on {1}" -f $c.Count, $p) -ForegroundColor Red }
    }
}

H "6. scheduled tasks that touch this project"
Get-ScheduledTask | ForEach-Object {
    $t = $_
    $acts = @($t.Actions | ForEach-Object { "$($_.Execute) $($_.Arguments)" })
    if ($acts -match 'backup|germline|octopus|organism|cortex|watchdog|tg-center') {
        $inf = $t | Get-ScheduledTaskInfo
        Write-Host ("    [{0}] {1}" -f $t.State, $t.TaskName)
        Write-Host ("        run as : {0}" -f $t.Principal.UserId)
        Write-Host ("        last   : {0}  result 0x{1:X}" -f $inf.LastRunTime, $inf.LastTaskResult)
        Write-Host ("        next   : {0}" -f $inf.NextRunTime)
        foreach ($a in $acts) { Write-Host ("        does   : {0}" -f $a) }
    }
}

H "7. is a germline run in flight right now?"
$lock = "F:\backup\_ops\backup\gitwrite.lock"
if (Test-Path $lock) {
    $li = Get-Item $lock
    Write-Host ("    gitwrite.lock present, age {0:N1} min" -f ((Get-Date)-$li.LastWriteTime).TotalMinutes)
    Write-Host ("    content: {0}" -f (Get-Content $lock -Raw -ErrorAction SilentlyContinue))
} else { Write-Host "    no git-write lock (idle)" }
Write-Host "    last 5 hourly results:"
Get-Content "E:\germline\hourly.log" -Tail 5 -ErrorAction SilentlyContinue | ForEach-Object { Write-Host "      $_" }

H "8. biggest space consumers under this project"
foreach ($p in @("F:\backup\.git", "F:\backup\_ops", "E:\germline", "$env:TEMP")) {
    if (Test-Path $p) {
        $s = (Get-ChildItem $p -Recurse -File -ErrorAction SilentlyContinue |
              Measure-Object -Property Length -Sum).Sum
        if (-not $s) { $s = 0 }
        Write-Host ("    {0,10:N0} MB   {1}" -f ($s/1MB), $p)
    }
}

H "9. antivirus real-time scanning (a common cause of git slowness here)"
$mp = Get-MpPreference -ErrorAction SilentlyContinue
if ($mp) {
    $st = Get-MpComputerStatus -ErrorAction SilentlyContinue
    Write-Host ("    Defender real-time protection : {0}" -f $st.RealTimeProtectionEnabled)
    $ex = @($mp.ExclusionPath)
    if ($ex.Count -eq 0 -or -not $ex) { Write-Host "    exclusions: NONE" }
    else { foreach ($e in $ex) { Write-Host "    excluded: $e" } }
    Write-Host "    (F:\backup\.git is scanned on every bundle unless excluded)"
} else { Write-Host "    Defender cmdlets unavailable (third-party AV?)" }

Write-Host ""
Write-Host "done - nothing was changed." -ForegroundColor Green
