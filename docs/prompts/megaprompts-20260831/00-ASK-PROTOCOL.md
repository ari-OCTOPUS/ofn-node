# 00 — ASK PROTOCOL (shared preamble for every megaprompt in this pack)

Updated: 2026-08-31
Canonical lineage: `main` @ `f77b68e7` (owner ruling Q5, 2026-08-31)
Deployed runtime record: `work/owner-brain-p0-fix` @ `570c856`
Vault: separate repository — publication FORBIDDEN except designed export branches

---

## Rule 0 — Ask, never assume

Every agent running a prompt in this pack MUST paste this block, filled, before
any step that changes a file, a branch, a gate, a threshold or a number:

```yaml
ask:
  prompt_id: <e.g. MP-03>
  step: <step number in that prompt>
  question_number: <1..n, sequential within the session>
  question: <one single question, under 200 chars>
  why_owner_only: <what breaks if the agent decides instead>
  options:
    - id: <short-id>
      text: <option text>
      consequence: <what this opens or closes>
  default_if_silent: NONE   # silence is never yes
  blocking: true|false
```

Hard constraints on asking:

- One question at a time. Never dump a form. Wait for the answer, record it,
  recompute what is still missing, then ask the next one.
- Never write `default_if_silent` as anything other than `NONE`.
- An unanswered row is `OPEN`, not a default.
- Record the owner answer verbatim. If the answer is partial, mark the
  remaining half `OPEN` explicitly (precedent: ruling 4, GST half unanswered).
- If the owner answer conflicts with a repository policy file, stop and ask a
  reconciliation question. Do not silently prefer either side.

## Rule 1 — Evidence, not prose

Every claim in output carries: command, exit code, counts, and a SHA-256 of the
log. Historical narrative values (0.80, 0.99, n=114, Brier tables) are narrative
artifacts until reproduced from actual claim records and may not score current
measurement quality.

## Rule 2 — The three-lineage rule

| Lineage | Identity | Allowed operation |
|---|---|---|
| A | `main` (public, protected, `required_linear_history`) | canonical; every change enters via PR, squash only |
| B | board138 runtime (`work/owner-brain-p0-fix` @ `570c856`) | read as the deployed-runtime record; never rewrite |
| C | Obsidian vault (separate repo, zero merge-base) | export-only, onto a branch that already shares history with `ofn-node` |

Common ancestor of every org path: `c1969bc` = `backup/board138-20260830`.
Never force-push, never graft, never rebase published history, never
squash-merge a vault dump, never `--admin` bypass.

## Rule 3 — Forbidden without an explicit written owner answer

- merge or deploy anything
- open D1 or D7, generate `OWNER_KEY`, rotate secrets
- turn on `live_sms`, `live_dm`, `live_email`, `auto_scrape`, `auto_post`, `auto_dm`
- set `OFN_KEEP_GATES_OPEN`
- print any secret value (only `SET` / `NOT_SET` / count)
- write a revenue, sale, send or booking number that was not read from the ledger
- delete a file or a branch (move to archive instead)
- publish vault history

## Rule 4 — Output contract

Each prompt ends with exactly one receipt file under
`docs/octopus-surgery/receipts/` or `docs/operations/`, plus one PR to `main`.
Verdicts are limited to: `CONFIRMED`, `REFUTED`, `UNTESTABLE`, `OPEN`.
"probably", "should work", "logically must" ⇒ the mission failed.
