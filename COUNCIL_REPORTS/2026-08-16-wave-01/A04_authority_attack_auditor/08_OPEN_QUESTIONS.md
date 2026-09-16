# A04 — OPEN QUESTIONS

Q1 · **MCP runtime registration** — `octopus_mcp/server.py` exists (git/file subprocess tools, loopback host allowlist) and `.mcp.json` sits at repo root, but A04 did not observe a live MCP listener or which client (editor?) consumes it. Needs T0 check by A02 (runtime investigator): is the MCP server process running, stdio or HTTP, and does any agent-facing client pass it untrusted tool names?

Q2 · **Env completeness** — flags verified against `.env` non-secret lines only. Do launcher `.cmd`/`.bat`/scheduled tasks set additional `OCTOPUS_*` flags at boot (e.g. OCTOPUS_WIRE_CODE_APPLY, OCTOPUS_KILL_SWITCH, OCTOPUS_WIRE_CB_TOKEN)? A file-based verdict could be stale the moment a launcher changes env. Owner or A02 can answer from the launcher set (`_ops/OCTOPUS-flags.cmd` et al.).

Q3 · **Live wire-set at runtime** — `wiring.wire_summary()` / organism heartbeat logs would give the authoritative on-flag list for this boot. Read-only snapshot recommended for wave 2 evidence (T0).

Q4 · **Viability Loop** — the project-claims list mentions it as runtime-enforced; A04 found no component of that name in the live path (only protective_override/protective_halt in wiring.py). Is it a synonym, a planned component, or 4d_system-side? (UNKNOWN)

Q5 · **Mutual veto (C-8)** — if it exists, where? Possibly in `debate/` or `governor/` (not audited in depth — out of authority-critical path as far as traced). A03/A05 may own this.

Q6 · **`_ops/state` write surface vs STOP files (R-9)** — can any *currently live* beat-driven writer modify `_ops/STOP-*` or `_ops/ACTIVATION-*` paths today (as opposed to code_autonomy's denied list)? A04 found deny coverage in shell+code_autonomy but did not exhaustively sweep all `open(..., "w")` callers for those targets. Recommend a targeted grep-wave.

Q7 · **Sensorium claim (C-9)** — A04 confirmed afferent/sensory beats exist; whether "Sensorium" names a specific live subsystem (and its payload trust handling) is A02/A03 territory.

Q8 · **Xero client liveness** — books_xero is flag-gated (`OCTOPUS_WIRE_COMPANY_BOOKS`) but the egress sweep marks Xero "LIVE"; reconcile: is the OAuth client actually called on any current beat, or only constructible? (T0 question for A02.)

Q9 · **4d_system + NBB-CP** — confirmed disconnected from the organism loop; whether they run as independent *processes* with their own Telegram bots (`4d_system/brain/telegram_bot.py` has unguarded arbitrary-URL `fetch_url`) is outside `_ops` scope but inside the owner's threat model. Recommend a dedicated process census.

Q10 · **`.claude/` (11.9k py)** — excluded as tooling; if any agent-skill code there executes with vault privileges and reads repo files, it is an indirect injection surface worth its own audit wave.
