$ErrorActionPreference = "SilentlyContinue"
function Get-Py([string]$match) {
    Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
        Where-Object { $_.CommandLine -like "*$match*" } |
        Select-Object -First 1
}
$c = Get-Py "cortex.py"
$d = Get-Py "brain.daemon"
$l = Get-Py "live\server.py"
$o = Get-Py "organism.py"
$out = [ordered]@{
    ts = (Get-Date).ToUniversalTime().ToString("s") + "Z"
    cortex = @{ pid = $(if ($c) { $c.ProcessId } else { $null }); cmd = $(if ($c) { $c.CommandLine } else { $null }) }
    daemon = @{ pid = $(if ($d) { $d.ProcessId } else { $null }); cmd = $(if ($d) { $d.CommandLine } else { $null }) }
    live   = @{ pid = $(if ($l) { $l.ProcessId } else { $null }); cmd = $(if ($l) { $l.CommandLine } else { $null }) }
    organism = @{ pid = $(if ($o) { $o.ProcessId } else { $null }); cmd = $(if ($o) { $o.CommandLine } else { $null }) }
    ports = @()
}
foreach ($p in 8771,8772,8773) {
    $t = Get-NetTCPConnection -LocalPort $p -State Listen | Select-Object -First 1
    $out.ports += @{ port = $p; pid = $(if ($t) { $t.OwningProcess } else { $null }) }
}
$dest = "F:\backup\06-EVIDENCE\NERVOUS-RECOVERY-2026-08-20\PROCESS-PIDS.json"
($out | ConvertTo-Json -Depth 6) | Set-Content -Encoding utf8 $dest
Write-Host "wrote $dest"
$out | ConvertTo-Json -Depth 6
