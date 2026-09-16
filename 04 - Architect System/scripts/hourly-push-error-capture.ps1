# hourly-push-error-capture.ps1 — P3: capture git-push stderr, redact, classify.
# Dot-source only. Does not change remotes, credentials, timers, or retry policy.
# PowerShell 5.1 compatible (no ternary / ?? / ?.).

Set-StrictMode -Version 2.0

function Get-RedactedGitPushStderr {
    param([string]$Text)
    if ($null -eq $Text) { return '' }
    $s = [string]$Text
    $s = [regex]::Replace($s, '(?i)\bhttps?://[^\s''"<>]+', '<redacted-url>')
    $s = [regex]::Replace($s, '(?i)\bssh://[^\s''"<>]+', '<redacted-url>')
    $s = [regex]::Replace($s, '(?i)\bgit@[^\s''"<>]+', '<redacted-url>')
    $s = [regex]::Replace($s, '(?i)\b(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{8,}', '<redacted-token>')
    $s = [regex]::Replace($s, '(?i)\bgithub_pat_[A-Za-z0-9_]{8,}', '<redacted-token>')
    $s = [regex]::Replace($s, '(?i)\bglpat-[A-Za-z0-9_\-]{8,}', '<redacted-token>')
    $s = [regex]::Replace($s, 'eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}', '<redacted-token>')
    $eval = [System.Text.RegularExpressions.MatchEvaluator] {
        param($m)
        return ($m.Groups[1].Value + '=<redacted-token>')
    }
    $s = [regex]::Replace($s, '(?i)\b(token|password|passwd|secret|api[_-]?key|access[_-]?token|username|user)[=:\s]+\S+', $eval)
    return $s
}

function Get-GitPushErrorClass {
    param(
        [Parameter(Mandatory)][int]$ExitCode,
        [string]$StderrText
    )
    if ($ExitCode -eq 0) { return 'NONE' }
    $t = ''
    if ($null -ne $StderrText) { $t = [string]$StderrText }

    if ($t -match 'could not read Username|could not read Password|terminal prompts disabled|Authentication required|could not authenticate') {
        return 'AUTH_REQUIRED'
    }
    if ($t -match 'Authentication failed|Invalid username or password|HTTP Basic: Access denied|401 Unauthorized|403 Forbidden|Authentication rejected|Permission denied \(publickey\)') {
        return 'AUTH_DENIED'
    }
    if ($t -match 'Could not resolve host|Name or service not known|nodename nor servname|getaddrinfo failed|Temporary failure in name resolution') {
        return 'DNS_FAILURE'
    }
    if ($t -match 'timed out|Timeout was reached|Failed to connect to|Connection timed out|Operation timed out|SSL connection timeout') {
        return 'NETWORK_TIMEOUT'
    }
    if ($t -match 'Repository not found|remote: Not Found|does not appear to be a git repository|repository .+ not found|Could not read from remote repository') {
        return 'REMOTE_NOT_FOUND'
    }
    if ($t -match '\[rejected\]|failed to push some refs|non-fast-forward|already exists|fetch first|Updates were rejected') {
        return 'REF_REJECTED'
    }
    if ($t -match 'index\.lock|Cannot lock ref|Unable to create|Another git process seems to be running in this repository|Permission denied') {
        return 'LOCK_FAILURE'
    }
    return 'UNKNOWN'
}

function Get-Sha256HexUtf8 {
    param([string]$Text)
    if ($null -eq $Text) { $Text = '' }
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($Text)
        $hash = $sha.ComputeHash($bytes)
        return (-join ($hash | ForEach-Object { $_.ToString('x2') }))
    } finally {
        $sha.Dispose()
    }
}

function Write-GitPushErrorRecord {
    param(
        [Parameter(Mandatory)][string]$RecordPath,
        [Parameter(Mandatory)][string]$Label,
        [Parameter(Mandatory)][int]$ExitCode,
        [Parameter(Mandatory)][string]$ErrorClass,
        [Parameter(Mandatory)][int]$ElapsedMs,
        [string]$RedactedStderr,
        [string]$CycleId,
        [string]$PushPhase,
        [string]$RemoteClass,
        [string]$TargetPathOrRedactedRemote,
        [string]$LockState
    )
    if ($null -eq $RedactedStderr) { $RedactedStderr = '' }
    if (-not $CycleId) { $CycleId = 'unknown' }
    if (-not $PushPhase) { $PushPhase = $Label }
    if (-not $RemoteClass) { $RemoteClass = 'unknown' }
    if ($null -eq $TargetPathOrRedactedRemote) { $TargetPathOrRedactedRemote = '' }
    if (-not $LockState) { $LockState = 'unknown' }
    $dir = Split-Path -Parent $RecordPath
    if ($dir) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    $ts = (Get-Date).ToString('o')
    $record = [ordered]@{
        report_schema_version = 'octopus.p3.push-diagnostics.v1'
        cycle_id = $CycleId
        push_phase = $PushPhase
        remote_class = $RemoteClass
        target_path_or_redacted_remote = (Get-RedactedGitPushStderr -Text $TargetPathOrRedactedRemote)
        exit_code = $ExitCode
        stderr_sha256 = (Get-Sha256HexUtf8 -Text $RedactedStderr)
        error_class = $ErrorClass
        elapsed_ms = $ElapsedMs
        lock_state = $LockState
        timestamp = $ts
        label = $Label
        redacted_stderr = $RedactedStderr
    }
    $line = ($record | ConvertTo-Json -Compress -Depth 6)
    Add-Content -LiteralPath $RecordPath -Value $line -Encoding utf8
    return [pscustomobject]$record
}

function Get-GitPushErrLogLine {
    param($First, $Second)
    $caps = @($First, $Second)
    foreach ($cap in $caps) {
        if ($null -eq $cap) { continue }
        if ([int]$cap.ExitCode -eq 0) { continue }
        $text = [string]$cap.RedactedStderr
        $firstLine = @(($text -replace "`r", '') -split "`n" | Where-Object { $_.Trim().Length -gt 0 } | Select-Object -First 1)
        if ($firstLine) { return ([string]$firstLine).Trim() }
        return ("exit={0} class={1}" -f $cap.ExitCode, $cap.ErrorClass)
    }
    return ''
}

function ConvertTo-NativeArgString {
    param([string[]]$Parts)
    $bits = New-Object System.Collections.Generic.List[string]
    foreach ($p in $Parts) {
        if ($null -eq $p) { continue }
        $s = [string]$p
        if ($s -match '[\s"]') {
            $s = '"' + ($s.Replace('"', '\"')) + '"'
        }
        $bits.Add($s)
    }
    return ($bits -join ' ')
}

function Invoke-CapturedGitCommand {
    # Native stderr is written to a TEMP file first, then redacted before persistence.
    # Uses Process streams (not PowerShell `2>`) so git text is not UTF-16-garbled.
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$RepoRoot,
        [Parameter(Mandatory)][string[]]$GitArgs,
        [Parameter(Mandatory)][string]$RecordPath,
        [Parameter(Mandatory)][string]$Label,
        [string]$GitExe = 'git',
        [string]$CycleId,
        [string]$PushPhase,
        [string]$RemoteClass,
        [string]$TargetPathOrRedactedRemote,
        [string]$LockState
    )
    $gitPath = (Get-Command $GitExe -ErrorAction Stop).Source
    $stamp = [guid]::NewGuid().ToString('n')
    $tmpErr = Join-Path $env:TEMP ("octopus-hourly-push-{0}-{1}.stderr" -f $Label, $stamp)
    $argString = ConvertTo-NativeArgString -Parts (@('-C', $RepoRoot) + @($GitArgs))

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $gitPath
    $psi.Arguments = $argString
    $psi.UseShellExecute = $false
    $psi.RedirectStandardError = $true
    $psi.RedirectStandardOutput = $true
    $psi.CreateNoWindow = $true

    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $proc = New-Object System.Diagnostics.Process
    $proc.StartInfo = $psi
    [void]$proc.Start()
    $outTask = $proc.StandardOutput.ReadToEndAsync()
    $errTask = $proc.StandardError.ReadToEndAsync()
    $proc.WaitForExit()
    $rawOut = $outTask.Result
    $rawErr = $errTask.Result
    $sw.Stop()
    $code = [int]$proc.ExitCode
    $proc.Dispose()

    if ($null -eq $rawErr) { $rawErr = '' }
    if ($null -eq $rawOut) { $rawOut = '' }
    [System.IO.File]::WriteAllText($tmpErr, $rawErr, [System.Text.UTF8Encoding]::new($false))
    $fromFile = [System.IO.File]::ReadAllText($tmpErr, [System.Text.UTF8Encoding]::new($false))

    $redacted = Get-RedactedGitPushStderr -Text $fromFile
    $cls = Get-GitPushErrorClass -ExitCode $code -StderrText $fromFile
    $elapsed = [int]$sw.ElapsedMilliseconds
    $record = Write-GitPushErrorRecord -RecordPath $RecordPath -Label $Label -ExitCode $code -ErrorClass $cls -ElapsedMs $elapsed -RedactedStderr $redacted -CycleId $CycleId -PushPhase $PushPhase -RemoteClass $RemoteClass -TargetPathOrRedactedRemote $TargetPathOrRedactedRemote -LockState $LockState

    Remove-Item -LiteralPath $tmpErr -Force -ErrorAction SilentlyContinue

    return [pscustomobject]@{
        ExitCode        = $code
        ErrorClass      = $cls
        ElapsedMs       = $elapsed
        RedactedStderr  = $redacted
        Stdout          = $rawOut
        StderrSha256    = $record.stderr_sha256
        Record          = $record
    }
}
