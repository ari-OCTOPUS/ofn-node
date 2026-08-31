# MP-09 — Close the hermetic boundary leak (two entries OPEN)

Read `00-ASK-PROTOCOL.md` first. Ask-first is mandatory.

## Problem

The hermetic full-suite evaluation ran once and returned a boundary violation:
827 suites executed, 770 passed, 57 failed, 1 live skipped, exit non-zero, and
twelve tracked state, budget and evidence files were mutated and then restored.
The child environment redirect held for network but not for tracked writes, so
two risk entries remain open: the default writes tracked state, and the redirect
does not stop hardcoded writers. The runbook forbids re-running this as a
campaign gate and forbids repairing it inside the measurement task. So the leak
is measured, documented, and untouched.

## Forbidden

Enabling the live provider suite to make the run green. Re-running the full
evaluation as a gate. Repairing and measuring in the same task. Deleting the
restored residue. Reporting a suite count that contradicts the recorded one.

## Steps

1. Enumerate the twelve mutated paths and, for each, find the writer in source:
   file, function, and whether the path is hardcoded or resolved through the
   redirect.
2. Classify each writer: honours redirect, ignores redirect, or writes before
   redirect is installed.
3. Report the 57 failures grouped by cause, separating platform-portability
   failures from genuine logic failures, and state which group each belongs to
   with evidence.
4. ASK Q1: is closing the writers a separate authorised task, or does it stay
   open as an accepted gap?
5. ASK Q2: for each writer class, does the fix redirect the path, refuse the
   write, or move the file out of version tracking? Ask per class, sequentially.
6. ASK Q3: after any fix, does the evaluation re-run — and if so, under what
   authorisation, given re-running as a gate is forbidden?
7. ASK Q4: the 57 failures were never triaged into a repair plan — does that
   triage start now or wait?
8. Change no writer without an answer. A failed gate stays a gate, not a task to
   bypass it.

## Expected output

`docs/octopus-surgery/receipts/HERMETIC-LEAK-<date>.yaml`: twelve paths mapped
to writers, the failure grouping with counts, and the four answers.

## Done when

Every mutated path has a named writer and an owner decision, and the failure
list is grouped by cause rather than counted in aggregate.
