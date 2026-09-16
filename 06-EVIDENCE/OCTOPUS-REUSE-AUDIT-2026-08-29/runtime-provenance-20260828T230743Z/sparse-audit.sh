#!/bin/bash
set -u
cd /home/ari/ofn
output=06-EVIDENCE/runtime-provenance-20260828T230743Z/sparse-commit-audit.txt
{
  printf '%s\n' '=== HEAD ==='
  git show --stat --oneline HEAD
  printf '%s\n' '=== HEAD~1 ==='
  git show --stat --oneline HEAD~1
  printf '%s\n' '=== LOG NAME-STATUS ==='
  git log --name-status -3
  printf '%s\n' '=== SPARSE CONFIG ==='
  git config --get core.sparseCheckout || true
  printf '%s\n' '=== SPARSE LIST ==='
  git sparse-checkout list 2>&1 || true
  printf '%s\n' '=== UCP FORENSIC COMMITS ==='
  git log --all --oneline --grep='ucp-forensic' -10
} > "$output"
python3 - "$output" <<'PY'
from pathlib import Path
import sys
print(Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace"))
PY
