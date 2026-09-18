param([string]$PacketRoot = (Split-Path $PSScriptRoot -Parent), [switch]$CheckOriginals)
$ErrorActionPreference='Stop'
$rootFull=[System.IO.Path]::GetFullPath($PacketRoot).TrimEnd('\','/')
function Resolve-PacketPath([string]$relative){
    if([System.IO.Path]::IsPathRooted($relative)){throw 'Absolute path in packet manifest'}
    $full=[System.IO.Path]::GetFullPath((Join-Path $rootFull $relative))
    if(!$full.StartsWith($rootFull+[System.IO.Path]::DirectorySeparatorChar,[System.StringComparison]::OrdinalIgnoreCase)){throw 'Path outside packet'}
    return $full
}
$index=Get-Content -Raw -LiteralPath (Join-Path $rootFull 'SOURCE-INDEX.json')|ConvertFrom-Json
$manifest=Get-Content -Raw -LiteralPath (Join-Path $rootFull 'ARTIFACT-MANIFEST.json')|ConvertFrom-Json
$errors=@();$drift=@();$parsed=0
foreach($item in $manifest.files){
    $path=Resolve-PacketPath $item.path
    if(!(Test-Path -LiteralPath $path -PathType Leaf)){$errors+='Missing artifact: '+$item.path;continue}
    if((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $item.sha256){$errors+='Hash mismatch: '+$item.path}
    if($item.path.EndsWith('.json')){try{Get-Content -Raw -LiteralPath $path|ConvertFrom-Json|Out-Null;$parsed++}catch{$errors+='JSON parse failed: '+$item.path}}
}
foreach($item in $index.sources){
    $path=Resolve-PacketPath $item.snapshot_path
    if((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $item.sha256){$errors+='Source snapshot mismatch: '+$item.id}
    if($CheckOriginals){
        if(!(Test-Path -LiteralPath $item.original_path -PathType Leaf)){$drift+='Source unavailable: '+$item.id}
        elseif((Get-FileHash -LiteralPath $item.original_path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $item.sha256){$drift+='Source changed: '+$item.id}
    }
}
if(@($index.internal_references|Where-Object {!$_.match}).Count){$errors+='Unresolved embedded source hash mismatch'}
$state=Get-Content -Raw -LiteralPath (Join-Path $rootFull 'CURRENT-STATE.json')|ConvertFrom-Json
if($state.overall -ne 'OPEN' -or $state.live_runtime_verified -ne $false){$errors+='Handoff must retain OPEN / local-only scope'}
if(($state.roles.node|Sort-Object) -join ',' -ne '100,114,138,160,180,182,193'){$errors+='Wrong seven-node role denominator'}
if(($state.npus.rows.node|Sort-Object) -join ',' -ne '100,114,138,160,180,182,193'){$errors+='Wrong seven-node NPU denominator'}
if($state.governance.customer_send -ne 'HOLD' -or $state.governance.may_authorize -ne $false){$errors+='Governance marker mismatch'}
$result=[ordered]@{scope='PACKET_INTEGRITY_AND_JSON_PARSE_ONLY';runtime_tested=$false;status=$(if($errors.Count){'FAIL'}else{'PASS'});artifact_count=$manifest.files.Count;source_count=$index.sources.Count;json_files_parsed=$parsed;errors=$errors;original_source_drift=$drift;drift_does_not_rewrite_snapshot=$true;checked_utc=[DateTime]::UtcNow.ToString('o')}
$result|ConvertTo-Json -Depth 6
if($errors.Count){exit 1}
