<#
.SYNOPSIS
  Staged, reversible deploy of the canonical octopus tree to the LIVE working tree F:\backup.
  DEFAULT = DRY-RUN. Nothing mutates the live system unless BOTH -Apply and -IUnderstand are given.

.DESCRIPTION
  Owner-gated. This script does NOT activate the organism. It:
    * snapshots the live tree (git bundle + untracked-work copy) to a snapshot root,
    * fast-forwards / checks out the live working tree to the canonical SHA,
    * ensures the 8 ACTIVATION-*.flag levers are ABSENT (paid/live gates closed),
    * verifies deployed launcher/watchdog artifacts contain zero "del STOP-ORGANISM",
    * registers the tg-center watchdog scheduled task (via the D5 script, -Apply),
    * restarts ONLY cortex(8772) and cockpit(8773); organism(8771) stays DOWN.

  HARD INVARIANTS (the script aborts rather than violate any):
    * STOP-ORGANISM (the owner kill-switch, an UNTRACKED runtime file) is never read-mutated,
      moved, or deleted. Its SHA-256 is recorded before and after and must match.
    * The organism (port 8771) must be DOWN before and after. If it is UP, ABORT.
    * No Telegram poller is started. No outward flag is enabled.
    * If the live tree has conflicting tracked modifications the checkout cannot safely
      apply, ABORT (the owner must triage the live tree's uncommitted work first).

  This script is the DEPLOY step only. ACTIVATION (removing STOP-ORGANISM + restarting the
  organism + enabling core flags) is a SEPARATE runbook and a separate owner vote:
  see ACTIVATION-RUNBOOK-2026-07-21.md. This script never does that.

.PARAMETER TargetSha
  Canonical commit to deploy. Default: the tip of the local 'master' (verified == germline).

.PARAMETER Apply
  Perform actions. Without it, every step is printed as "[DRY-RUN] would ...".

.PARAMETER IUnderstand
  Second required confirmation. -Apply alone stays dry-run; -Apply -IUnderstand acts.

.NOTES
  Expected STOP-ORGANISM sha256 (owner kill-switch, 2026-07-19):
    C8FE7176514E3DA8629DBF0A4C411D2909138EDE12C2739C2F8E8D43295CD099
#>
[CmdletBinding()]
param(
  [string]$LiveRoot     = 'F:\backup',
  [string]$SnapshotRoot = 'E:\deploy-snapshots',
  [string]$TargetSha    = '',
  [switch]$Apply,
  [switch]$IUnderstand
)

$ErrorActionPreference = 'Stop'
$EXPECTED_STOP_SHA = 'C8FE7176514E3DA8629DBF0A4C411D2909138EDE12C2739C2F8E8D43295CD099'
$STOP = Join-Path $LiveRoot '_ops\STOP-ORGANISM'
$ACT_FLAGS = @(
  'ACTIVATION-CORTEX-PAID.flag','ACTIVATION-DEBATE.flag','ACTIVATION-GO-LIVE.flag',
  'ACTIVATION-HEART-DOCTOR.flag','ACTIVATION-PULSE.flag','ACTIVATION-RESEARCH-EARLY.flag',
  'ACTIVATION-SELF-IMPROVE-AUTO.flag','ACTIVATION-WORK-LLM.flag'
)
$DoIt = $Apply -and $IUnderstand
function Step($msg) { if ($DoIt) { Write-Host "[APPLY]   $msg" } else { Write-Host "[DRY-RUN] would $msg" } }
function Note($msg) { Write-Host "          $msg" }
function Abort($msg){ Write-Error "ABORT: $msg"; exit 1 }

Write-Host "=== octopus deploy-to-live ($(if($DoIt){'APPLY'}else{'DRY-RUN'})) ===" -ForegroundColor Cyan

# --- 0. preconditions -------------------------------------------------------
if (-not (Test-Path $STOP)) {
  Abort "STOP-ORGANISM absent - deploy assumes the organism is halted. Do NOT deploy into a live organism."
}
$stopHashBefore = (Get-FileHash -Algorithm SHA256 $STOP).Hash
if ($stopHashBefore -ne $EXPECTED_STOP_SHA) {
  Abort "STOP-ORGANISM sha256 mismatch (got $stopHashBefore). Refusing to touch a tree whose kill-switch is not the expected owner marker."
}
Note "STOP-ORGANISM verified: $stopHashBefore"

$org = Get-NetTCPConnection -State Listen -LocalPort 8771 -ErrorAction SilentlyContinue
if ($org) { Abort "organism port 8771 is LISTENING - organism appears UP. Deploy requires it DOWN." }
Note "organism 8771: DOWN (ok)"

Push-Location $LiveRoot
try {
  $liveHead = (git rev-parse HEAD).Trim()
  if (-not $TargetSha) { $TargetSha = (git rev-parse master).Trim() }
  Note "live HEAD:  $liveHead"
  Note "target SHA: $TargetSha"

  # live tree cleanliness (2026-07-21 fix): only TRACKED modifications block the checkout --
  # they are what a checkout can clobber. Untracked files are PRESERVED by checkout (see step 2),
  # and STOP-ORGANISM itself is a REQUIRED untracked file, so gating on the full porcelain
  # output could never pass while the kill-switch exists.
  $dirtyTracked = @(git status --porcelain --untracked-files=no)
  $dirtyAll     = @(git -c core.quotePath=false status --porcelain)
  if ($dirtyTracked.Count) {
    Note "LIVE TREE HAS TRACKED MODIFICATIONS - these would be clobbered by checkout:"
    $dirtyTracked | ForEach-Object { Note "  $_" }
    if ($DoIt) {
      Abort "Refusing to checkout over tracked modifications. Commit them to a backup branch first (git add -u on a backup/pre-deploy-* branch), then re-run. (This is the owner-supervised triage step.)"
    }
  } elseif ($dirtyAll.Count) {
    Note ("untracked-only dirt: " + $dirtyAll.Count + " entries (preserved on disk by checkout; copied to snapshot below)")
  }

  # --- 1. snapshot (always safe; runs even in dry-run so a rollback substrate exists) ---
  $stamp = (git rev-parse --short HEAD).Trim()
  $snapDir = Join-Path $SnapshotRoot ("live-" + $stamp)
  Step "create snapshot dir $snapDir"
  if ($DoIt) { New-Item -ItemType Directory -Force -Path $snapDir | Out-Null }
  Step "git bundle live repo -> $snapDir\live.bundle"
  if ($DoIt) { git bundle create (Join-Path $snapDir 'live.bundle') --all }
  Step "copy untracked runtime work (personal\, _ops\state\, uncommitted _ops code) -> $snapDir"
  if ($DoIt) {
    # quotePath=false keeps non-ASCII paths raw; strip any remaining surrounding quotes.
    # -Recurse so untracked DIRECTORIES are copied with contents (was silently empty before).
    # Skip _git_tmp_obj_quarantine* (repo-object junk from a past incident; the bundle already
    # holds all repo data) and .fuse_hidden* lock artifacts.
    git -c core.quotePath=false status --porcelain | ForEach-Object { ($_ -replace '^...','').Trim('"') } |
      Where-Object { $_ -and $_ -notmatch '_git_tmp_obj_quarantine|\.fuse_hidden' } | ForEach-Object {
        $src = Join-Path $LiveRoot $_
        if (Test-Path $src) {
          $dst = Join-Path $snapDir ("worktree\" + $_)
          New-Item -ItemType Directory -Force -Path (Split-Path $dst) | Out-Null
          Copy-Item $src $dst -Force -Recurse -ErrorAction SilentlyContinue
        }
      }
  }
  Step "checksum snapshot"
  # exclude checksums.csv itself: hashing the file the pipeline is writing self-locks (2026-07-21).
  if ($DoIt) { Get-ChildItem -Recurse -File $snapDir | Where-Object { $_.Name -ne 'checksums.csv' } | Get-FileHash -Algorithm SHA256 | Export-Csv (Join-Path $snapDir 'checksums.csv') -NoTypeInformation }

  # --- 2. deploy code (checkout tracked tree; UNTRACKED live files are preserved by git) ---
  Step "git fetch germline"
  if ($DoIt) { git fetch germline --quiet }
  Step "checkout live working tree to $TargetSha (tracked files only; untracked live files preserved)"
  if ($DoIt) {
    # switch the live tree onto the canonical branch at TargetSha. checkout keeps untracked files
    # UNLESS an untracked path is tracked in the target tree - pre-flight those loudly, because
    # a raw checkout failure under EAP=Stop dies as an opaque NativeCommandError (2026-07-21).
    $targetSet = @{}
    git -c core.quotePath=false ls-tree -r --name-only $TargetSha | ForEach-Object { $targetSet[$_] = $true }
    $collide = @(git -c core.quotePath=false ls-files --others --exclude-standard | Where-Object { $targetSet.ContainsKey($_) })
    if ($collide.Count) {
      $collide | ForEach-Object { Note ("  COLLIDES: " + $_) }
      Abort ("untracked live files collide with the target tree (" + $collide.Count + " above); MOVE them aside (e.g. into the snapshot's collisions\ dir - never delete) and re-run.")
    }
    # PS5.1: never 2>&1-redirect native git under EAP=Stop (stderr becomes a terminating
    # NativeCommandError). Relax, capture for the log, then verify by observed state.
    $ErrorActionPreference = 'Continue'
    $coOut = git checkout master 2>&1
    $ErrorActionPreference = 'Stop'
    $coOut | ForEach-Object { Note ("  git: " + $_) }
    if ((git rev-parse --abbrev-ref HEAD).Trim() -ne 'master') {
      Abort "checkout of master failed (see git output above; is master checked out in another worktree?) - live tree unchanged."
    }
    $ErrorActionPreference = 'Continue'
    $mgOut = git merge --ff-only $TargetSha 2>&1
    $mergeExit = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    $mgOut | ForEach-Object { Note ("  git: " + $_) }
    if ($mergeExit -ne 0) { Abort "ff-only merge to target failed - master diverged; owner triage required." }
  }

  # --- 3. ensure ALL activation levers are PHYSICALLY ABSENT (paid/live gates closed) ---
  # NOTE (2026-07-21 audit): git rm --cached (D2) untracked these but KEPT the working-tree
  # copies; a fresh checkout from ec64568 no longer contains them, but the live tree at a2183c3
  # tracks+carries them, so we delete recursively (catch-all, not just the 8 named) + verify.
  Step "back up then RECURSIVELY delete every _ops\ACTIVATION-*.flag from the live tree"
  if ($DoIt) {
    $flags = @(Get-ChildItem -Path (Join-Path $LiveRoot '_ops') -Filter 'ACTIVATION-*.flag' -File -ErrorAction SilentlyContinue)
    if ($flags.Count) {
      $flagBackup = Join-Path $snapDir 'activation-flags-backup'
      New-Item -ItemType Directory -Force -Path $flagBackup | Out-Null
      $flags | ForEach-Object { Copy-Item $_.FullName -Destination $flagBackup -Force; Note ("  backed up + will delete: " + $_.Name) }
      $flags | Remove-Item -Force
    }
    $remain = @(Get-ChildItem -Path (Join-Path $LiveRoot '_ops') -Filter 'ACTIVATION-*.flag' -File -ErrorAction SilentlyContinue)
    if ($remain.Count) { Abort ("activation levers still present after removal: " + (($remain | ForEach-Object Name) -join ', ')) }
    Note ("activation levers removed: " + $flags.Count + " (paid/live gates now closed by absence)")
  }

  # --- 3b. VERIFY paid_gate() is CLOSED post-removal (independent check; auto-rollback if OPEN) ---
  Step "verify model_router.paid_gate() == CLOSED"
  if ($DoIt) {
    $py = "import sys; sys.path[:0]=[r'" + (Join-Path $LiveRoot '_ops') + "', r'" + (Join-Path $LiveRoot '_ops\cortex') + "', r'" + (Join-Path $LiveRoot '_ops\budget') + "']; import model_router as m; ok,why=m.paid_gate(); print('OPEN' if ok else 'CLOSED')"
    $gate = (& python -X utf8 -c $py 2>&1 | Select-Object -Last 1)
    Note ("paid_gate = " + $gate)
    if ("$gate" -notmatch 'CLOSED') {
      Write-Host "FATAL: paid_gate is not CLOSED after flag removal - rolling back." -ForegroundColor Red
      & (Join-Path $PSScriptRoot 'rollback-from-snapshot.ps1') -SnapshotDir $snapDir -Apply -IUnderstand
      Abort "paid_gate OPEN post-deploy; rollback invoked."
    }
  }

  # --- 4. verify no launcher/watchdog deploys a STOP-ORGANISM deletion ---
  Step "grep deployed launchers/watchdogs for 'del ... STOP-ORGANISM'"
  if ($DoIt) {
    $bad = Select-String -Path (Join-Path $LiveRoot '_ops\*.bat'),(Join-Path $LiveRoot '_ops\*.ps1'),(Join-Path $LiveRoot '04 - Architect System\scripts\*.ps1') -Pattern 'del\s+.*STOP-ORGANISM','Remove-Item.*STOP-ORGANISM' -ErrorAction SilentlyContinue
    if ($bad) { Abort ("a deployed artifact deletes STOP-ORGANISM: " + ($bad.Path -join ', ')) }
  }
  Note "no deployed artifact deletes STOP-ORGANISM (ok)"

  # --- 5. watchdog content is auto-updated by the checkout; DO NOT register tg-center here ---
  # DEFERRED TO ACTIVATION (2026-07-21 fix): register-tg-center-watchdog.ps1 schedules a task
  # that REVIVES center.py (a Telegram poller). Registering it during DEPLOY would try to start
  # a poller every 5 min -- violating the deploy invariant "Telegram pollers remain DOWN" (and it
  # would use the not-yet-rotated .env token). The twin/cortex/live watchdog SOURCE is already
  # refreshed by the step-2 checkout (they read the updated .ps1 on their next fire); no
  # registration is needed for those. tg-center watchdog registration belongs in the ACTIVATION
  # runbook, after token rotation. Deploy leaves the TG surface fully down.
  Note "tg-center watchdog registration DEFERRED to activation (would start a poller); skipped."

  # --- 6. controlled restart of cortex(8772) + cockpit(8773) ONLY ---
  Step "restart cortex 8772 (kill-by-port + relaunch RUN-CORTEX.bat detached)"
  Step "restart cockpit 8773 (kill-by-port + relaunch run-live-headless.bat detached)"
  if ($DoIt) {
    foreach ($pc in @(@{port=8772; bat='_ops\RUN-CORTEX.bat'}, @{port=8773; bat='_ops\run-live-headless.bat'})) {
      $conn = Get-NetTCPConnection -State Listen -LocalPort $pc.port -ErrorAction SilentlyContinue
      if ($conn) { $conn.OwningProcess | Sort-Object -Unique | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue } }
      Start-Process -FilePath (Join-Path $LiveRoot $pc.bat) -WorkingDirectory (Join-Path $LiveRoot '_ops') -WindowStyle Hidden
    }
  }

  # --- 7. post-deploy probes ---
  Step "probe: 8771 down, 8772/8773 up, STOP unchanged, no poller"
  if ($DoIt) {
    Start-Sleep -Seconds 6
    $p71 = Get-NetTCPConnection -State Listen -LocalPort 8771 -ErrorAction SilentlyContinue
    $p72 = Get-NetTCPConnection -State Listen -LocalPort 8772 -ErrorAction SilentlyContinue
    $p73 = Get-NetTCPConnection -State Listen -LocalPort 8773 -ErrorAction SilentlyContinue
    $stopHashAfter = (Get-FileHash -Algorithm SHA256 $STOP).Hash
    Note ("8771(down?)=" + [bool]!$p71 + " 8772(up?)=" + [bool]$p72 + " 8773(up?)=" + [bool]$p73)
    Note ("STOP sha before/after: $stopHashBefore / $stopHashAfter")
    if ($p71)                              { Abort "organism 8771 came UP after deploy - this must never happen here." }
    if ($stopHashAfter -ne $EXPECTED_STOP_SHA) { Abort "STOP-ORGANISM changed during deploy." }
    Write-Host "=== deploy OK - organism DOWN, STOP intact, cortex/cockpit on canonical code ===" -ForegroundColor Green
  } else {
    Write-Host "=== DRY-RUN complete - no live change. Re-run with -Apply -IUnderstand to execute. ===" -ForegroundColor Yellow
  }
}
finally { Pop-Location }
