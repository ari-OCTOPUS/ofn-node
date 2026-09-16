# Second Brain Super-Governor — Phase 1 artifacts

> **Phase 1 = docs/prompts only.** Zero vault access, zero private data, zero API
> calls, fully reversible. These files are the *canonical source* for the brain
> prompts, config, and templates; they get **synced into the Obsidian vault**
> later (they are authored here first so they are versioned and reviewable).
>
> Built per [`docs/SECOND-BRAIN-BUILD-PLAN.md`](../docs/SECOND-BRAIN-BUILD-PLAN.md),
> faithful to [`docs/SECOND-BRAIN-SUPERGOVERNOR-v0.2.md`](../docs/SECOND-BRAIN-SUPERGOVERNOR-v0.2.md),
> under the IMPROVE-DON'T-REWRITE doctrine. NBB-CP stays component **B6**; nothing
> here rebuilds it.

## Contents

```
second-brain/
  agents/
    SUPERBRAIN-GOVERNOR.md   B0 — orchestrator/governor (routes, never executes)
    B1_INTAKE.md             raw input → normalized notes
    B2_DASHBOARD.md          human-readable status/pulse (no new truth)
    B3_LIFE_CHRONOS.md       time / priority / life OS
    B4_PROJECTS.md           project cards (financial/comms → propose only)
    B5_ARCHITECT.md          system design / specs / ADRs (mutations gated)
    B6_AGENTOPS_NBB.md       control plane = the existing NBB-CP (this repo)
    B7_KNOWLEDGE.md          research / evidence (confidence-labelled)
    B8_PEOPLE_COMMS.md       people / comms (draft only, never send)
    agents.yaml              Fugu config (use_ultra: false), risk + folders per brain
  templates/
    brain-state.md · handoff-packet.md · project-card.md · evidence-card.md
    decision-record.md · approval-packet.md · memory-write.md
  FRONTMATTER-STANDARD.md    the note frontmatter every brain must emit
  CHANNEL_MAP.md             empty scaffold; filled by the Phase 2 read-only scanner
```

## Vault mapping (for the later sync — NOT done in Phase 1)

| Here | Obsidian vault destination |
|---|---|
| `agents/*.md`, `agents.yaml` | `05 - Agents/` |
| `templates/*.md` | `_Templates/` |
| `FRONTMATTER-STANDARD.md`, `CHANNEL_MAP.md` | `06 - Architecture Maps/` |

## The one law (spec §18)

> Every brain *thinks*; the SuperBrain *routes*; **NBB (B6) controls**; the Vault is
> canonical memory; and the **human approves** every sensitive action. No brain
> executes an external message, canonical write, script, deletion, financial action,
> architecture change, or memory promotion directly — all of those become an
> `ActionProposal` through B6.

## Not in Phase 1 (need owner GO + inputs)

- Phase 2 read-only vault scanner → needs the **Obsidian vault path**.
- Phase 3 SuperBrain runtime → needs the **Fugu API key** (supplied via env/gitignored
  `.env` at runtime — never committed, per CLAUDE.md rule 6).
