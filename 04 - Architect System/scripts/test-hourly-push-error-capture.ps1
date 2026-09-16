# test-hourly-push-error-capture.ps1 — P3 acceptance (offline).
# Does not touch F:\backup\.git, remotes, credentials, or the scheduled task.
# Not registered in _ops/tests/run_all.py (WORKLOCK).
#
# Run: powershell -NoProfile -ExecutionPolicy Bypass -File "test-hourly-push-error-capture.ps1"

$ErrorActionPreference = 'Stop'
$helper = Join-Path $PSScriptRoot 'hourly-push-error-capture.ps1'
if (-not (Test-Path -LiteralPath $helper)) { throw "helper not found: $helper" }
. $helper

$work = Join-Path $env:TEMP ("hourly-push-capture-test-{0}-{1}" -f $PID, (Get-Random))
$repo = Join-Path $work 'repo'
$bare = Join-Path $work 'bare.git'
$records = Join-Path $work 'hourly-push-errors.jsonl'
New-Item -ItemType Directory -Force -Path $repo | Out-Null
$errors = @()
$requiredFields = @(
    'cycle_id', 'push_phase', 'remote_class', 'target_path_or_redacted_remote',
    'exit_code', 'stderr_sha256', 'error_class', 'elapsed_ms', 'lock_state',
    'timestamp', 'report_schema_version'
)
$allowedClasses = @(
    'NONE', 'AUTH_REQUIRED', 'AUTH_DENIED', 'NETWORK_TIMEOUT', 'DNS_FAILURE',
    'REMOTE_NOT_FOUND', 'REF_REJECTED', 'LOCK_FAILURE', 'UNKNOWN'
)

function Assert-True($cond, [string]$msg) {
    if (-not $cond) { $script:errors += $msg }
}

function Assert-Schema($row, [string]$where) {
    foreach ($k in $script:requiredFields) {
        Assert-True ($row.PSObject.Properties.Name -contains $k) ("{0} missing {1}" -f $where, $k)
    }
    Assert-True ($row.report_schema_version -eq 'octopus.p3.push-diagnostics.v1') ("{0} schema version" -f $where)
    Assert-True ($script:allowedClasses -contains $row.error_class) ("{0} class not allowed: {1}" -f $where, $row.error_class)
}

try {
    & git -C $repo init -q
    & git -C $repo config user.email 'test@example.invalid'
    & git -C $repo config user.name 'hourly push capture test'
    & git -C $repo config commit.gpgsign false
    'seed' | Out-File -FilePath (Join-Path $repo 'seed.txt') -Encoding utf8
    & git -C $repo add -A
    & git -C $repo commit -q -m 'initial'

    # 1) redaction: URL, token, password, username must not persist
    $secret = 'ghp_TESTTOKEN1234567890abcdefghij'
    $raw = "fatal: Authentication failed for 'https://github.com/example/repo.git' token=$secret password=s3cretValue username=alice"
    $red = Get-RedactedGitPushStderr -Text $raw
    Assert-True ($red -notmatch [regex]::Escape($secret)) 'redact leaked ghp_ test token'
    Assert-True ($red -notmatch 's3cretValue') 'redact leaked password value'
    Assert-True ($red -notmatch 'username=alice') 'redact leaked username value'
    Assert-True ($red -notmatch 'https://') 'redact left a URL'
    Assert-True ($red -match '<redacted-url>') 'redact missing URL placeholder'
    Assert-True ($red -match '<redacted-token>') 'redact missing token placeholder'
    $clsAuth = Get-GitPushErrorClass -ExitCode 1 -StderrText $raw
    Assert-True ($clsAuth -eq 'AUTH_DENIED') ("auth class got $clsAuth")
    Write-GitPushErrorRecord -RecordPath $records -Label 'redact' -ExitCode 1 -ErrorClass $clsAuth -ElapsedMs 1 -RedactedStderr $red -CycleId 'test-redact' -PushPhase 'all' -RemoteClass 'github' -TargetPathOrRedactedRemote 'https://github.com/example/repo.git' -LockState 'held' | Out-Null
    $persisted = Get-Content -LiteralPath $records -Raw
    Assert-True ($persisted -notmatch [regex]::Escape($secret)) 'persisted log leaked ghp_ test token'
    Assert-True ($persisted -notmatch 's3cretValue') 'persisted log leaked password'
    Assert-True ($persisted -notmatch 'https://github.com') 'persisted log leaked URL'
    Assert-True ($persisted -notmatch 'username=alice') 'persisted log leaked username'

    $classFixtures = @{
        AUTH_REQUIRED   = 'fatal: could not read Username for ''https://example.invalid'': terminal prompts disabled'
        AUTH_DENIED     = 'remote: Invalid username or password'
        NETWORK_TIMEOUT = 'fatal: unable to access ''https://example.invalid/'': Failed to connect to example.invalid port 443: Connection timed out'
        DNS_FAILURE     = 'fatal: unable to access ''https://no-such-host.invalid/'': Could not resolve host: no-such-host.invalid'
        REMOTE_NOT_FOUND = 'fatal: repository ''https://example.invalid/missing.git'' not found'
        REF_REJECTED    = '! [rejected]        main -> main (non-fast-forward)'
        LOCK_FAILURE    = 'fatal: Unable to create ''C:/tmp/repo/.git/index.lock'': File exists.'
        UNKNOWN         = 'fatal: something unclassified happened'
    }
    foreach ($name in $classFixtures.Keys) {
        $got = Get-GitPushErrorClass -ExitCode 1 -StderrText $classFixtures[$name]
        Assert-True ($got -eq $name) ("class fixture {0} got {1}" -f $name, $got)
    }
    Assert-True ((Get-GitPushErrorClass -ExitCode 0 -StderrText 'ignored') -eq 'NONE') 'zero exit not NONE'

    # 2) simulated nonzero git command -> non-empty redacted record
    $missing = Join-Path $work 'no-such-remote.git'
    $capFail = Invoke-CapturedGitCommand -RepoRoot $repo -GitArgs @('push','--quiet',$missing,'--all') -RecordPath $records -Label 'all' -CycleId 'test-fail' -PushPhase 'all' -RemoteClass 'local-path' -TargetPathOrRedactedRemote $missing -LockState 'held'
    Assert-True ($capFail.ExitCode -ne 0) ("expected nonzero git push, got $($capFail.ExitCode)")
    Assert-True ($capFail.ErrorClass -ne 'NONE') 'nonzero push classified as NONE'
    Assert-True ($capFail.RedactedStderr -and $capFail.RedactedStderr.Trim().Length -gt 0) 'nonzero push produced empty redacted stderr'
    Assert-True ($capFail.StderrSha256 -and $capFail.StderrSha256.Length -eq 64) 'missing stderr_sha256'
    Assert-True ($capFail.ElapsedMs -ge 0) 'elapsed_ms missing'
    Assert-True ($allowedClasses -contains $capFail.ErrorClass) ("class not in allowlist: $($capFail.ErrorClass)")
    Write-Host ("nonzero stderr: {0}" -f (($capFail.RedactedStderr -replace '\s+', ' ').Trim()))
    Assert-True ($capFail.RedactedStderr -notmatch [regex]::Escape($secret)) 'capture path leaked test token'
    Assert-Schema $capFail.Record 'fail-record'

    # 3) successful command -> exit_code=0 error_class=NONE
    $capOk = Invoke-CapturedGitCommand -RepoRoot $repo -GitArgs @('status','--porcelain') -RecordPath $records -Label 'ok' -CycleId 'test-ok' -PushPhase 'all' -RemoteClass 'local-path' -TargetPathOrRedactedRemote $repo -LockState 'held'
    Assert-True ($capOk.ExitCode -eq 0) ("success exit got $($capOk.ExitCode)")
    Assert-True ($capOk.ErrorClass -eq 'NONE') ("success class got $($capOk.ErrorClass)")
    Assert-Schema $capOk.Record 'ok-record'

    # 4) lock: classifier fixture is authoritative; live git add with index.lock
    $clsLock = Get-GitPushErrorClass -ExitCode 1 -StderrText "fatal: Unable to create 'C:/tmp/repo/.git/index.lock': File exists. Another git process seems to be running in this repository."
    Assert-True ($clsLock -eq 'LOCK_FAILURE') ("lock classifier got $clsLock")
    'lock-seed' | Out-File -FilePath (Join-Path $repo 'lock-seed.txt') -Encoding utf8
    $indexLock = Join-Path $repo '.git\index.lock'
    'held-by-p3-test' | Out-File -FilePath $indexLock -Encoding ascii
    $capLock = Invoke-CapturedGitCommand -RepoRoot $repo -GitArgs @('add','-A') -RecordPath $records -Label 'lock' -CycleId 'test-lock' -PushPhase 'all' -RemoteClass 'local-path' -TargetPathOrRedactedRemote $repo -LockState 'held'
    Remove-Item -LiteralPath $indexLock -Force -ErrorAction SilentlyContinue
    Assert-True ($capLock.ExitCode -ne 0) ("lock test expected nonzero, got $($capLock.ExitCode)")
    Assert-True ($capLock.ErrorClass -eq 'LOCK_FAILURE') ("lock class got $($capLock.ErrorClass)")
    Assert-True ($capLock.RedactedStderr -match 'index\.lock|Unable to create|Another git process|lock') 'lock stderr missing lock marker'
    Assert-Schema $capLock.Record 'lock-record'

    # 5) --tags failure, separate from --all
    & git init --bare -q $bare
    $capAll = Invoke-CapturedGitCommand -RepoRoot $repo -GitArgs @('push','--quiet',$bare,'--all') -RecordPath $records -Label 'all' -CycleId 'test-tags' -PushPhase 'all' -RemoteClass 'local-path' -TargetPathOrRedactedRemote $bare -LockState 'held'
    Assert-True ($capAll.ExitCode -eq 0) ("--all seed push failed: $($capAll.RedactedStderr)")
    & git -C $repo tag p3-test-tag
    $capTags1 = Invoke-CapturedGitCommand -RepoRoot $repo -GitArgs @('push','--quiet',$bare,'--tags') -RecordPath $records -Label 'tags' -CycleId 'test-tags' -PushPhase 'tags' -RemoteClass 'local-path' -TargetPathOrRedactedRemote $bare -LockState 'held'
    Assert-True ($capTags1.ExitCode -eq 0) ("first --tags push failed: $($capTags1.RedactedStderr)")
    'second' | Out-File -FilePath (Join-Path $repo 'seed.txt') -Encoding utf8
    & git -C $repo add -A
    & git -C $repo commit -q -m 'second'
    & git -C $repo tag -f p3-test-tag
    $capTagsFail = Invoke-CapturedGitCommand -RepoRoot $repo -GitArgs @('push','--quiet',$bare,'--tags') -RecordPath $records -Label 'tags' -CycleId 'test-tags' -PushPhase 'tags' -RemoteClass 'local-path' -TargetPathOrRedactedRemote $bare -LockState 'held'
    Assert-True ($capTagsFail.ExitCode -ne 0) ("expected --tags reject, got $($capTagsFail.ExitCode)")
    Assert-True ($capTagsFail.ErrorClass -eq 'REF_REJECTED') ("--tags class got $($capTagsFail.ErrorClass)")
    Assert-True ($capTagsFail.Record.push_phase -eq 'tags') 'tags phase not separated'
    Assert-True ($capAll.Record.push_phase -eq 'all') 'all phase not separated'
    $combinedErr = Get-GitPushErrLogLine -First $capAll -Second $capTagsFail
    Assert-True ($combinedErr -and $combinedErr.Trim().Length -gt 0) 'failing tags line dropped when --all succeeded'
    Assert-Schema $capTagsFail.Record 'tags-fail-record'

    # 6) github/wire channel kept separate (skip, not a heartbeat)
    Write-GitPushErrorRecord -RecordPath $records -Label 'github_wire' -ExitCode 0 -ErrorClass 'NONE' -ElapsedMs 0 -RedactedStderr 'probe_skipped: no github remote configured on F:\backup' -CycleId 'test-tags' -PushPhase 'github_wire' -RemoteClass 'absent' -TargetPathOrRedactedRemote '' -LockState 'held' | Out-Null

    $lines = @(Get-Content -LiteralPath $records)
    Assert-True ($lines.Count -ge 6) ("expected >=6 jsonl rows, got $($lines.Count)")
    $phases = @()
    foreach ($line in $lines) {
        $row = $line | ConvertFrom-Json
        Assert-Schema $row 'jsonl'
        $phases += [string]$row.push_phase
        $blob = $line
        Assert-True ($blob -notmatch 'ghp_') 'jsonl leaked ghp_'
        Assert-True ($blob -notmatch 's3cretValue') 'jsonl leaked password fixture'
        Assert-True ($blob -notmatch 'https://github.com') 'jsonl leaked github URL'
    }
    Assert-True ($phases -contains 'all') 'missing all phase'
    Assert-True ($phases -contains 'tags') 'missing tags phase'
    Assert-True ($phases -contains 'github_wire') 'missing github_wire phase'

    $prodScan = @($helper, (Join-Path $PSScriptRoot 'germline-hourly.ps1'))
    foreach ($p in $prodScan) {
        $txt = Get-Content -LiteralPath $p -Raw -ErrorAction Stop
        Assert-True ($txt -notmatch 'ghp_[A-Za-z0-9]{10,}') ("secret scan ghp_ in $p")
        Assert-True ($txt -notmatch 'github_pat_[A-Za-z0-9_]+') ("secret scan github_pat in $p")
        Assert-True ($txt -notmatch '(?i)(ghp|gho|github_pat)_[A-Za-z0-9]{20,}') ("secret scan long token in $p")
    }
    $jsonlAll = Get-Content -LiteralPath $records -Raw
    Assert-True ($jsonlAll -notmatch 'ghp_[A-Za-z0-9]{8,}') 'jsonl leaked ghp_ token shape'
    Assert-True ($jsonlAll -notmatch 's3cretValue') 'jsonl leaked password fixture'
    Assert-True ($jsonlAll -notmatch 'https://') 'jsonl leaked URL'
    Assert-True ($jsonlAll -notmatch 'username=alice') 'jsonl leaked username fixture'

    Write-Host ("nonzero class : {0}  exit={1}" -f $capFail.ErrorClass, $capFail.ExitCode)
    Write-Host ("success class : {0}  exit={1}" -f $capOk.ErrorClass, $capOk.ExitCode)
    Write-Host ("lock class    : {0}  exit={1}" -f $capLock.ErrorClass, $capLock.ExitCode)
    Write-Host ("tags class    : {0}  exit={1}" -f $capTagsFail.ErrorClass, $capTagsFail.ExitCode)
    Write-Host ("records       : {0}" -f $lines.Count)

    if ($errors.Count -gt 0) {
        Write-Host 'RESULT: FAIL'
        $errors | ForEach-Object { Write-Host "  - $_" }
        exit 1
    }
    Write-Host 'RESULT: PASS - capture, redact, classify, lock, tags-fail, schema'
    exit 0
}
finally {
    Remove-Item -Recurse -Force $work -ErrorAction SilentlyContinue
}
