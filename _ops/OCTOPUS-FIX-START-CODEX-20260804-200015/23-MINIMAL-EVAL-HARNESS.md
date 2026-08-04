# 23 — Minimal eval harness

Existing runners (`_ops/tests/run_all.py`, `4d_system/tests/run_all.py`) were explicitly on
the master instruction's "do not execute" list (may subprocess/call an LLM) and were not
run. Built a new, minimal, purpose-scoped harness instead:

`_ops/tests/run_p0_verify.py` (new file, this session).

## What it does

Runs exactly the 6 P0-relevant test files as subprocesses of the current Python
interpreter, each with `PYTHONIOENCODING=utf-8` / `PYTHONUTF8=1` / `-X utf8` forced, and
aggregates their exit codes + a short tail of their own output into one pass/fail table.
Nothing else — no network, no other subprocess, no install, no Docker.

## Why it needed to exist: a real false-red bug found this session

Running any of the 5 non-unittest P0 test files with a plain `python test_x.py` on this
Windows machine's default console (cp1252) crashes with `UnicodeEncodeError` while printing
a ✅ character — **after** every check had already run and recorded pass/fail internally.
The crash happens in the results-printing loop, not in the test logic, so the misleading
part is specifically the exit code: 1, meaning "looks failed," when the real answer was "20
for 20 passed, then a print statement crashed." `RUN-ORGANISM.bat` already works around
this exact class of problem (`chcp 65001`, `PYTHONUTF8=1`, `PYTHONIOENCODING=utf-8`) for the
production process; the test files did not inherit that same protection when run standalone.
`run_p0_verify.py` applies the identical fix at the harness level so nobody re-discovers
this the hard way in CI or a future session.

## Result

`python run_p0_verify.py` → `ALL GREEN`, exit 0. See `24-EVAL-RESULTS.md` for full output.
