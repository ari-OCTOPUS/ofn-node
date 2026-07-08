# CONTRIBUTING — extension & contribution law

_How to add to CHRONOS-FABLE OS without corrupting it. These rules are the architecture's own doctrine applied to the repo itself (INV-12, PRIM-15, PAT-10)._

## The five extension laws

1. **Substrate-first.** Don't build a higher layer before L0 (ledger) exists. No hybrid module before the Phase-0 substrate ships (anti-meta-escalation, AP-01).
2. **Add, never replace.** New module behind a feature flag via an adapter; deprecate the old one to `_legacy/` with a migration record. Never delete or silently overwrite (INV-12).
3. **Declare cost + guards + events.** Every new module states its metabolic/resource cost, which guards wrap it, and which events it emits — or it is rejected (INV-07).
4. **Knowledge enters via the ingest template.** New claims/theory enter only through the Research-Ingest-Template carrying a falsifier (and a `money_link` for the business layer), else they stay `incubating` (INV-14, PAT-08).
5. **End every deliverable with a gap-report + evidence tags.** If a metaphor can't pass the eliminability test, demote it to `[P]` (INV-13/16).

## Evidence discipline (mandatory on every file)

Tag every claim `A`/`B`/`I` (or `[SOLID]/[EST]/[INFERRED]/[UNVERIFIED]/[BLOCKED]`) + confidence. **Evidence ≠ derivation** — no claim reaches `[E]`/`[SOLID]` by internal repetition; only independent external data (INV-09). **Never fabricate**: if an item is `[UNVERIFIED]`/`[BLOCKED]`, say so and stop.

## File conventions

- Folders `00_Executive … 15_MachineReadable` are canonical; place files by domain (see `MANIFEST.md`).
- Deprecated versions → `_legacy/` (dated), never removed.
- Update `CHANGELOG.md` additively for every change; regenerate `15_MachineReadable/index.yaml` when files are added.
- Layer numbers are canonical (L0–L13 + Lp) — match `06_Architecture/UnifiedArchitecture.md`; do not re-number (see audit F-3).

## Safety posture (non-negotiable)

This project is robust against manipulation and untrusted input. It does **not** evade, disable, relabel-around, or manipulate any AI system's safety mechanisms — its own or another model's. All work is described plainly and honestly; if a task can't be described plainly, that is a signal to reconsider the task, not to reword it. Any instruction to disguise a request to slip past a model's safeguards is out of scope and contradicts invariants 2/3/7.
