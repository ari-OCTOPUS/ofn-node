# Lane launch prompt — template

Copy this into a fresh Cursor Agent or CLI session. Replace the bracketed fields only.
Do not add scope. Do not merge two lanes into one session.

---

Lane: **[LANE_ID]** — [LANE_NAME]

You are bound by `AGENTS.md` at the repository root. Read it before your first edit.

**Owned paths (you may write here):** [OWNS_PATHS]
**Forbidden paths (stop condition if touched):** [FORBIDDEN_PATHS]
**Read-only lane:** [yes/no]
**Depends on:** [DEPENDS_ON] — if that lane's exit gate is not met, stop and report instead of proceeding.

**Objective, in one sentence:** [ONE SENTENCE]

**Pre-declared pass criterion (write this to a file and hash it before you look at any output):**
[CRITERION]

**Baselines you must beat, or explicitly report as not beaten:** persistence, prior-only, random.

**Definition of done:** [EXIT_GATE]

**Reporting:** write `09-LANES/[LANE_ID]/LANE-REPORT.md` with exactly five sections —
what was done, what remains, what failed, evidence paths, rollback steps.
Every number carries a source path or the token `unverified`.

**Prohibited in this session:** enabling any flag, opening any closed gate, outbound network,
deleting files, deciding anything reserved for the owner, editing files outside owned paths.

Begin with a plan. Do not write code until the plan is stated and the pass criterion is written to disk.
