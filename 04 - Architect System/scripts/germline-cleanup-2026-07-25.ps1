# germline-cleanup-2026-07-25.ps1
# One-time cleanup of E:\germline after the owner verdict 2026-07-25:
#   "backup must be OVERWRITTEN, not accumulate."
#
# Retention chosen by owner: 1 rolling daily (vault-latest.bundle) + 1 rolling hourly
# (hourly-latest.bundle). Everything timestamped is legacy and goes.
#
# SAFE BY DEFAULT: this script only REPORTS. It deletes nothing unless you pass -Apply.
#   Report only :  powershell -ExecutionPolicy Bypass -File .\germline-cleanup-2026-07-25.ps1
#   Do it       :  powershell -ExecutionPolicy Bypass -File .\germline-cleanup-2026-07-25.ps1 -Apply
#   Also fix ACL:  ... -Apply -FixPerms      (run this one from an ADMIN PowerShell)
#
# NEVER touches F:\backup (the live vault) and never touches E:\germline\vault.git
# (the live push target).

param(
    [switch]$Apply,
    [switch]$FixPerms
)

$ErrorActionPreference = "Stop"
$OFFBOX  = "E:\germline"
$PROTECT = @("vault.git", "hourly-latest.bundle", "vault-latest.bundle",
             "hourly.log", "hourly-state.json", "last_backup_manifest.json",
             "state-latest", "state-hourly")

function Size-Of($path) {
    if (Test-Path $path -PathType Leaf) { return (Get-Item $path).Length }
    if (Test-Path $path -PathType Container) {
        $s = (Get-ChildItem $path -Recurse -File -ErrorAction SilentlyContinue |
              Measure-Object -Property Length -Sum).Sum
        if (-not $s) { return 0 }
        return $s
    }
    return 0
}
function MB($b) { "{0,9:N1} MB" -f ($b / 1MB) }

if (-not (Test-Path $OFFBOX)) { throw "OFFBOX not found: $OFFBOX" }

Write-Host ""
Write-Host "=== germline cleanup ===  mode: $(if($Apply){'APPLY (will delete)'}else{'REPORT ONLY'})"
Write-Host ""

$plan = @()   # @{ Path; Why; Bytes; Action }

# --- 1) daily bundles: keep the newest, rename it to the rolling name, drop the rest ---
# Sort by NAME, not LastWriteTime: the date is embedded in the filename
# (vault-YYYY-MM-DD_HHMM.bundle) and lexicographic order on ISO dates is correct.
# mtime can be rewritten by a copy, an AV scan or a restore - the name cannot.
$dailies = @(Get-ChildItem $OFFBOX -Filter "vault-2*.bundle" -File -ErrorAction SilentlyContinue |
             Sort-Object Name -Descending)
if ($dailies.Count -gt 0) {
    $keep = $dailies[0]
    # SAFETY: never delete a set of good bundles to keep a truncated one. If the newest is
    # much smaller than the biggest of the others, something is wrong - report and skip.
    $others = @($dailies | Select-Object -Skip 1)
    $biggestOther = 0
    foreach ($o in $others) { if ($o.Length -gt $biggestOther) { $biggestOther = [int64]$o.Length } }
    if ($biggestOther -and $keep.Length -lt ($biggestOther * 0.5)) {
        Write-Host ("  !! SKIPPING daily pruning: newest ({0}, {1}) is under half the size of the largest other ({2}). Investigate before deleting anything." `
                    -f $keep.Name, (MB $keep.Length), (MB $biggestOther)) -ForegroundColor Red
    } else {
        $plan += [pscustomobject]@{ Path = $keep.FullName; Why = "newest daily -> promote to vault-latest.bundle";
                    Bytes = $keep.Length; Action = "PROMOTE" }
        foreach ($b in ($dailies | Select-Object -Skip 1)) {
            $plan += [pscustomobject]@{ Path = $b.FullName; Why = "older daily bundle (retention = 1 rolling)";
                        Bytes = $b.Length; Action = "DELETE" }
        }
    }
}

# --- 2) orphan one-off bundles (not part of any rotation) ---
foreach ($b in @(Get-ChildItem $OFFBOX -Filter "*.bundle" -File -ErrorAction SilentlyContinue)) {
    if ($PROTECT -contains $b.Name) { continue }
    if ($b.Name -like "vault-2*") { continue }          # handled above
    $plan += [pscustomobject]@{ Path = $b.FullName; Why = "orphan one-off bundle, not in any rotation";
                Bytes = $b.Length; Action = "DELETE" }
}

# --- 3) stale duplicate bare repos (vault.git is protected and never listed) ---
foreach ($d in @(Get-ChildItem $OFFBOX -Directory -Filter "*.git" -ErrorAction SilentlyContinue)) {
    if ($PROTECT -contains $d.Name) { continue }
    $ageD = [math]::Round(((Get-Date) - $d.LastWriteTime).TotalDays, 1)
    $plan += [pscustomobject]@{ Path = $d.FullName; Why = "duplicate bare repo, idle $ageD days (vault.git is the live target)";
                Bytes = (Size-Of $d.FullName); Action = "DELETE" }
}

# --- 4) timestamped state folders: keep newest as state-latest, drop the rest ---
$states = @(Get-ChildItem $OFFBOX -Directory -Filter "state-2*" -ErrorAction SilentlyContinue |
            Sort-Object Name -Descending)   # name carries the ISO date; see note above
if ($states.Count -gt 0) {
    $plan += [pscustomobject]@{ Path = $states[0].FullName; Why = "newest state snapshot -> promote to state-latest";
                Bytes = (Size-Of $states[0].FullName); Action = "PROMOTE-DIR" }
    foreach ($s in ($states | Select-Object -Skip 1)) {
        $plan += [pscustomobject]@{ Path = $s.FullName; Why = "older state snapshot (retention = 1 rolling)";
                    Bytes = (Size-Of $s.FullName); Action = "DELETE" }
    }
}

# --- 5) orphan build artifacts left on the SYSTEM drive by crashed runs ---
foreach ($t in @(Get-ChildItem $env:TEMP -Filter "*germline*" -ErrorAction SilentlyContinue) +
               @(Get-ChildItem $env:TEMP -Filter "vault-2*.bundle" -File -ErrorAction SilentlyContinue)) {
    $plan += [pscustomobject]@{ Path = $t.FullName; Why = "orphan build artifact on system drive (%TEMP%)";
                Bytes = (Size-Of $t.FullName); Action = "DELETE" }
}

# ---------------- report ----------------
$del = @($plan | Where-Object { $_.Action -eq "DELETE" })
$freed = 0
foreach ($d in $del) { $freed += [int64]$d.Bytes }

foreach ($p in $plan) {
    $tag = switch ($p.Action) { "DELETE" { "delete " } "PROMOTE" { "rename " } "PROMOTE-DIR" { "rename " } }
    Write-Host ("  {0} {1}  {2}" -f $tag, (MB $p.Bytes), (Split-Path $p.Path -Leaf))
    Write-Host ("            -> {0}" -f $p.Why) -ForegroundColor DarkGray
}
Write-Host ""
Write-Host ("  reclaimed: {0}   ({1} item(s) to delete)" -f (MB $freed), $del.Count) -ForegroundColor Cyan
Write-Host ""

if (-not $Apply) {
    Write-Host "REPORT ONLY - nothing was changed. Re-run with -Apply to execute." -ForegroundColor Yellow
    exit 0
}

# ---------------- apply ----------------
foreach ($p in $plan) {
    switch ($p.Action) {
        "DELETE" {
            Remove-Item $p.Path -Recurse -Force
            Write-Host ("  deleted  {0}" -f (Split-Path $p.Path -Leaf))
        }
        "PROMOTE" {
            $dst = Join-Path $OFFBOX "vault-latest.bundle"
            if (Test-Path $dst) { Remove-Item $dst -Force }
            Move-Item -Force $p.Path $dst
            Write-Host ("  promoted {0} -> vault-latest.bundle" -f (Split-Path $p.Path -Leaf))
        }
        "PROMOTE-DIR" {
            $dst = Join-Path $OFFBOX "state-latest"
            if (Test-Path $dst) { Remove-Item $dst -Recurse -Force }
            Move-Item -Force $p.Path $dst
            Write-Host ("  promoted {0} -> state-latest" -f (Split-Path $p.Path -Leaf))
        }
    }
}

# ---------------- optional: fix the INC-2 root cause ----------------
# The hourly log shows: "remote: error: unable to write file
# E:/germline/vault.git/./objects/tmp_objdir-incoming-.../...: Permission denied"
# i.e. the account the Scheduled Task runs as cannot write into the bare repo, so every
# run falls back to a full ~250MB bundle. Granting Modify to SYSTEM + Users fixes it.
# SIDs are used instead of names so this works on a non-English Windows too.
if ($FixPerms) {
    Write-Host ""
    Write-Host "  fixing ACLs on $OFFBOX (needs an elevated PowerShell)..."
    icacls $OFFBOX /grant "*S-1-5-18:(OI)(CI)M" /T /C | Out-Null   # SYSTEM
    icacls $OFFBOX /grant "*S-1-5-32-545:(OI)(CI)M" /T /C | Out-Null # BUILTIN\Users
    Write-Host "  ACLs updated. Next hourly run should log 'OK push' instead of 'bundle-fallback'."
}

$after = (Get-ChildItem $OFFBOX -Recurse -File -ErrorAction SilentlyContinue |
          Measure-Object -Property Length -Sum).Sum
Write-Host ""
Write-Host ("[OK] cleanup done. E:\germline is now {0}" -f (MB $after)) -ForegroundColor Green
Write-Host "     From here on both layers overwrite in place - size stays flat."
Write-Host "     Verify tomorrow:  Get-Content E:\germline\hourly.log -Tail 5"
