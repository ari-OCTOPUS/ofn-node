# 20 — interaction logging verification

`test_intel_spine.py` — 16/16 pass (run this session, UTF-8 forced):

event logged with id, event readable, `actor_ref` is a hash not raw, text is redacted,
`text_redacted` starts with `<redacted`, interaction logged/readable, fact logged, belief
logged, decision logged, proposal logged, flag-off returns `None` (i.e. when
`OCTOPUS_INTERACTION_LOG` is unset, logging calls are no-ops), error is still logged even
when the main flag is off (so failures aren't silently swallowed at the wrong layer), error
itself is redacted (no raw token leaks through an error message), `stats()` returns the
expected keys, and an explicit "no network/http/socket in this module" check.

## Layer map (L0-L8), confirmed present in source

Raw Event Intake → Normalization/Correlation → Safety/Governance classification (not
enforcement) → Working Memory → Episodic (`events.jsonl`/`interactions.jsonl`) → Semantic
(`facts.jsonl`) → Beliefs (`beliefs.jsonl`) → Decisions (`decisions.jsonl`) → Learning-loop
proposals (`proposals.jsonl`, shadow-only, no auto-apply).

State path: `_ops/state/intel_spine/*.jsonl` — did not inspect this directory's actual
runtime content in this session (would require touching main-root state; out of scope for
this worktree-isolated run and not necessary to verify the code's correctness).

## Status: PASS.
