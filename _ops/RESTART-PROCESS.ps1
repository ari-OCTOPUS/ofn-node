# RESTART-PROCESS.ps1 - restart one octopus process, verifiably (owner-run).
#
#   .\RESTART-PROCESS.ps1 center     # telegram_center\center.py
#   .\RESTART-PROCESS.ps1 live       # live\server.py        (port 8773)
#   .\RESTART-PROCESS.ps1 cortex     # cortex\cortex.py      (port 8772)
#   .\RESTART-PROCESS.ps1 gateway    # telegram_center\miniapp_gateway.py (port 8774)
#   .\RESTART-PROCESS.ps1 status     # just print every age, change nothing
#
# To restart EVERYTHING with one command, use RESTART-ALL.ps1 (or double-click
# RESTART-ALL.bat). It calls this script per limb and then verifies the result.
#
# Why this exists (2026-07-28):
#   None of the RUN-*.bat launchers kill the running instance. Launch one while
#   the old process still holds its port and the new one cannot bind, exits
#   silently, and from the outside it looks like "restarted". That happened
#   FOUR times in one day - cortex twice, then center and live - and each time
#   the fix that was supposedly live was still sitting in a file nobody had
#   loaded. The organism is four independent processes; "I restarted it" is
#   not a fact until you compare PIDs.
#
# Strategy per process:
#   center - honours STOP-TG-CENTER: create marker, wait for exit, remove, launch.
#   cortex - honours STOP-CORTEX (checked at the top of a ~120s cycle).
#   live   - has no stop marker; its watchdog revives it whenever 8773 is down,
#            so it is stopped directly and then relaunched.
#
# Safety: a stray STOP-* marker keeps a limb asleep forever, so the marker is
# always removed - including on the timeout path. Output is ASCII-only: Persian
# text pasted back into a console gets re-executed as commands.

param([Parameter(Position = 0)][string]$Target = "status")

$ErrorActionPreference = "Stop"
$ops = "F:\backup\_ops"

function Get-Proc([string]$match) {
    # Filter on Name='python.exe' first. Matching CommandLine alone also matches
    # the shell running THIS script (its own text contains the pattern) - that
    # false positive made a probe report six supervisor loops when there were two.
    Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
        Where-Object { $_.CommandLine -like "*$match*" } | Select-Object -First 1
}

function Get-Loops([string]$batName) {
    # The supervisor loops (cmd.exe running RUN-*.bat), not the python child.
    #
    # 2026-07-28: RUN-TG-CENTER.bat is a LOOP - it runs center.py and, when that
    # exits, sleeps 10s and starts it again. The first version of this script only
    # waited for center.py to die, then removed the STOP marker immediately. The
    # OLD loop never saw the marker, woke up, and launched a second centre. Result:
    # two supervisor loops and two pollers on one bot token - a 409 waiting to
    # happen. Killing the child without the parent is not a restart, it is a
    # respawn.
    @(Get-CimInstance Win32_Process -Filter "Name='cmd.exe'" |
        Where-Object { $_.CommandLine -like "*$batName*" })
}

function Show-Status {
    foreach ($m in @("organism.py", "center.py", "cortex.py", "live\server.py", "miniapp_gateway.py")) {
        $p = Get-Proc $m
        if ($p) {
            Write-Host ("  {0,-22} pid={1,-7} started {2}" -f $m, $p.ProcessId,
                        $p.CreationDate.ToString("HH:mm:ss"))
        } else {
            Write-Host ("  {0,-22} NOT RUNNING" -f $m)
        }
    }
}

if ($Target -eq "status") { Write-Host "PROCESS AGES:"; Show-Status; exit 0 }

$cfg = @{
    center = @{ match = "center.py";     stop = "STOP-TG-CENTER"; port = $null
                loop = "RUN-TG-CENTER"
                bat = "$ops\telegram_center\RUN-TG-CENTER.bat" }
    cortex = @{ match = "cortex.py";     stop = "STOP-CORTEX";    port = 8772
                loop = $null
                bat = "$ops\RUN-CORTEX.bat" }
    live   = @{ match = "live\server.py"; stop = $null;           port = 8773
                loop = $null
                bat = "$ops\run-live-headless.bat" }
}
# organism is deliberately NOT in $cfg above: its stop marker is STOP-ORGANISM, the one
# global kill switch, and on 2026-07-28 a stray copy of that file (written by a test that
# ran against the live tree) kept the whole system down for 30 minutes. So it gets its own
# path with two rules the generic one does not have:
#   1. If it is not running, just launch. Never write a marker to start something.
#   2. If it is running, write ONLY RESTART-REQUESTED (C-047 fix, OWNER-DIRECTIVE-12
#      section 10): under the P2 launcher, STOP-ORGANISM is NEVER auto-deleted, so
#      writing the pair risks a stray STOP killing the whole system if this script
#      dies mid-restart (exactly the 2026-07-28 incident class). Single marker =
#      organism clean-exits as RESTART; the launcher loop (or this script's own
#      relaunch below) brings it back. STOP-ORGANISM alone still means "stay down
#      until a human deletes it".
if ($Target -eq "organism") {
    $bat = "$ops\RUN-ORGANISM.bat"
    if (-not (Test-Path $bat)) { Write-Host ("ERROR: launcher not found: " + $bat); exit 1 }
    $before = Get-Proc "organism.py"
    $restF = Join-Path $ops "RESTART-REQUESTED"
    if (-not $before) {
        Write-Host "BEFORE : not running - launching directly (no marker written)."
    } else {
        Write-Host ("BEFORE : pid={0} started {1}" -f $before.ProcessId,
                    $before.CreationDate.ToString("HH:mm:ss"))
        try {
            Set-Content -Path $restF -Value (Get-Date -Format "s") -Encoding utf8
            Write-Host "RESTART-REQUESTED written (single marker, C-047) - waiting up to 300s..."
            $deadline = (Get-Date).AddSeconds(300)
            while ((Get-Date) -lt $deadline) {
                $still = Get-Proc "organism.py"
                if ((-not $still) -or ($still.ProcessId -ne $before.ProcessId)) { break }
                Start-Sleep -Seconds 5
            }
        } finally {
            # Only OUR OWN marker is cleaned here; the owner STOP is never touched (P2).
            if (Test-Path $restF) { Remove-Item $restF -Force -ErrorAction SilentlyContinue }
        }
    }
    if (-not (Get-Proc "organism.py")) {
        Write-Host "Launching..."
        Start-Process -FilePath $bat -WindowStyle Hidden
    }
    $deadline = (Get-Date).AddSeconds(120)
    while ((Get-Date) -lt $deadline) {
        $now = Get-Proc "organism.py"
        if ($now -and ((-not $before) -or ($now.ProcessId -ne $before.ProcessId))) { break }
        Start-Sleep -Seconds 5
    }
    $after = Get-Proc "organism.py"
    foreach ($m in @($stopF, $restF)) {
        if (Test-Path $m) {
            Write-Host ("WARNING: marker still present: " + $m + " - remove it or nothing boots.")
        }
    }
    if (-not $after) { Write-Host "WARNING: organism not running yet."; exit 4 }
    Write-Host ("AFTER  : pid={0} started {1}" -f $after.ProcessId,
                $after.CreationDate.ToString("HH:mm:ss"))
    if ($before -and $after.ProcessId -eq $before.ProcessId) {
        Write-Host "WARNING: same pid - it never actually restarted."; exit 3
    }
    Write-Host "OK: organism running with fresh code."
    exit 0
}

# gateway is not in $cfg either, for two reasons: it has no .bat launcher (the
# scheduled watchdog starts it inline) and it needs OCTOPUS.env loaded into the
# process environment before launch. Added 2026-08-03 so that "how do I restart X"
# has exactly ONE answer for every X - before this, the gateway was the one limb you
# had to restart by hand, and the hand-written version is how a stale gateway kept
# serving pre-merge code.
if ($Target -eq "gateway") {
    $before = Get-Proc "miniapp_gateway.py"
    if ($before) {
        Write-Host ("BEFORE : pid={0} started {1}" -f $before.ProcessId,
                    $before.CreationDate.ToString("HH:mm:ss"))
        Stop-Process -Id $before.ProcessId -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 4
    } else {
        Write-Host "BEFORE : not running"
    }
    $envFile = Join-Path $ops "OCTOPUS.env"
    if (Test-Path $envFile) {
        Get-Content $envFile | ForEach-Object {
            if ($_ -match '^([A-Za-z_][A-Za-z0-9_]*)=(.*)$') {
                [Environment]::SetEnvironmentVariable($Matches[1], $Matches[2], "Process")
            }
        }
    }
    # ⚠️ ۲۰۲۶-۰۸-۰۵ — گیت‌وی OCTOPUS.env را می‌گرفت ولی OCTOPUS-flags.cmd را نه.
    #
    # سنجهٔ زنده: center و cortex هرکدام **۱۶۵** فلگ داشتند و گیت‌وی **۷**.
    # یعنی پروسه‌ای که رابطِ اصلیِ مالک را سرو می‌کند تقریباً بی‌فلگ بالا
    # می‌آمد، و هر قابلیتی که پشتِ یک فلگ است در آن limb خاموش بود — بی‌آنکه
    # کسی بفهمد، چون از بیرون سالم به‌نظر می‌رسید.
    #
    # این‌طور کشف شد: OCTOPUS_REACH را ست کردم، center و cortex ردیفِ پروب
    # نوشتند و گیت‌وی ننوشت. خودِ پروب اولین چیزی را که پیدا کرد، همین
    # نابرابری بود.
    #
    # همان تجزیه‌ای که خطِ ۱۶۵ برای بقیهٔ limbها می‌کند — نه کپیِ منطق، همان الگو.
    $flagsFile = Join-Path $ops "OCTOPUS-flags.cmd"
    if (Test-Path $flagsFile) {
        foreach ($ln in (Get-Content $flagsFile -Encoding utf8)) {
            if ($ln -match '^\s*set\s+([A-Za-z_][A-Za-z0-9_]*)=(.*)$') {
                [Environment]::SetEnvironmentVariable($Matches[1], $Matches[2].Trim(), "Process")
            }
        }
    }
    $env:OCTOPUS_TG_MINIAPP = "1"
    Write-Host "Launching..."
    Start-Process -FilePath "python" `
        -ArgumentList @("-X","utf8",(Join-Path $ops "telegram_center\miniapp_gateway.py")) `
        -WorkingDirectory (Join-Path $ops "telegram_center") -WindowStyle Hidden | Out-Null
    $deadline = (Get-Date).AddSeconds(90)
    while ((Get-Date) -lt $deadline) {
        $now = Get-Proc "miniapp_gateway.py"
        if ($now -and ((-not $before) -or ($now.ProcessId -ne $before.ProcessId))) { break }
        Start-Sleep -Seconds 3
    }
    $after = Get-Proc "miniapp_gateway.py"
    if (-not $after) {
        Write-Host "WARNING: gateway not running yet. The 10-min watchdog should revive it."; exit 4
    }
    Write-Host ("AFTER  : pid={0} started {1}" -f $after.ProcessId,
                $after.CreationDate.ToString("HH:mm:ss"))
    if ($before -and $after.ProcessId -eq $before.ProcessId) {
        Write-Host "WARNING: same pid - it never actually restarted."; exit 3
    }
    Write-Host "OK: gateway restarted with fresh code."
    exit 0
}

if (-not $cfg.ContainsKey($Target)) {
    Write-Host "ERROR: unknown target '$Target'. Use: organism | center | live | cortex | gateway | status"; exit 1
}
$c = $cfg[$Target]
if (-not (Test-Path $c.bat)) { Write-Host ("ERROR: launcher not found: " + $c.bat); exit 1 }

$before = Get-Proc $c.match
if ($before) {
    Write-Host ("BEFORE : pid={0} started {1}" -f $before.ProcessId,
                $before.CreationDate.ToString("HH:mm:ss"))
} else {
    Write-Host "BEFORE : not running"
}

$marker = if ($c.stop) { Join-Path $ops $c.stop } else { $null }
try {
    if ($marker) {
        if (-not (Test-Path $marker)) { New-Item -ItemType File -Path $marker | Out-Null }
        Write-Host ("STOP marker created ({0}) - waiting up to 300s..." -f $c.stop)
    } elseif ($before) {
        Write-Host "No stop marker for this process - stopping it directly."
        Stop-Process -Id $before.ProcessId -Force -ErrorAction SilentlyContinue
    }

    # Wait for BOTH the python child and every supervisor loop to be gone.
    # Waiting only for the child is what produced two loops earlier today: the
    # marker was removed the moment center.py died, the old loop woke up 10s
    # later, never saw the marker, and started a second centre.
    $deadline = (Get-Date).AddSeconds(300)
    while ((Get-Date) -lt $deadline) {
        $still  = Get-Proc $c.match
        $childGone = (-not $still) -or ($before -and $still.ProcessId -ne $before.ProcessId)
        $loopsGone = $true
        if ($c.loop) { $loopsGone = ((Get-Loops $c.loop).Count -eq 0) }
        if ($childGone -and $loopsGone) { break }
        Start-Sleep -Seconds 5
    }

    if ($c.loop) {
        $lingering = @(Get-Loops $c.loop)
        if ($lingering.Count -gt 0) {
            Write-Host ("Stopping {0} lingering supervisor loop(s)..." -f $lingering.Count)
            foreach ($l in $lingering) {
                Stop-Process -Id $l.ProcessId -Force -ErrorAction SilentlyContinue
            }
            Start-Sleep -Seconds 3
        }
    }

    $still = Get-Proc $c.match
    if ($still -and $before -and $still.ProcessId -eq $before.ProcessId) {
        Write-Host "TIMEOUT: old process still alive. Nothing relaunched."
        exit 2
    }
} finally {
    # Never leave a marker behind - that would keep the limb asleep forever.
    if ($marker -and (Test-Path $marker)) { Remove-Item $marker -Force -ErrorAction SilentlyContinue }
}

Write-Host "Old process gone. Launching..."
Start-Process -FilePath $c.bat -WindowStyle Hidden

$deadline = (Get-Date).AddSeconds(120)
while ((Get-Date) -lt $deadline) {
    $now = Get-Proc $c.match
    if ($now -and (-not $before -or $now.ProcessId -ne $before.ProcessId)) { break }
    Start-Sleep -Seconds 5
}

$after = Get-Proc $c.match
if (-not $after) {
    Write-Host "WARNING: not running yet. The 5-min watchdog should revive it."
    exit 4
}
Write-Host ("AFTER  : pid={0} started {1}" -f $after.ProcessId,
            $after.CreationDate.ToString("HH:mm:ss"))
if ($before -and $after.ProcessId -eq $before.ProcessId) {
    Write-Host "WARNING: same pid - it never actually restarted."
    exit 3
}
if ($c.loop) {
    # 2026-07-28: this printed "LOOPS  :  supervisor loop(s)" with an empty count and
    # then warned about it. The @() inside Get-Loops does NOT survive the return - a
    # zero-match pipeline unrolls to $null, and $null.Count formats as empty. So the
    # script reported a scary 409 warning when the real answer was "zero loops". Wrap
    # at the CALL SITE, which is the only place PowerShell cannot unroll it.
    $loops = @(Get-Loops $c.loop)
    Write-Host ("LOOPS  : {0} supervisor loop(s)" -f $loops.Count)
    if ($loops.Count -ne 1) {
        Write-Host "WARNING: expected exactly 1 supervisor loop - two pollers on one bot token cause 409."
        exit 5
    }
}
Write-Host "OK: restarted with fresh code."
exit 0
