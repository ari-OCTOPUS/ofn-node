# git-serialize.ps1 — cross-process serialization for git WRITES against F:\backup\.git.
#
# INCIDENT-2 (git-race): the scheduled germline backup task and dev/organism processes
# both write to F:\backup\.git at the same time -> transient "Permission denied" on
# .git/objects (Windows renames loose objects; a concurrent read/repack holds the handle).
#
# Fix: a LIGHT advisory lock. Any automated git writer routes its git calls through here so
# they run one-at-a-time, and the writer also defers while git's own .git\index.lock is held.
#
# Design mirrors the vault's existing lock convention (_ops/budget/opslib.py -> LockedJson):
#   * atomic create-exclusive lock file (FileMode::CreateNew, FileShare::None)
#   * bounded retry with capped exponential back-off + jitter
#   * steal a STALE lock (older than -StaleSeconds) left by a crashed process
#   * release in a finally block (crash -> handle freed by OS -> next run steals it)
#   * FAIL LOUD on timeout: write a FAILED flag + throw (never silently skip a backup)
#
# Dot-source it, then use Invoke-WithGitWriteLock { ... } or Invoke-SerializedGit -GitArgs @(...).
# This file only DEFINES functions; dot-sourcing it runs nothing.
#
# PowerShell 5.1 compatible (no ternary / ?? / ?.).

Set-StrictMode -Version 2.0

function Write-GitWriteFailure {
    # Fail-loud marker. Never throws; the caller decides to throw/exit after calling this.
    param([string]$FlagDir, [string]$Reason)
    try {
        if ($FlagDir) {
            New-Item -ItemType Directory -Force -Path $FlagDir | Out-Null
            $stamp = Get-Date -Format 'yyyy-MM-dd_HHmmss'
            "GITWRITE-FAILED $stamp : $Reason" |
                Out-File -FilePath (Join-Path $FlagDir 'GITWRITE-FAILED.flag') -Encoding utf8
        }
    } catch {
        # a broken flag dir must not mask the real failure; the throw still follows upstream
    }
    Write-Error $Reason
}

function Enter-GitWriteLock {
    # Acquire the advisory lock. Returns an open [System.IO.FileStream] handle (keep it,
    # pass to Exit-GitWriteLock). On timeout: writes FAILED flag and throws.
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$LockPath,
        [string]$FlagDir,
        [int]$MaxAttempts   = 40,
        [double]$BaseDelayMs = 100,
        [double]$MaxDelayMs  = 2000,
        [double]$StaleSeconds = 120
    )
    $lockDir = Split-Path -Parent $LockPath
    if ($lockDir) { New-Item -ItemType Directory -Force -Path $lockDir | Out-Null }

    for ($attempt = 0; $attempt -lt $MaxAttempts; $attempt++) {
        try {
            $fs = [System.IO.File]::Open(
                $LockPath,
                [System.IO.FileMode]::CreateNew,   # atomic: throws IOException if it already exists
                [System.IO.FileAccess]::Write,
                [System.IO.FileShare]::None)       # exclusive handle while we hold it
            $meta = [System.Text.Encoding]::UTF8.GetBytes(
                "pid=$PID host=$env:COMPUTERNAME acquired=$([DateTime]::UtcNow.ToString('o'))")
            $fs.Write($meta, 0, $meta.Length)
            $fs.Flush()
            return $fs
        } catch [System.IO.IOException] {
            # Lock is held (or vanished mid-check). Try to steal it if it is stale.
            try {
                $age = ([DateTime]::UtcNow - [System.IO.File]::GetLastWriteTimeUtc($LockPath)).TotalSeconds
                if ($age -gt $StaleSeconds) {
                    try {
                        Remove-Item -LiteralPath $LockPath -Force -ErrorAction Stop
                        continue   # stolen (holder was dead) -> retry create immediately
                    } catch {
                        # a LIVE holder still owns the exclusive handle -> not really stale; wait
                    }
                }
            } catch {
                # lock disappeared between existence and mtime read -> just retry
            }
            # capped exponential back-off + small jitter (avoid thundering herd)
            $exp   = [Math]::Min($attempt, 8)
            $delay = [Math]::Min($MaxDelayMs, $BaseDelayMs * [Math]::Pow(2, $exp))
            $delay = $delay + (Get-Random -Minimum 0 -Maximum 50)
            Start-Sleep -Milliseconds ([int]$delay)
        } catch {
            # unexpected (e.g. permission on the lock dir) -> fail loud, do not spin
            Write-GitWriteFailure -FlagDir $FlagDir -Reason "git-write lock error on ${LockPath}: $_"
            throw
        }
    }
    $reason = "git-write lock TIMEOUT after $MaxAttempts attempts on $LockPath"
    Write-GitWriteFailure -FlagDir $FlagDir -Reason $reason
    throw $reason
}

function Exit-GitWriteLock {
    # Release the advisory lock: close the handle, then delete the file. Idempotent, never throws.
    param([System.IO.FileStream]$Handle, [string]$LockPath)
    if ($Handle) {
        try { $Handle.Close(); $Handle.Dispose() } catch { }
    }
    if ($LockPath) {
        try { Remove-Item -LiteralPath $LockPath -Force -ErrorAction SilentlyContinue } catch { }
    }
}

function Wait-GitIndexLock {
    # Defer while git's own .git\index.lock is present (a commit/add is in flight in another
    # process). On timeout: FAILED flag + throw. No-op if .git is a gitdir file (worktree/submodule).
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$RepoRoot,
        [double]$TimeoutSeconds = 60,
        [double]$MaxDelayMs = 1000,
        [string]$FlagDir
    )
    $indexLock = Join-Path $RepoRoot '.git\index.lock'
    $deadline  = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    $attempt   = 0
    while (Test-Path -LiteralPath $indexLock) {
        if ([DateTime]::UtcNow -gt $deadline) {
            $reason = "git index.lock still held after $TimeoutSeconds s: $indexLock"
            Write-GitWriteFailure -FlagDir $FlagDir -Reason $reason
            throw $reason
        }
        $exp   = [Math]::Min($attempt, 6)
        $delay = [Math]::Min($MaxDelayMs, 100 * [Math]::Pow(2, $exp))
        Start-Sleep -Milliseconds ([int]$delay)
        $attempt++
    }
}

function Invoke-WithGitWriteLock {
    # Run a scriptblock as the SOLE git writer: acquire advisory lock, wait out index.lock,
    # run the action, always release the lock in finally. The action's own throw propagates
    # (lock still released) so callers stay fail-loud.
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][scriptblock]$Action,
        [string]$RepoRoot = $(if ($env:VAULT_ROOT)      { $env:VAULT_ROOT }      else { 'F:\backup' }),
        [string]$LockPath = $(if ($env:GITWRITE_LOCK)    { $env:GITWRITE_LOCK }    else { 'F:\backup\_ops\backup\gitwrite.lock' }),
        [string]$FlagDir  = $(if ($env:GITWRITE_FLAGDIR) { $env:GITWRITE_FLAGDIR } else { 'F:\backup\_ops\backup' }),
        [int]$MaxAttempts    = 40,
        [double]$BaseDelayMs  = 100,
        [double]$MaxDelayMs   = 2000,
        [double]$StaleSeconds = 120,
        [double]$IndexLockTimeoutSeconds = 60
    )
    $handle = Enter-GitWriteLock -LockPath $LockPath -FlagDir $FlagDir `
        -MaxAttempts $MaxAttempts -BaseDelayMs $BaseDelayMs -MaxDelayMs $MaxDelayMs -StaleSeconds $StaleSeconds
    try {
        Wait-GitIndexLock -RepoRoot $RepoRoot -TimeoutSeconds $IndexLockTimeoutSeconds -FlagDir $FlagDir
        return (& $Action)
    } finally {
        Exit-GitWriteLock -Handle $handle -LockPath $LockPath
    }
}

function Invoke-SerializedGit {
    # Convenience: run a single git command under the advisory lock. Fail-loud on non-zero exit.
    #   Invoke-SerializedGit -GitArgs @('-C', $repo, 'commit', '-m', 'x')
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string[]]$GitArgs,
        [string]$RepoRoot = $(if ($env:VAULT_ROOT)      { $env:VAULT_ROOT }      else { 'F:\backup' }),
        [string]$LockPath = $(if ($env:GITWRITE_LOCK)    { $env:GITWRITE_LOCK }    else { 'F:\backup\_ops\backup\gitwrite.lock' }),
        [string]$FlagDir  = $(if ($env:GITWRITE_FLAGDIR) { $env:GITWRITE_FLAGDIR } else { 'F:\backup\_ops\backup' }),
        [int]$MaxAttempts    = 40,
        [double]$BaseDelayMs  = 100,
        [double]$MaxDelayMs   = 2000,
        [double]$StaleSeconds = 120,
        [double]$IndexLockTimeoutSeconds = 60
    )
    Invoke-WithGitWriteLock -RepoRoot $RepoRoot -LockPath $LockPath -FlagDir $FlagDir `
        -MaxAttempts $MaxAttempts -BaseDelayMs $BaseDelayMs -MaxDelayMs $MaxDelayMs `
        -StaleSeconds $StaleSeconds -IndexLockTimeoutSeconds $IndexLockTimeoutSeconds -Action {
            & git @GitArgs
            if ($LASTEXITCODE -ne 0) {
                $reason = "git failed exit=$LASTEXITCODE  args: $($GitArgs -join ' ')"
                Write-GitWriteFailure -FlagDir $FlagDir -Reason $reason
                throw $reason
            }
        }
}
