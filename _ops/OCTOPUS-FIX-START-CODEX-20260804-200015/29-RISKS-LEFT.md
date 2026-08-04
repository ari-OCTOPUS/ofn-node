# 29 — Risks left open after this run

| Risk | Severity | Status after this run |
|---|---|---|
| arm_gate not wired to `code_autonomy` (self_patch.py) | was P0 | **Closed** — wired same day on owner's explicit instruction, 4 new + 35 regression tests pass (§31, DR-001) |
| arm_gate not wired to `self_improve_auto` | was new gap | **Closed** — wired at both real write sites (`auto_approve.run()` live path + `vault_updater_apply.apply()` defense-in-depth), 22 new + 18 regression tests pass (§32) |
| arm_gate not applicable to `replicate` | n/a | **Not a risk to close** — no real spawn/execute function exists anywhere in the codebase; confirmed by full-file read of `budget/replication.py` + adversarial verify. Nothing to gate today (§32) |
| latent_space silent wipe | was P0 | **Closed** — verified fixed and tested from source, independently confirmed |
| `store()` bare `except OSError: pass` on the persist/write path | new, minor | Not a wipe risk (doesn't touch already-loaded data); flagged for awareness only, not actioned |
| 249 dirty files in `F:\backup` main root | pre-existing, operational | Out of scope for this worktree-isolated run; not touched, not worsened |
| doctor-pulse stuck mission (8 days) | pre-existing | Unrelated to P0 scope; not touched, still open per source scan docs |
| OWNER-PROFILE PII in git history | pre-existing, low urgency unless repo goes public | Not touched (destructive history rewrite, out of scope) |
| `_append_jsonl` in intel_spine is append-only but not tmp+replace-atomic | new, minor | Documented as an accepted/intentional tradeoff in the source; a mid-write crash could leave a truncated last JSONL line. No test for this specific edge case was found or added this session. |
| `vault_updater_apply.py`'s new arm_gate check protects a currently-orphaned module | new, minor | It has no production caller today (per `_agent_reports/ORPHAN-TRIAGE-2026-07-30.md` and repo-wide grep) — the wiring is real and tested but not load-bearing until this module is separately wired into production (§32) |

Nothing in this table is new risk introduced by this session — every row is either a
pre-existing item from the source scan, a residual scope gap this run's own verification
surfaced, or (in the case of `store()`'s except-pass) a genuinely minor finding raised for
completeness rather than urgency.
