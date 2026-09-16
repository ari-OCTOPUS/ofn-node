# test-git-serialize.ps1 — proof for the INCIDENT-2 (git-race) fix.
#
# OFFLINE / $0. Creates a THROWAWAY git repo under the OS temp dir and points the lock at
# temp too — it NEVER touches F:\backup\.git or the real _ops\backup lock.
#
# Two concurrent OS processes (Start-Job) hammer the SAME repo with git commits, each routed
# through Invoke-WithGitWriteLock. Asserts:
#   1. both workers complete cleanly
#   2. no GITWRITE-FAILED flag was raised
#   3. `git fsck --full` is clean (no corruption from the race)
#   4. commit count == initial + workers*iters (no lost / dropped writes)
#   5. lock critical-sections never overlap in time (true mutual exclusion)
#   6. stale-lock steal works (a lock older than the threshold is reclaimed, no deadlock)
#
# Run:  powershell -NoProfile -ExecutionPolicy Bypass -File test-git-serialize.ps1

$ErrorActionPreference = 'Stop'
$helper = Join-Path $PSScriptRoot 'git-serialize.ps1'
if (-not (Test-Path $helper)) { throw "helper not found: $helper" }
. $helper

$work  = Join-Path $env:TEMP ("gitrace-test-{0}-{1}" -f $PID, (Get-Random))
$repo  = Join-Path $work 'repo'
$lock  = Join-Path $work 'gitwrite.lock'
$flags = Join-Path $work 'flags'
New-Item -ItemType Directory -Force -Path $repo, $flags | Out-Null
Write-Host "test workspace : $work"
Write-Host "real .git touched? NO (temp repo only)"
Write-Host ""

$errors = @()
try {
    # ---- setup throwaway repo (isolated identity; no signing) ----
    & git -C $repo init -q
    & git -C $repo config user.email 'test@example.invalid'
    & git -C $repo config user.name  'git race test'
    & git -C $repo config commit.gpgsign false
    'seed' | Out-File -FilePath (Join-Path $repo 'seed.txt') -Encoding utf8
    & git -C $repo add -A
    & git -C $repo commit -q -m 'initial'

    $ITER    = 8
    $WORKERS = 2

    # Each worker is a separate process: dot-source the helper, then commit ITER times
    # under the advisory lock, recording the critical-section [start,end] ticks to its own file.
    $worker = {
        param($helper, $repo, $lock, $flags, $jobId, $iter, $witness)
        . $helper
        for ($k = 0; $k -lt $iter; $k++) {
            Invoke-WithGitWriteLock -RepoRoot $repo -LockPath $lock -FlagDir $flags -Action {
                $s = [DateTime]::UtcNow.Ticks
                & git -C $repo commit --allow-empty -q -m "job$jobId-commit$k"
                $code = $LASTEXITCODE
                $e = [DateTime]::UtcNow.Ticks
                "$s $e $code" | Add-Content -LiteralPath $witness
                if ($code -ne 0) { throw "commit failed job$jobId k$k exit=$code" }
            } | Out-Null
        }
        return "job$jobId committed=$iter"
    }

    $jobs = @()
    $witnessFiles = @()
    for ($j = 0; $j -lt $WORKERS; $j++) {
        $wf = Join-Path $work "witness-$j.txt"
        $witnessFiles += $wf
        $jobs += Start-Job -ScriptBlock $worker -ArgumentList $helper, $repo, $lock, $flags, $j, $ITER, $wf
    }

    $jobs | Wait-Job | Out-Null
    foreach ($jb in $jobs) {
        $out = Receive-Job $jb
        Write-Host ("  worker[{0}] state={1} -> {2}" -f $jb.Id, $jb.State, ($out -join '; '))
        if ($jb.State -ne 'Completed') { $errors += "worker $($jb.Id) state=$($jb.State)" }
    }
    $jobs | Remove-Job -Force

    # ---- assertions ----

    # 2) no fail-loud marker
    if (Test-Path (Join-Path $flags 'GITWRITE-FAILED.flag')) {
        $errors += "GITWRITE-FAILED.flag present: " + (Get-Content (Join-Path $flags 'GITWRITE-FAILED.flag') -Raw)
    }

    # 3) repo integrity (no 2>&1: native stderr must not be turned into terminating errors)
    & git -C $repo fsck --full --no-dangling | Out-Null
    $fsckExit = $LASTEXITCODE
    if ($fsckExit -ne 0) { $errors += "git fsck exit=$fsckExit (corruption)" }

    # 4) no lost writes
    $count    = [int](& git -C $repo rev-list --count HEAD)
    $expected = 1 + $WORKERS * $ITER
    if ($count -ne $expected) { $errors += "commit count $count != expected $expected (lost/dup writes)" }

    # 5) mutual exclusion: sort all critical sections by start; none may start before the prev ended
    $intervals = @()
    foreach ($wf in $witnessFiles) {
        if (Test-Path $wf) {
            foreach ($line in (Get-Content $wf)) {
                $p = $line -split ' '
                $intervals += [pscustomobject]@{ Start = [long]$p[0]; End = [long]$p[1]; Code = [int]$p[2] }
            }
        }
    }
    $sorted  = $intervals | Sort-Object Start
    $prevEnd = [long]0
    $overlap = 0
    foreach ($iv in $sorted) {
        if ($iv.Start -lt $prevEnd) { $overlap++ }
        if ($iv.End -gt $prevEnd)   { $prevEnd = $iv.End }
    }
    $nonzero = @($intervals | Where-Object { $_.Code -ne 0 }).Count
    if ($overlap -gt 0) { $errors += "$overlap overlapping critical sections (serialization broken)" }
    if ($nonzero -gt 0) { $errors += "$nonzero git commits returned non-zero inside the lock" }

    # 6) stale-lock steal (no deadlock after a crashed holder)
    $staleLock = Join-Path $work 'stale.lock'
    'orphan-from-a-dead-process' | Out-File -FilePath $staleLock -Encoding utf8
    (Get-Item $staleLock).LastWriteTime = (Get-Date).AddSeconds(-3600)   # 1 hour old
    $stoleOk = $false
    $h = Enter-GitWriteLock -LockPath $staleLock -FlagDir $flags -StaleSeconds 120 -MaxAttempts 5
    if ($h) { Exit-GitWriteLock -Handle $h -LockPath $staleLock; $stoleOk = $true }
    if (-not $stoleOk) { $errors += "stale-lock steal failed (would deadlock)" }

    Write-Host ""
    Write-Host ("commits      : {0}  (expected {1})" -f $count, $expected)
    Write-Host ("crit-sections: {0}   overlaps: {1}   nonzero-commits: {2}" -f $intervals.Count, $overlap, $nonzero)
    Write-Host ("git fsck     : exit {0}" -f $fsckExit)
    Write-Host ("stale-steal  : {0}" -f $(if ($stoleOk) { 'reclaimed 1h-old lock' } else { 'FAILED' }))
    Write-Host ""

    if ($errors.Count -gt 0) {
        Write-Host 'RESULT: FAIL'
        $errors | ForEach-Object { Write-Host "  - $_" }
        exit 1
    }
    Write-Host 'RESULT: PASS - concurrent git writes serialized, repo valid, zero lost writes, zero overlap'
    exit 0
}
finally {
    Get-Job -ErrorAction SilentlyContinue | Where-Object { $_.Name -like 'Job*' } | Remove-Job -Force -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force $work -ErrorAction SilentlyContinue
}
