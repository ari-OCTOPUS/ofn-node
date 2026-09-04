# BOARD-SELF-MODEL-TRUST-001

Authority: direct owner board-file edit grant, BOARD-CODE-001. Node 138 only in this implementation. Formal CANON-001 source designation remains open.

Owned source paths: ofn/kernel/self_model.py and tests/test_self_model_input_trust.py. Report path: 09-LANES/BOARD-SELF-MODEL-TRUST-001/. Other source, untracked data, remotes, runtime state, services, flags, credentials and existing lanes are untouched.

Work in a separate sparse Git worktree on the board, based on e00c8ed5be7ec6609c600bb7a5bc3b99ace3c3e9, without fetch, push, merge or service activation. Existing root worktree is read-only. No dependency installation or bulk repository copy. Source preimages and exact candidate hashes retained locally; no secret contents.

Objective: make the existing self-model input boundary preserve unknownness instead of turning malformed freshness, liveness/capability inputs or a missing/invalid brain-probe status into a healthy organism claim. No schema/gate/threshold change; the existing five-second future tolerance stays unchanged.

Predeclared acceptance: the existing self-model test suite stays green; new isolated negative contract tests fail against the captured original and pass against the candidate; kernel purity tests pass or any pre-existing failure is reported separately. Invalid windows/overflow return unknown, only actual booleans form measured process/capability states, and a missing/invalid brain-probe status makes the aggregate unverifiable. Genuine zero, measured absence, deterministic output, valid freshness and frozen thresholds remain compatible.

Test inputs are explicit malformed API arguments, not invented observations, benchmark results, business events or runtime data. No test writes to live logs or databases. Runtime health and performance uplift remain unverified; persistence/prior/random predictive baselines are not beaten or evaluated because this patch is contract validation, not a predictor.

Deliverable: tested board-local source patch and five-section lane report. Promotion to the main service worktree is not silently inferred from source-edit permission: no canonical designation or activation claim is manufactured.
