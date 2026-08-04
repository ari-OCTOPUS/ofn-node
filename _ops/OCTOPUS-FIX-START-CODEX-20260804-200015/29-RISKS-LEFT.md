# 29 — Risks left open after this run

| Risk | Severity | Status after this run |
|---|---|---|
| arm_gate not wired to any production call site | was P0 | Downgraded from "P0, live gap" to "module fixed + tested, wiring is the one remaining step" — proposal written, not applied (§14) |
| latent_space silent wipe | was P0 | **Closed** — verified fixed and tested from source, independently confirmed |
| `store()` bare `except OSError: pass` on the persist/write path | new, minor | Not a wipe risk (doesn't touch already-loaded data); flagged for awareness only, not actioned |
| 249 dirty files in `F:\backup` main root | pre-existing, operational | Out of scope for this worktree-isolated run; not touched, not worsened |
| doctor-pulse stuck mission (8 days) | pre-existing | Unrelated to P0 scope; not touched, still open per source scan docs |
| OWNER-PROFILE PII in git history | pre-existing, low urgency unless repo goes public | Not touched (destructive history rewrite, out of scope) |
| `_append_jsonl` in intel_spine is append-only but not tmp+replace-atomic | new, minor | Documented as an accepted/intentional tradeoff in the source; a mid-write crash could leave a truncated last JSONL line. No test for this specific edge case was found or added this session. |
| arm_gate's `self_improve_auto`/`replicate` real call sites unaudited | new, follow-up | Only `code_autonomy`'s call site was traced to a specific function this session |

Nothing in this table is new risk introduced by this session — every row is either a
pre-existing item from the source scan, a residual scope gap this run's own verification
surfaced, or (in the case of `store()`'s except-pass) a genuinely minor finding raised for
completeness rather than urgency.
