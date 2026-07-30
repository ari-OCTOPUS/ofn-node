$ErrorActionPreference = 'Stop'
Set-Location 'F:\backup'

Write-Host "=== Syntax check ==="
$files = @(
  '_ops\c6_trigger.py',
  '_ops\c6_probes.py',
  '_ops\c6_producer.py',
  '_ops\outcomes\learning_gate.py',
  '_ops\memory\gate.py',
  '_ops\outcomes\research_loop.py',
  '_ops\tests\test_c6_hypothesis_producer.py',
  '_ops\tests\test_c3_owner_trust_forgery.py',
  '_ops\tests\test_paid_router_dark_config.py',
  '_ops\tests\test_learning_loop.py',
  '_ops\organ_dialogue.py',
  '_ops\chrono.py',
  '_ops\wiring.py',
  '_ops\tests\test_organ_dialogue_digest.py',
  '_ops\tests\test_leg_failure_reason.py',
  '_ops\heart\producers.py',
  '_ops\legs\journal_bridge.py',
  '_ops\doctor\doctor.py',
  '_ops\tests\test_heart_honest_pulse.py',
  '_ops\tests\test_doctor_rfc_stale_dedup.py',
  '_ops\cortex\goal_directed.py',
  '_ops\cortex\improve.py',
  '_ops\tests\test_honest_outcomes.py'
)
foreach ($f in $files) {
  python -X utf8 -m py_compile $f
  if ($LASTEXITCODE -ne 0) { throw "SYNTAX FAIL: $f" }
}
Write-Host "syntax ok"

Write-Host "`n=== C2 targeted ==="
python -X utf8 "F:\backup\_ops\tests\test_c6_hypothesis_producer.py"
if ($LASTEXITCODE -ne 0) { throw "C2 targeted failed" }

Write-Host "`n=== C6 propose-only ==="
python -X utf8 "F:\backup\_ops\tests\test_c6_trigger_propose_only.py"
if ($LASTEXITCODE -ne 0) { throw "C6 propose-only failed" }

Write-Host "`n=== C3 targeted ==="
python -X utf8 "F:\backup\_ops\tests\test_c3_owner_trust_forgery.py"
if ($LASTEXITCODE -ne 0) { throw "C3 targeted failed" }

Write-Host "`n=== Router dark config ==="
python -X utf8 "F:\backup\_ops\tests\test_paid_router_dark_config.py"
if ($LASTEXITCODE -ne 0) { throw "Router dark config failed" }

Write-Host "`n=== T1 severity-label digest ==="
python -X utf8 "F:\backup\_ops\tests\test_organ_dialogue_digest.py"
if ($LASTEXITCODE -ne 0) { throw "T1 digest failed" }

Write-Host "`n=== T3 leg failure reason ==="
python -X utf8 "F:\backup\_ops\tests\test_leg_failure_reason.py"
if ($LASTEXITCODE -ne 0) { throw "T3 leg failure reason failed" }

Write-Host "`n=== T4 honest pulse ==="
python -X utf8 "F:\backup\_ops\tests\test_heart_honest_pulse.py"
if ($LASTEXITCODE -ne 0) { throw "T4 honest pulse failed" }

Write-Host "`n=== T8 rfc stale dedup ==="
python -X utf8 "F:\backup\_ops\tests\test_doctor_rfc_stale_dedup.py"
if ($LASTEXITCODE -ne 0) { throw "T8 rfc stale dedup failed" }

Write-Host "`n=== T2 honest outcomes ==="
python -X utf8 "F:\backup\_ops\tests\test_honest_outcomes.py"
if ($LASTEXITCODE -ne 0) { throw "T2 honest outcomes failed" }

Write-Host "`nALL QUICK CHECKS PASSED"
