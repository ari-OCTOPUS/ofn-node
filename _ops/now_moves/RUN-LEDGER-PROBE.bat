@echo off
REM RUN-LEDGER-PROBE.bat — M1 read-only genome-ledger integrity check.
REM Default: verify ONLY (no state writes); prints a content-free verdict.
REM Exit code 1 only if the chain is BROKEN (genuine fork/tamper), else 0.
REM Add --emit to open ONE incident event on a chain worse than the baseline.
REM Add --acknowledge to accept the current state as baseline (no incident).
REM Add --path "<ledger.jsonl>" to check a specific ledger.
setlocal
cd /d "%~dp0"
python -X utf8 ledger_integrity_probe.py %*
endlocal
