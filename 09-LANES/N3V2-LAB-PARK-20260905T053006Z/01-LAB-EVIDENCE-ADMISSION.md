---
type: report
status: done
created: 2026-09-05
updated: 2026-09-05
tags: [octopus, lab, evidence, provenance]
---

# Lab evidence admission

The admitted historical conclusion artifact has 24 rows and reports `16 SUPPORTED / 8 INCONCLUSIVE / 0 REFUTED`. Its rows contain only `experiment_id` and `result`; it does not provide an experiment-level preregistration reference, denominator, control, instrumentation, outcome, or receipt pointer.

The admitted security preregistry contains only 11 records, all `PENDING`, at a different code head. This is a provenance conflict, not permission to fabricate the missing evidence.

The eight `INCONCLUSIVE` labels are confirmed from the conclusion artifact. The classification below concerns the gap in the admitted evidence packet only:

| Experiment | Evidence-gap classification | What is not established |
|---|---|---|
| EXP-TG-003 | `MISSING_INSTRUMENTATION` | Underlying scientific cause |
| EXP-TG-005 | `MISSING_INSTRUMENTATION` | Underlying scientific cause |
| EXP-HUB-001 | `HYPOTHESIS_UNDERDEFINED` | Underlying scientific cause |
| EXP-HUB-002 | `HYPOTHESIS_UNDERDEFINED` | Underlying scientific cause |
| EXP-HUB-003 | `HYPOTHESIS_UNDERDEFINED` | Underlying scientific cause |
| EXP-DOCTOR-001 | `HYPOTHESIS_UNDERDEFINED` | Underlying scientific cause |
| EXP-C21-001 | `HYPOTHESIS_UNDERDEFINED` | Underlying scientific cause |
| EXP-C23-001 | `HYPOTHESIS_UNDERDEFINED` | Underlying scientific cause |

Each classification is an `INFERENCE` restricted to the admitted packet. It does not upgrade any result, change a production registry, or assert that a broader vault search is complete.

The complete source hashes, heads, and per-row caveats are in `LAB-EVIDENCE-ADMISSION-v1.json` in the isolated package.

