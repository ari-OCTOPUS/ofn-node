---
megaprompt_title: VibeGuard implement — spec is SoT
version: "1.0"
written_by: "Cursor Grok 4.6 — 2026-08-17 ingest from owner research drop"
audience: Claude Code or Cursor agent implementing vg
vault_root: "F:\\backup"
---

# VibeGuard — پیاده‌سازی از spec (بحث معماری ممنوع)

You are implementing **VibeGuard (`vg`)**, a local-first offline security engine for AI-generated / vibe-coded repos. Research is finished. Do not re-open architecture.

## Read first (in order)

1. `F:\backup\03 - Projects\VibeGuard\00-START-HERE.md`
2. `F:\backup\03 - Projects\VibeGuard\NEXT-AGENT.md`
3. `F:\backup\03 - Projects\VibeGuard\Project-Specification.md` — **this wins** on conflict
4. `F:\backup\03 - Projects\VibeGuard\Deep-Research-and-Architecture-Report.md` — evidence only

`research/00_design_directive.md` is **missing** from this vault. Treat locked decisions in START-HERE as D1–D11. Do not invent new product surfaces.

## Locked decisions

- Product = Python 3.12 engine + CLI `vg`. Offline. Model-agnostic. No Anthropic requirement.
- Adapters only: `vg-mcp` (read-only default), `vg-hook` (deny tool calls), `vg-plugin` (packaging), `vg-app` (Checks write).
- Skill-only product = rejected.
- Scanner engine for rules = Opengrep (LGPL-2.1) + first-party corpus. Do not redistribute Semgrep rules. Do not ship CodeQL CLI for commercial use.
- Honesty: never claim secure / 100% safe / clean. Vocabulary: risk reduction, residual risk, confidence, abstain, unverified.
- MVP: JS/TS + Python; S0–S5, S7, S9 + repo-trust; no auto-apply patches; no IDE plugins; no DAST-at-scale; no cloud multi-tenant source scan.

## Octopus house rules (this vault is live)

- Work in `03 - Projects/VibeGuard/` (or a **new** git repo if the owner says so). Do not wire into `_ops` or OCTOPUS flags without an explicit owner vote.
- Never `git add -A`. Never commit `_ops/state/**`, live ledgers, `nervous-system/*-data.js`.
- Do not print secrets. Do not delete. Improve, don't rewrite the spec.

## Done looks like

A `vg scan` that runs offline on a small JS or Python fixture, emits SARIF 2.1.0 + signed JSON findings, never executes repo code, never opens network in S1–S5, and every finding has CWE + VIBE class + confidence. Tests for invariants you touch.

[END]
