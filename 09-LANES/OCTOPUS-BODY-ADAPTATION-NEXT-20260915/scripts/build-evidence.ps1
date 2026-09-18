param([string]$PacketRoot = (Split-Path $PSScriptRoot -Parent))
$ErrorActionPreference = 'Stop'
$utf8 = New-Object System.Text.UTF8Encoding($false)
$execRoot = 'F:\backup\09-LANES\OCTOPUS-PERSISTENT-FLEET-EXEC-20260915'
$hwRoot = 'F:\backup\09-LANES\OCTOPUS-HARDWARE-EXEC-20260915'
$rows = @()
function Add-Source([string]$Id, [string]$Path, [string]$Relative, [string]$Category) {
    $script:rows += [pscustomobject]@{id=$Id; original_path=$Path; snapshot_path=('sources/' + $Relative); category=$Category}
}
Add-Source 'user_context' 'C:\Users\Armin\.codex\attachments\82c3ce41-434d-484b-b86f-7be3112d902d\pasted-text.txt' 'user/pasted-text.txt' 'USER_SUPPLIED_HISTORY'
Add-Source 'agents' 'F:\backup\AGENTS.md' 'governance/AGENTS.md' 'CURRENT_LOCAL_CONTRACT'
Add-Source 'freedom' 'F:\backup\06-EVIDENCE\OCTOPUS-OWNER-BOARD-2026-08-24\GOV-FREEDOM-V2-2026-09-13.md' 'governance/GOV-FREEDOM-V2.md' 'CURRENT_LOCAL_CONTRACT'
$execFiles = [ordered]@{
    old_next='NEXT-AGENT-MEGAPROMPT.md'; old_report='LANE-REPORT.md';
    p0='P0/P0-DISCOVERY.json'; p1='P1/receipts/P1-DRY-PERSIST-RECEIPT.json';
    p2='P2/P2-DRY-BOOTSTRAP-RECEIPT.json'; p2_source='P2/fleet_job_sm.py';
    p3='P3/P3-VERIFIED-RESTORE-RECEIPT.json'; p3_timing='P3/P3-RPO-RTO-ADDENDUM.json';
    p4='P4/P4-NODE-AUTH-RECEIPT.json'; p4_gate='P4/SEC-NODE-ID-AUTH-ADDENDUM-20260915.md';
    p4_matrix='P4/P4-7ROW-MATRIX.json';
    p5='P5/P5-E2E-RECEIPT.json'; p5_gate='P5/SEC-P5-JOB-PATH-GATE-20260915.md';
    p5_contract='P5/P5-JOB-PATH-CONTRACT-20260915.md'; p5_qa='P5/QA-P5-E2E-20260915.md';
    p5_result='P5/worker-result-job-8f635a12d2cd4228.json';
    p5_excerpt='P5/job-excerpt-job-8f635a12d2cd4228.jsonl';
    p6_gate='P6/SEC-P6-ACCEPTANCE-20260915.md';
    p6_design='P6/P6-ACCEPTANCE-MATRIX-DESIGN-20260915.md';
    p6_align='P6/P6-SEC-ALIGN-20260915.md'; p6_schema='P6/schemas/acceptance_matrix.v1.schema.json';
    p6_matrix='P6/ACCEPTANCE-MATRIX.json';
    pb1='P6/PB-1/PB-1-INTERMEDIATE-RECEIPT.json';
    pb2='P6/PB-2/PB-2-CRASH-IDEMPOTENCY.json';
    pb3='P6/PB-3/PB-3-RESTORE.json';
    pb4='P6/PB-4/PB-4-ANSWER-MEMORY-AB.json';
    pb5='P6/PB-5/PB-5-NPU-HONESTY.json';
    pb6='P6/PB-6/PB-6-SEVEN-ROW-EXPAND.json';
    worker_bind='fleet-brain/WORKER-BIND-MAP-100-160-193-114-20260915.md'
}
foreach ($pair in $execFiles.GetEnumerator()) { Add-Source $pair.Key (Join-Path $execRoot $pair.Value) ('exec/' + $pair.Value) 'STORED_EVIDENCE_OR_CONTRACT' }
Add-Source 'npu_matrix' (Join-Path $hwRoot 'T2-PILOT/T2-NPU-INFERENCE-MATRIX.json') 'hw/T2-PILOT/T2-NPU-INFERENCE-MATRIX.json' 'STORED_BENCHMARK'
Add-Source 'npu_source' (Join-Path $hwRoot 'T2-PILOT/src/rknn_infer_bench.c') 'hw/T2-PILOT/src/rknn_infer_bench.c' 'SOURCE_REVIEW_NOT_LOADED_CODE_PROOF'
Add-Source 'npu193' (Join-Path $hwRoot 'T2-PILOT/193-infer-bench.txt') 'hw/T2-PILOT/193-infer-bench.txt' 'STORED_BENCHMARK'
foreach ($node in @('100','160','193','114')) { Add-Source ('hb'+$node) (Join-Path $hwRoot ('WORKER-CONNECT/worker-'+$node+'.json')) ('hw/WORKER-CONNECT/worker-'+$node+'.json') 'STORED_HEARTBEAT' }
Add-Source 'parent_exec_gate' (Join-Path $hwRoot 'PERSISTENT-FLEET-EXEC/GO-PERSISTENT-FLEET-EXEC-20260915.md') 'governance/GO-PERSISTENT-FLEET-EXEC.md' 'STORED_GATE'
$indexPath = Join-Path $PacketRoot 'SOURCE-INDEX.json'
if (Test-Path -LiteralPath $indexPath) { throw 'Snapshot already exists. Create a new version instead of overwriting evidence.' }
$sources = @()
foreach ($row in $rows) {
    if (!(Test-Path -LiteralPath $row.original_path -PathType Leaf)) { throw ('Missing source: '+$row.id) }
    $before = (Get-FileHash -LiteralPath $row.original_path -Algorithm SHA256).Hash.ToLowerInvariant()
    $destination = Join-Path $PacketRoot $row.snapshot_path
    if (Test-Path -LiteralPath $destination) { throw ('Snapshot exists: '+$row.snapshot_path) }
    [void][System.IO.Directory]::CreateDirectory((Split-Path $destination -Parent))
    Copy-Item -LiteralPath $row.original_path -Destination $destination
    $snapshot = (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToLowerInvariant()
    $after = (Get-FileHash -LiteralPath $row.original_path -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($before -ne $snapshot -or $after -ne $before) { throw ('Source changed during copy: '+$row.id) }
    $sources += [pscustomobject]@{id=$row.id; original_path=$row.original_path; snapshot_path=$row.snapshot_path; category=$row.category; sha256=$snapshot; bytes=(Get-Item -LiteralPath $destination).Length; read_at_utc=[DateTime]::UtcNow.ToString('o'); hash_verified=$true; runtime_reexecuted=$false; signature_verified=$false}
}
$byId=@{}; foreach($s in $sources){$byId[$s.id]=$s}
function Read-Snapshot([string]$id) { Get-Content -Raw -LiteralPath (Join-Path $PacketRoot $byId[$id].snapshot_path) | ConvertFrom-Json }
$matrix = Read-Snapshot 'p6_matrix'
$p5 = Read-Snapshot 'p5'
$npu = Read-Snapshot 'npu_matrix'
$checks=@()
function Check-Reference([string]$Id,[string]$Expected,[string]$Origin) {
    $actual=$script:byId[$Id].sha256
    $script:checks += [pscustomobject]@{source_id=$Id; origin=$Origin; expected_sha256=$Expected; actual_sha256=$actual; match=($actual -eq $Expected)}
}
Check-Reference 'old_next' $matrix.next_sha256 'P6 matrix'
Check-Reference 'p6_design' $matrix.design_sha256 'P6 matrix'
Check-Reference 'p6_align' $matrix.sec_align_sha256 'P6 matrix'
Check-Reference 'p6_gate' $matrix.sec_p6_sha256 'P6 matrix'
Check-Reference 'p6_schema' $matrix.schema_sha256 'P6 matrix'
Check-Reference 'p5_gate' $p5.sec_p5_job_path_gate_sha256 'P5 receipt'
Check-Reference 'p5_contract' $p5.exit_receipt_contract_sha256 'P5 receipt'
Check-Reference 'p4' $p5.p4_node_auth_receipt_sha256 'P5 receipt'
foreach($row in $matrix.tests) { Check-Reference ($row.id.ToLowerInvariant().Replace('-','')) $row.witness_receipt_sha256 ('P6 '+$row.id) }
$referenceMismatches=@($checks | Where-Object {!$_.match})
$index=[ordered]@{schema='octopus.handoff.source_index.v1'; created_at_utc=[DateTime]::UtcNow.ToString('o'); verification_scope='LOCAL_FILE_HASHES_AND_CONTENT_ONLY'; live_node_contact=$false; source_count=$sources.Count; sources=$sources; internal_references=$checks; reference_mismatch_count=$referenceMismatches.Count; missing_direct_evidence=@([ordered]@{id='p6_qa_seal'; name='QA-P6-ACCEPTANCE-20260915.md'; cited_sha256='f9c68553c1bb898baee29c093f07d50c216936b10295be4adcaa5235f59f246b'; status='REFERENCED_NOT_LOCALLY_VERIFIED'; cited_by=@('old_report','user_context')},[ordered]@{id='w24_current_state'; status='USER_REPORTED_OPEN_NOT_RUNTIME_VERIFIED'})}
[System.IO.File]::WriteAllText($indexPath,($index | ConvertTo-Json -Depth 25),$utf8)
$state=[ordered]@{
    schema='octopus.body_adaptation.handoff_state.v1'; observed_at_utc=[DateTime]::UtcNow.ToString('o'); scope='STORED_LOCAL_EVIDENCE_REVIEW'; live_runtime_verified=$false;
    success_criteria=@('better_answers','usable_durable_memory','laptop_independent_continuity'); overall='OPEN';
    continuity=[ordered]@{reported_status='IN_PROGRESS'; started_at_utc='2026-09-15T04:03:36Z'; earliest_time_only_utc='2026-09-16T04:03:36Z'; earliest_sydney='2026-09-16T14:03:36+10:00'; elapsed_time_alone_sufficient=$false; laptop_dependency_probe='NOT_YET_IN_STORED_RECEIPT'; automatic_scheduler_proven_by_this_review=$false; preserve_prior_window=$true};
    path=[ordered]@{commander='138'; bus='jsonl_138'; p5_job_id=$p5.job_id; p5_type=$p5.job_type; p5_recorded_state=$p5.final_job_state; p5_qa='PASS_WITH_CAVEAT'; actual_retrieval_proven=$false; nats_durability='NOT_CLAIMED'; jetstream_consumers_at_snapshot=0};
    acceptance_rows=@($matrix.tests | ForEach-Object {[ordered]@{id=$_.id; reported_status=$_.status; receipt_source_id=$_.id.ToLowerInvariant().Replace('-',''); caveats=$_.caveats; carry_forward_notes=$_.notes}});
    review_limits=@(
      [ordered]@{id='PB2-SCOPE'; finding='sleep stand-in killed; manual UNKNOWN; lease expires in 2099'; implication='real consumer crash recovery and short lease expiry not established'},
      [ordered]@{id='PB3-SCOPE'; finding='9/9 file match; RPO=0 at snapshot; 3 seconds manifest/transfer/check'; implication='service recovery time and continuous RPO not established'},
      [ordered]@{id='NPU-CORRECTNESS'; finding='pseudo-image plus checksum; no gold reference'; implication='runtime execution evidence distinct from semantic output correctness'},
      [ordered]@{id='NPU-HARNESS'; finding='loop can break on error but statistics use loops and final STATUS=PASS remains unconditional'; implication='repair new benchmark version; no claim historical runs actually failed'},
      [ordered]@{id='P4-IDENTITY'; finding='shared client mesh key; strict-hostkey method recorded'; implication='no independent per-worker signing or HMAC claim'},
      [ordered]@{id='P6-QA'; finding='seal cited but direct file not found in inspected lane tree'; implication='cannot claim independently verified QA seal here'});
    npus=[ordered]@{denominator=7; reported_pass=@($npu.rows|Where-Object {$_.status -eq 'PASS'}).Count; not_run=@($npu.rows|Where-Object {$_.status -eq 'NOT_RUN'}|ForEach-Object {$_.node}); rows=$npu.rows; usable_42_tops_claim=$false; semantic_correctness='UNVALIDATED_IN_REVIEWED_BENCHMARK'; reexecution_this_turn=$false};
    roles=@([ordered]@{node='138';role='sole_commander_writer'},[ordered]@{node='180';role='quality_restore_readonly'},[ordered]@{node='182';role='witness_existing_sensorium'},[ordered]@{node='100';role='knowledge_retrieve'},[ordered]@{node='160';role='knowledge_prep'},[ordered]@{node='193';role='model_infer'},[ordered]@{node='114';role='eval_batch'});
    governance=[ordered]@{p5_go='RECORDED';p6_go='RECORDED';repeat_general_go_request=$false;customer_send='HOLD';may_authorize=$false;dual_commander=$false;power_off_138=$false;mac_dhcp='DOCS_ONLY';new_operational_job_types='CHECK_SCOPED_GATE_BEFORE_DEPLOY';normal_class_a='PROCEED';normal_class_b='WITNESS_THEN_SINGLE_NODE_CANARY'};
    next_actions=@('reconcile_active_owner_and_runtime_path','verify_continuity_has_real_scheduler_and_dependency_evidence','build_real_retrieval_and_PB4_heldout_harness','build_T3_service_in_separate_owned_slice','measure_real_worker_recovery_and_semantic_restore','wire_measured_capabilities_into_existing_scheduler_and_self_model')
}
[System.IO.File]::WriteAllText((Join-Path $PacketRoot 'CURRENT-STATE.json'),($state | ConvertTo-Json -Depth 25),$utf8)
[pscustomobject]@{source_count=$sources.Count;reference_checks=$checks.Count;reference_mismatches=$referenceMismatches.Count;packet_root=$PacketRoot}|ConvertTo-Json
if($referenceMismatches.Count){$referenceMismatches|ConvertTo-Json -Depth 5;throw 'Referenced hash mismatch; preserve discrepancy and investigate.'}
