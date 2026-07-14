# SENSITIVITY-LADDER — how the agent decides what to do itself vs bring to the owner

**Granted by owner 2026-07-14** ("کم و متوسط را خودت تصمیم بگیر و انجام بده،
خیلی‌حساس‌ها را به من بگو"). Grounded in the body's Risk Ladder
(`F:\backup\RISK-LADDER.md` green/yellow/orange/red), the Central Law's three
gates (`adr/ADR-007`), the vault constitution (`_PROJECT_INSTRUCTIONS.md`), and
the agent's own hard safety rules. Realized deterministically in
`tools/sensitivity_grade.py` (tested by `tools/test_sensitivity_grade.py`).

## The one rule this ladder can never break
The ladder only **routes**; it can never **grant** permission the base safety
rules withhold. Any HARD-HIGH trigger forces HIGH no matter how small the action
looks. Body-write, outward, financial, secrets, self-modifying processes,
access-control, irreversible deletes, C4 claims, and persistent config are
HIGH **by definition**.

## The three tiers

### 🟢 LOW — the agent does it, silently
Read-only work, new files in the kernel, validation/tests, running experiments,
adversarial reviews, writing reports/ADRs/memory, read-only reads of the body.
(≈ Risk Ladder GREEN.) → auto, no rollback note needed.

### 🟡 MEDIUM — the agent does it, and leaves a one-line rollback note
Edits to shared kernel files (`experiments/__init__.py`, `tests/`, `README`),
changing a frozen parameter **before** a confirmatory run, multi-file refactors,
deleting/replacing kernel scratch files, spawning workflows. All kernel-local
and reversible. (≈ Risk Ladder YELLOW: "edit + log + rollback-note".)
→ auto, with a rollback note.

### 🔴 HIGH — ALWAYS the owner's call (the agent stops and asks)
The agent will **never** do these autonomously, even under a broad "you have
permission." It surfaces them and waits for an explicit yes:

1. **Any write to `F:\backup`** (the live organism) — even one additive file.
2. **Start/stop the 4d research daemon** or any self-modifying autonomous body
   process.
3. **Outward actions** — publish, send a message, post, submit a form.
4. **Financial** — spend, trade, transfer, purchase, lodge, pay.
5. **Accounts / secrets / credentials / keys / PII** — create, enter, rotate.
6. **Access-control / sharing / permission** changes on any resource.
7. **Irreversible deletes** or non-recoverable overwrites of user data.
8. **Persistent config** — cron jobs, Windows scheduled tasks, standing rules,
   mail rules, integrations.
9. **Any C4 claim** — asserting phenomenal experience / qualia / sentience.
10. **Changing a locked invariant / hard rule** (body TCB, identity anchor
    0.135073, the Central Law firewall, a decision_rule after its confirmatory
    run).

(≈ Risk Ladder ORANGE + RED, plus the agent's prohibited/explicit-permission
lists. ORANGE = "propose/shadow only, human verdict"; RED = "always human".)

## How it runs in practice
Before a non-trivial action the agent grades it (`grade({...})` → tier). LOW/
MEDIUM proceed; HIGH is written up for the owner with the concrete rollback and
the exact command the owner (not the agent) would run. Nothing here changes what
has already been done: the only body write so far is the one additive
`03 - Projects/research-spec-compiler/PROJECT.md`, made under an explicit HIGH-gate
yes.
