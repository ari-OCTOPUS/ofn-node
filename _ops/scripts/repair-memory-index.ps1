# repair-memory-index.ps1 -- self-heal the agent memory index (MEMORY.md)
# Owner ruling 2026-09-02 (ruling 7, ECONOMIC-LEARNING-RULINGS-2026-09-02):
# MEMORY.md is NOT the source of truth; the per-fact .md files are. This script
# appends MISSING index entries (derived from each file's frontmatter) and never
# rewrites or removes existing hand-written lines. Idempotent. Dry-run by default.
# ASCII-only on purpose: PS 5.1 mangles un-BOM'd UTF-8 scripts.

param(
    [string]$MemoryDir = "$env:USERPROFILE\.zcode\cli\memories\projects\project-9ee5fdeb26688fae\memory",
    [switch]$Apply
)

$ErrorActionPreference = 'Stop'
$indexPath = Join-Path $MemoryDir 'MEMORY.md'
if (-not (Test-Path $indexPath)) {
    Write-Output "INDEX MISSING: $indexPath -- recreating header only"
    if ($Apply) { Set-Content -Path $indexPath -Value '# Memory Index' -Encoding UTF8 }
    return
}

$existing = Get-Content $IndexPath -Encoding UTF8
$knownFiles = @()
foreach ($line in $existing) {
    if ($line -match '^\s*-\s*\[.*?\]\((.+?\.md)\)') { $knownFiles += $Matches[1] }
}

$missing = @()
Get-ChildItem -Path $MemoryDir -Filter '*.md' | Where-Object { $_.Name -ne 'MEMORY.md' } | ForEach-Object {
    if ($knownFiles -contains $_.Name) { return }
    $name = $null; $desc = $null
    foreach ($line in (Get-Content $_.FullName -Encoding UTF8 -TotalCount 15)) {
        if ($line -match '^name:\s*(.+)$') { $name = $Matches[1].Trim() }
        if ($line -match '^description:\s*(.+)$') { $desc = $Matches[1].Trim() }
        if ($name -and $desc) { break }
    }
    if (-not $name) { $name = $_.BaseName }
    if (-not $desc) { $desc = '(no description in frontmatter -- repair manually)' }
    $hook = $desc; if ($hook.Length -gt 180) { $hook = $hook.Substring(0, 180) + '...' }
    $missing += "- [$name]($($_.Name)) - $hook"
}

$orphanEntries = @($knownFiles | Where-Object { -not (Test-Path (Join-Path $MemoryDir $_)) })
$fileCount = @(Get-ChildItem -Path $MemoryDir -Filter '*.md' | Where-Object { $_.Name -ne 'MEMORY.md' }).Count

Write-Output "index: $indexPath"
Write-Output "entries now: $(@($knownFiles).Count) / memory files: $fileCount"
Write-Output "missing entries: $(@($missing).Count)"
$missing | ForEach-Object { Write-Output "  + $_" }
Write-Output "entries pointing to missing files: $(@($orphanEntries).Count)"
$orphanEntries | ForEach-Object { Write-Output "  ? $_" }

if (-not $Apply) { Write-Output '(dry run -- pass -Apply to append missing entries)'; return }
if ($missing.Count -gt 0) {
    Add-Content -Path $indexPath -Value ''
    Add-Content -Path $indexPath -Value $missing
    Write-Output "APPENDED $($missing.Count) entries"
}
# orphaned/duplicate entries are REPORTED only -- removal stays a human decision
