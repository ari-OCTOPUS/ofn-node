$ErrorActionPreference = 'Stop'
Set-Location 'F:\backup'

$steps = @(
  @{ Name = 'C2 targeted'; Cmd = 'python -X utf8 "F:\backup\_ops\tests\test_c6_hypothesis_producer.py"' },
  @{ Name = 'C6 propose-only'; Cmd = 'python -X utf8 "F:\backup\_ops\tests\test_c6_trigger_propose_only.py"' },
  @{ Name = 'C6 bench honesty'; Cmd = 'python -X utf8 "F:\backup\_ops\tests\test_c6_bench_honesty.py"' },
  @{ Name = 'C3 targeted'; Cmd = 'python -X utf8 "F:\backup\_ops\tests\test_c3_owner_trust_forgery.py"' },
  @{ Name = 'C3 learning loop'; Cmd = 'python -X utf8 "F:\backup\_ops\tests\test_learning_loop.py"' },
  @{ Name = 'C3 research loop'; Cmd = 'python -X utf8 "F:\backup\_ops\tests\test_research_loop.py"' },
  @{ Name = 'C3 memory gate'; Cmd = 'python -X utf8 "F:\backup\_ops\tests\test_memory_gate.py"' },
  @{ Name = 'C3 lead learning'; Cmd = 'python -X utf8 "F:\backup\_ops\tests\test_lead_learning_wire.py"' },
  @{ Name = 'C3 verdict outcome'; Cmd = 'python -X utf8 "F:\backup\_ops\tests\test_verdict_outcome.py"' },
  @{ Name = 'C3 paper lead e2e'; Cmd = 'python -X utf8 "F:\backup\_ops\tests\test_paper_lead_mvo_e2e.py"' },
  @{ Name = 'Router dark config'; Cmd = 'python -X utf8 "F:\backup\_ops\tests\test_paid_router_dark_config.py"' },
  @{ Name = 'Full suite'; Cmd = 'python -X utf8 "F:\backup\_ops\tests\run_all.py"' }
)

foreach ($s in $steps) {
  Write-Host "`n=== $($s.Name) ==="
  Invoke-Expression $s.Cmd
  $code = $LASTEXITCODE
  Write-Host "exit=$code"
  if ($code -ne 0) { throw "FAILED: $($s.Name) with exit code $code" }
}

Write-Host "`nALL GREEN. Suggested commits:"
Write-Host "1) fix(c6): add honest hypothesis producer and id-safe queue lifecycle"
Write-Host "2) fix(memory): derive owner trust from durable attestation"
Write-Host "3) chore(llm): lock router paths behind explicit dark flags"
