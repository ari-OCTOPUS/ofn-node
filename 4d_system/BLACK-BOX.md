# Black Box — NBB-CP / Second Brain Super-Governor

Relocated to `F:\Black Box` on **2026-07-11**. This is now a **standalone git repo**
(its own history starts at the relocation commit).

## What's here
- **NBB Control Plane** (component **B6**, 171 tests green) — `src/`, `tests/`, `run.py`.
- **Second Brain Phase 1** artifacts — `second-brain/` (9 brain prompts, `agents.yaml`,
  7 templates, frontmatter standard, channel-map scaffold).
- **Docs & governance** — `CLAUDE.md`, `docs/` (spec, build plan, hardening, doctrine).

## Full prior history (the 5 commits) is preserved
`_history/nbb-cp-full-history.bundle` holds the complete lineage
(skeleton → hardening → idempotency+saga → approval-TTL → Phase 1). Inspect/restore:

    git clone "_history/nbb-cp-full-history.bundle" restored

## Run

    python -m pytest        # 171 green
    python run.py           # shadow demo epoch (no keys, no network)

## First read
`CLAUDE.md` — STRICT SAFETY RULES + IMPROVE-DON'T-REWRITE. No secrets in the repo
(Fugu key supplied at runtime via env / gitignored `.env`, never committed).

_Origin worktree: `C:\Users\Armin\.claude\worktrees\second-brain-governor-v02-2a6e36`._
