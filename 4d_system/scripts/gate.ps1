# Phase 0 gate (Windows): full suite green + kernel purity.
# Usage: powershell -File scripts/gate.ps1
$ErrorActionPreference = "Stop"
python -m pytest
if ($LASTEXITCODE -ne 0) { exit 1 }
python -m pytest tests/test_import_lint.py -q
exit $LASTEXITCODE
