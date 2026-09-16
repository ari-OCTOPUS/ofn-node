# gap001_closure_verify.ps1 -- GAP-001 executable-closure verifier (TEMPLATE, laptop-side, read-only)
# Bundle : OCTOPUS World-Discovery Phase 1 (DISCOVERY-PHASE1-06) | 2026-08-18
# Ledger : board-checkpoint-ledger ONLY (see manifest homonym_warning -- Telegram GAP-001 is a different gap)
# Authority: reports and verifies. NEVER lifts WAVE0_OBSERVE_ONLY / GITWRITE-FAILED (owner-only per D14).
# Exit codes: 0 = CLOSED | 1 = report written, not closed (incl. PENDING_OWNER_SIGNATURE) | 2 = error
#
# Usage:
#   powershell -NoProfile -ExecutionPolicy Bypass -File _ops\world_discovery\gap001_closure_verify.ps1 `
#     -EvidenceDir "F:\backup\06-EVIDENCE\sensorium-d14-verify-2026-08-18" `
#     -RepoRoot "F:\backup" `
#     -ManifestPath "F:\backup\_ops\world_discovery\gap001-criteria.manifest.json"

param(
    [Parameter(Mandatory=$true)][string]$EvidenceDir,
    [Parameter(Mandatory=$true)][string]$RepoRoot,
    [string]$ManifestPath = '',
    [string]$OutDir = ''
)

$ErrorActionPreference = 'Stop'
if (-not $ManifestPath) { $ManifestPath = Join-Path $PSScriptRoot 'gap001-criteria.manifest.json' }
if (-not $OutDir) { $OutDir = Join-Path $EvidenceDir 'gap001-verify' }
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$RunId = 'gap001-' + (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')

# ---------------------------------------------------------------- guard ----
# This verifier is read-only by construction: file reads, hashing, JSON/regex
# parsing only. The allowlist below is enforced for ANY future probe command
# a manifest may declare -- nothing outside it may ever be invoked.
$script:Allowlist = @(
    '^(Get-Content|Get-ChildItem|Get-Item|Get-FileHash|Select-String|ConvertFrom-Json|Write-Output)\b'
)
$script:Blacklist = @(
    'ping\b','Test-Connection','Test-NetConnection','nmap','masscan','arp-scan','fping','hping3',
    'curl\b','wget\b','Invoke-WebRequest','Invoke-RestMethod','dig\b','host\b','nslookup','telnet','nc\b','netcat',
    'traceroute','tracert','ssh\b','scp\b','mosquitto','Wake-on-LAN','wol\b',
    'Remove-Item','rm\b','del\b','rd\b','Move-Item','mv\b','Copy-Item','cp\b','Clear-Content','Set-Content','Out-File','Add-Content',
    'Restart-Computer','Stop-Computer','Stop-Process','taskkill','kill\b','Shutdown','reboot',
    'schtasks','Register-ScheduledJob','Start-Process','Invoke-Command','Invoke-Expression','iex\b',
    'git\s+(push|pull|checkout|reset|clean)','systemctl','crontab','docker\b'
)
function Test-CommandAllowed([string]$Cmd) {
    foreach ($b in $script:Blacklist) { if ($Cmd -match $b) { return $false } }
    foreach ($a in $script:Allowlist) { if ($Cmd -match $a) { return $true } }
    return $false
}

# ------------------------------------------------------------- helpers -----
function Get-Sha256([string]$Path) {
    if (Test-Path -LiteralPath $Path) { return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLower() }
    return $null
}
function Resolve-JsonPath($Object, [string[]]$Segments) {
    # Assigns to $script:JsonPathValue instead of returning through the
    # pipeline: PowerShell unrolls empty arrays on function output, which
    # would erase a legitimate "gates_failed": [] into $null.
    $cur = $Object
    foreach ($seg in $Segments) {
        if ($null -eq $cur) { $script:JsonPathValue = $null; return }
        $prop = $cur.PSObject.Properties[$seg]
        if ($null -eq $prop) { $script:JsonPathValue = $null; return }
        $cur = $prop.Value
    }
    $script:JsonPathValue = $cur
}
function Test-Expectation($Value, [string]$Expect) {
    switch ($Expect) {
        'EXISTS'       { return ($null -ne $Value -and "$Value" -ne '') }
        'NOT_NULL'     { return ($null -ne $Value) }
        'EMPTY_ARRAY'  { return ($null -ne $Value -and $Value -is [System.Array] -and $Value.Count -eq 0) }
        default        { return ("$Value" -eq $Expect) }
    }
}

# --------------------------------------------------------- evaluators ------
function Invoke-Check([psobject]$C) {
    $r = [ordered]@{
        check_id = $C.id; kind = $C.kind; mandatory = [bool]$C.mandatory
        status = 'UNKNOWN'; evidence = $null; sha256 = $null; note = $null
        severity = $(if ($C.severity) { $C.severity } else { 'mandatory' })
    }
    switch ($C.kind) {

        'JSON_PATH' {
            $f = Join-Path $EvidenceDir $C.file
            if (-not (Test-Path -LiteralPath $f)) {
                $r.status = 'UNKNOWN'; $r.note = "missing evidence file: $($C.file)"; break
            }
            $r.evidence = $f; $r.sha256 = Get-Sha256 $f
            $json = Get-Content -LiteralPath $f -Raw | ConvertFrom-Json
            Resolve-JsonPath $json @($C.segments)
            $val = $script:JsonPathValue
            $shown = $(if ($null -eq $val) { 'null' } elseif ("$val" -eq '') { '<empty>' } else { "$val" })
            if (Test-Expectation $val $C.expect) {
                $r.status = 'PASS'; $r.note = "path=$($C.segments -join '.') value=$shown expect=$($C.expect)"
            } else {
                $r.status = 'FAIL'; $r.note = "path=$($C.segments -join '.') value=$shown expect=$($C.expect)"
            }
        }

        'FILE_REGEX' {
            $f = Join-Path $EvidenceDir $C.file
            if ($C.file -match '[\\/]') { $f = Join-Path $RepoRoot $C.file }   # repo-relative target
            if (-not (Test-Path -LiteralPath $f)) {
                $r.status = 'UNKNOWN'; $r.note = "missing target file: $($C.file)"; break
            }
            $r.evidence = $f; $r.sha256 = Get-Sha256 $f
            $hit = Select-String -LiteralPath $f -Pattern $C.pattern -SimpleMatch:$false | Select-Object -First 1
            $matched = ($null -ne $hit)
            if ($matched -eq [bool]$C.must_match) {
                $r.status = $(if ($C.documentary) { 'PASS_DOCUMENTED' } else { 'PASS' })
                $r.note = "pattern '$($C.pattern)' line $($hit.LineNumber): $($hit.Line.Trim())"
            } else {
                $r.status = 'FAIL'; $r.note = "pattern '$($C.pattern)' expected must_match=$($C.must_match), matched=$matched"
            }
        }

        'ARTIFACT_SEARCH' {
            # Filename-anchored only: broad content search over all evidence
            # false-matches (e.g. GAP-002's CLOSED_BY_SIGNED_CHECKPOINT note
            # sits within 400 chars of GAP-001 in ordinary evidence JSON).
            # A candidate counts ONLY if its name matches AND its content
            # contains every required string (closure + rider inside the
            # signed bundle itself, per D5/D6).
            $found = $null; $nearMisses = @()
            foreach ($rootRel in $C.roots) {
                $root = Join-Path $RepoRoot $rootRel
                if (-not (Test-Path -LiteralPath $root)) { continue }
                $candidates = Get-ChildItem -LiteralPath $root -Recurse -File -ErrorAction SilentlyContinue |
                    Where-Object { $_.Name -match $C.filename_regex -and $_.FullName -notmatch 'gap001-verify' }
                foreach ($cand in $candidates) {
                    $content = Get-Content -LiteralPath $cand.FullName -Raw -ErrorAction SilentlyContinue
                    $allPresent = $true
                    foreach ($req in @($C.require_content_all)) {
                        if ($content -notlike "*$req*") { $allPresent = $false; break }
                    }
                    if ($allPresent) { $found = $cand; break } else { $nearMisses += $cand.Name }
                }
                if ($found) { break }
            }
            if ($found) {
                $r.status = 'PASS'   # runtime artifact -- the only check class that can formalize closure
                $r.evidence = $found.FullName.Substring($RepoRoot.Length).TrimStart('\','/')
                $r.sha256 = Get-Sha256 $found.FullName
                $r.note = "signed-checkpoint artifact found: name /$($C.filename_regex)/ + content contains all of [$($C.require_content_all -join ', ')]"
            } else {
                $r.status = $C.on_miss   # UNKNOWN_PENDING per manifest
                $r.note = "no artifact under $($C.roots -join ',') matches /$($C.filename_regex)/ with content [$($C.require_content_all -join ', ')] -- closure not yet formalized by owner"
                if ($nearMisses.Count -gt 0) { $r.note += " (name-matched but content-incomplete: $($nearMisses -join ', ') - inspect before trusting)" }
            }
        }

        default { $r.status = 'UNKNOWN'; $r.note = "unknown check kind: $($C.kind)" }
    }
    return [pscustomobject]$r
}

# ---------------------------------------------------------------- main ------
try {
    if (-not (Test-Path -LiteralPath $ManifestPath)) { throw "manifest not found: $ManifestPath" }
    $manifest = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json

    if ($manifest.ledger_id -ne 'board-checkpoint-ledger') {
        throw "manifest ledger_id '$($manifest.ledger_id)' is not the board checkpoint ledger -- homonym guard tripped (Telegram-redesign GAP-001 evidence must never be fed to this verifier)."
    }

    $results = @()
    foreach ($c in $manifest.checks) { $results += @(Invoke-Check $c) }

    # verdict per manifest matrix
    $criteriaChecks  = $results | Where-Object { $_.mandatory -and $_.check_id -ne 'OWNER-SIGNED-CHECKPOINT' }
    $signedCheck     = $results | Where-Object { $_.check_id -eq 'OWNER-SIGNED-CHECKPOINT' }
    $criteriaHold    = (@($criteriaChecks | Where-Object { $_.status -in @('PASS','PASS_DOCUMENTED') }).Count -eq @($criteriaChecks).Count)
    $contradicted    = (@($results | Where-Object { $_.status -eq 'FAIL' -and $_.severity -ne 'informational' }).Count -gt 0)

    $verdict = 'NOT_CLOSED'; $reason = @()
    if ($contradicted) {
        $verdict = 'INTEGRITY_INCIDENT'
        $reason += 'one or more mandatory checks FAILED -- treat as integrity incident per D14: stop, report, await owner decision'
    } elseif ($criteriaHold -and $signedCheck.Status -eq 'PASS') {
        $verdict = 'CLOSED'
        $reason += 'all criteria hold AND owner-signed checkpoint artifact present (with rider check satisfied)'
    } elseif ($criteriaHold -and $signedCheck.Status -eq 'UNKNOWN_PENDING') {
        $verdict = 'PENDING_OWNER_SIGNATURE'
        $reason += 'criteria met per evidence (D5) but the owner-signed checkpoint formalizing GAP-001 CLOSED + rider POWER_LOSS_UNTESTED has not been captured under 06-EVIDENCE'
    } else {
        $verdict = 'NOT_CLOSED'
        foreach ($c in $criteriaChecks) { if ($c.status -notin @('PASS','PASS_DOCUMENTED')) { $reason += "$($c.check_id)=$($c.status)" } }
        if ($signedCheck.Status -eq 'FAIL') { $reason += 'OWNER-SIGNED-CHECKPOINT=FAIL' }
    }

    # integrity record of consumed inputs
    $inputs = @()
    foreach ($rel in @($ManifestPath, (Join-Path $EvidenceDir 'msg-evidence-latest.json'), (Join-Path $EvidenceDir 'OWNER-DECISIONS.md'))) {
        $h = Get-Sha256 $rel
        if ($h) { $inputs += @{ path = $rel; sha256 = $h } }
    }

    $report = [ordered]@{
        schema     = 'octopus:world_discovery:gap001-closure-report:v1'
        run_id     = $RunId
        gap_id     = 'GAP-001'
        ledger_id  = $manifest.ledger_id
        ran_on     = 'LAPTOP-191'
        read_only  = $true
        packets_injected = 0
        flags_lifted = $false
        verdict    = $verdict
        reasons    = $reason
        structural_gate_note = 'WAVE0_OBSERVE_ONLY + GITWRITE-FAILED retention stays in force regardless of this verdict; only the owner lifts it (D14).'
        checks     = $results
        integrity_inputs = $inputs
        canonical_definition = $manifest.canonical_definition
    }
    $jsonPath = Join-Path $OutDir ("GAP001-CLOSURE-REPORT-$RunId.json")
    ($report | ConvertTo-Json -Depth 8) | Set-Content -LiteralPath $jsonPath -Encoding UTF8
    $outSha = Get-Sha256 $jsonPath

    # human summary
    $lines = @()
    $lines += "# GAP-001 Executable-Closure Report ($RunId)"
    $lines += ""
    $lines += "Ledger: $($manifest.ledger_id) | Ran on: LAPTOP-191 | read-only, zero network, no flags touched"
    $lines += "Canonical definition: $($manifest.canonical_definition)"
    $lines += ""
    $lines += "| check | status | note |"
    $lines += "|---|---|---|"
    foreach ($c in $results) { $lines += "| $($c.check_id) | $($c.status) | $($c.note) |" }
    $lines += ""
    $lines += "## VERDICT: $verdict"
    foreach ($rzn in $reason) { $lines += "- $rzn" }
    $lines += ""
    $lines += "Report: $jsonPath (sha256 $outSha)"
    $lines += "Structural gate: untouched -- WAVE0_OBSERVE_ONLY + GITWRITE-FAILED stays until the OWNER formalizes closure (D14)."
    $mdPath = Join-Path $OutDir ("GAP001-CLOSURE-REPORT-$RunId.md")
    ($lines -join "`r`n") | Set-Content -LiteralPath $mdPath -Encoding UTF8

    Write-Output "VERDICT: $verdict"
    Write-Output "JSON: $jsonPath"
    Write-Output "MD  : $mdPath"
    if ($verdict -eq 'CLOSED') { exit 0 } else { exit 1 }
}
catch {
    Write-Error "GAP-001 verifier error: $_"
    exit 2
}
