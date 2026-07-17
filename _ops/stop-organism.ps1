# stop-organism.ps1 — cleanly stop the running organism (HTTP server on port 8771)
# so RESTART-ORGANISM.bat's Step 2 can start a fresh process.
#
# WHY THIS FILE EXISTS (2026-07-17): RESTART-ORGANISM.bat line 6 called this script,
# but it was never created. So every "restart" errored at Step 1, the OLD organism kept
# running (still holding port 8771), and Step 2's RUN-ORGANISM.bat hit its own port-guard
# and printed "[redundant] already running" — the restart silently did nothing.
#
# Safe by design: targets ONLY a python process that is actually LISTENING on 8771
# (the organism). Cortex (8772) and everything else are untouched. State writes are
# atomic (tmp + os.replace), so a hard stop never corrupts ORGANISM-STATE.json.

$ErrorActionPreference = 'SilentlyContinue'
$OPS = 'F:\backup\_ops'

Write-Host '  stopping the organism on 127.0.0.1:8771 ...'

# 1) find the PID(s) listening on 8771
$owners = @(Get-NetTCPConnection -LocalPort 8771 -State Listen -ErrorAction SilentlyContinue |
            Select-Object -ExpandProperty OwningProcess -Unique)

if ($owners.Count -eq 0) {
    Write-Host '  (nothing was listening on 8771 - already stopped.)'
} else {
    foreach ($procId in $owners) {
        $p = Get-Process -Id $procId -ErrorAction SilentlyContinue
        if ($null -eq $p) { continue }
        # safety: only stop a python process (the organism), never anything else on 8771
        if ($p.ProcessName -like 'python*') {
            Write-Host ('  stopping organism PID {0} ({1}) ...' -f $procId, $p.ProcessName)
            Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        } else {
            Write-Host ('  WARNING: PID {0} on 8771 is {1}, not python - NOT touching it.' -f $procId, $p.ProcessName)
        }
    }
    Start-Sleep -Seconds 2
    $still = @(Get-NetTCPConnection -LocalPort 8771 -State Listen -ErrorAction SilentlyContinue)
    if ($still.Count -gt 0) {
        Write-Host '  WARNING: port 8771 is still held. Close the old organism window manually, then retry.'
    } else {
        Write-Host '  organism stopped.'
    }
}

# 2) clear any leftover control files so the FRESH boot is not immediately halted
foreach ($f in @('STOP-ORGANISM', 'RESTART-REQUESTED')) {
    $path = Join-Path $OPS $f
    if (Test-Path $path) {
        Remove-Item $path -Force -ErrorAction SilentlyContinue
        Write-Host ('  cleared leftover {0} file.' -f $f)
    }
}

Write-Host '  stop-organism done.'
