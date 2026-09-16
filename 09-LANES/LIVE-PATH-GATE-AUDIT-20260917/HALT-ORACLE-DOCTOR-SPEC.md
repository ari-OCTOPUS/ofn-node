---
type: design
status: draft
tags: [octopus, od-1, halt-oracle, doctor, read-only, design]
updated: 2026-09-17
project: "[[OCTOPUS]]"
---

# HALT-ORACLE DOCTOR — SPEC (read-only) — OD-1 clause 3–5

`GOV_VERSION=V8 · LADDER=L2 · status: SPEC ONLY (not built) · date: 2026-09-17`
`authority: owner ruling OD-1 Option B, 2026-09-17`
`no create · no delete · no arm · no restart · no env change · no patch`

> This is a **specification**, not code and not an authorization to run. OD-1 clause 6
> forbids arming, creating, deleting, or restarting anything. Clause 3 authorizes the
> doctor to be **built read-only**; running it against live hardware requires a
> separate authorized plan (§5).

---

## 1. Purpose

Answer, with machine-readable evidence and no mutation: **for each Octopus process,
which halt file does it actually resolve and read, what state is that file in, and does
the documentation agree?** Every disagreement is loud.

The doctor exists because of two verified defects:
- **D-3 — path fragmentation.** Four halt conventions coexist; the one named in
  `AGENTS.md` GOV-V7 (`F:\ofn-node\HALT`) does not exist. Since
  `ofn/kernel/halt.py:26` defines **absent = RUNNING**, arming the documented switch
  fails *silently*.
- **D-9 — coverage gap.** Even with the right file armed, the Telegram publish path
  and paid-model spend never consult it (`node.py:3607` uses the in-process
  `self.killed`; `ofn/kernel/callbudget.py:28` states "HALT is not a parameter").
  A doctor that reported only *resolution* would certify a system whose halt coverage
  is partial. It must report **coverage** too.

---

## 2. Hard prohibitions (from the owner ruling, clause 6)

The doctor MUST NOT, under any flag or mode:

1. create, delete, rename, truncate, chmod, symlink, or **arm** any HALT file;
2. restart, start, stop, reload, or `systemctl`-mutate any service or timer;
3. change any environment variable, budget file, gate file, or systemd unit;
4. write anywhere except its own append-only receipt directory;
5. make a network request;
6. import the live `ofn` package in its static half (see §3, Half A); **one bounded
   exception is defined in §8.1** (`ofn.kernel.halt` only, justified and mechanically
   guarded). Any second `ofn` import is a stop condition.

A run that cannot satisfy these must exit `BLOCKED_BY_SAFETY` with a reason — never
degrade to "best effort".

---

## 3. Two halves, deliberately split

### Half A — static / offline (buildable now, laptop-side)

Reads code only. For each halt-reading site, resolve the path the module *would*
compute for a declared `HOME`, and diff it against the documented path.

Inputs: `F:\ofn-node` (read-only), a declared `HOME` (parameter, not inherited from
the environment), and the documented oracle path(s) extracted from the vault.

Mechanism: enumerate halt-reading sites by AST/regex over the module set
(`master_halted`, `halt_flag_active`, `is_halted`, plus literal `HALT` path
construction), evaluate the path expressions (`<HOME>/ofn/HALT-ALL`, `<root>/HALT`,
caller-supplied), and emit a table:

| site (`path:line`) | resolved path (for declared HOME) | reads it? | documented? | verdict |
|---|---|---|---|---|

Verdict vocabulary is exactly one of **`WIRED` / `TESTED_ONLY` / `DOC_ONLY` /
`UNVERIFIED`** — never "safe", never "covered", never a boolean.

Known sites this half must find (verified 2026-09-17; the scanner must rediscover
them, not hardcode them):

| Site | Resolves to |
|---|---|
| `ofn/budget/opslib.py:20` (+ readers `:28`) | `<HOME>/ofn/HALT-ALL`, and `HALT_SURVIVAL_LOOP=1` |
| `ops/ign1_telegram_ignite.py:28` | `<repo-root>/HALT` |
| `ofn/adapters/run_gate.py:35` | *caller-supplied* `self._halt_path` — **no production constructor** |
| `ofn/adapters/halt_log.py:228` | *caller-supplied* `flag_path` |
| `ofn/node.py:3607` | **none** — in-process `self.killed` |
| `ofn/adapters/remote_brain.py:88` | **none** (spend path) |

### Half B — on-node (NOT AUTHORIZED YET)

Read-only observation on a live host, requiring its own approved plan. Per service:
identity, commit/runtime identity, the path actually resolved at runtime, file state
(`absent` / `present` / `malformed` / `unreadable` / `symlink`), predicate state
(`RUNNING` / `HALTED` / `UNKNOWN`), and legacy halt files discovered.

**It still may not arm anything.** File state is observed, never changed.

---

## 4. Coverage amendment (required)

Per the audit report §E.3, the doctor must emit, for every egress-bearing consumer, a
**coverage row** in addition to resolution:

```
consumer | egress path:line | consults canonical oracle? | what stops it instead | severity
```

Consumers that consult **no** oracle — at minimum the Telegram publish path
(`node.py:3607`) and hosted-model spend (`remote_brain.py:88`) — must appear as
explicit rows with `consults_canonical_oracle: false` and a severity, **not** as
missing entries. Omitting them would reproduce the original defect in a new artifact.

---

## 5. Receipt format (append-only, fail-loud)

One JSON object per mismatch, appended to `receipts/halt-doctor.jsonl`. Never edited.

```json
{
  "schema": "octopus.halt-doctor.v1",
  "observed_at_utc": "<ISO8601>",
  "half": "A_static | B_on_node",
  "host_identity": "<declared; never a secret>",
  "runtime_identity": {"commit": "<sha>", "source": "git rev-parse HEAD | declared"},
  "canonical_oracle": "<path>",
  "documented_oracle": "<path from docs>",
  "mismatch": {
    "kind": "path_divergence | undocumented | orphan_file | coverage_gap | malformed",
    "severity": "info | warn | high | critical",
    "reason": "<exact reason, one line>",
    "paths_involved": ["<path>", "..."],
    "consumers": ["<module:line>", "..."],
    "owner_action_required": true
  },
  "verdict": "WIRED | TESTED_ONLY | DOC_ONLY | UNVERIFIED",
  "mutations_performed": 0
}
```

**`mutations_performed` is mandatory and must always be `0`.** A non-zero value means
the doctor violated clause 6 and the run is an incident, not a result.

`mismatch.owner_action_required` is `true` whenever resolution would require a runtime
or governance change — i.e. for D-3's canonical-oracle correction and for every D-9
coverage gap.

---

## 6. Acceptance criteria (for whoever builds it)

1. Static half runs offline; makes no network request; writes only under `receipts/`.
2. Every halt-reading site in §3 is **rediscovered by the scanner**, not hardcoded —
   demonstrated by adding a synthetic site in a temp tree and seeing it reported.
3. Coverage rows appear for the §D.2 consumers, with `consults_canonical_oracle: false`.
4. `mutations_performed` is `0` on every receipt; a negative test proves the doctor
   cannot create/delete/arm a flag (plant an attempted write, assert `BLOCKED_BY_SAFETY`).
5. Verdicts use only the four allowed values; no "safe"/"covered" string appears.
6. Re-running on an unchanged tree produces byte-identical receipts except
   `observed_at_utc`.
7. Explicit pass/fail counts published — "no errors" is not a result.

---

## 7. What this spec deliberately does not do

- It does not canonicalize anything. Clause 1 of OD-1 is **decided but forbidden to
  execute** until a separate authorized plan exists.
- It does not create, delete, or arm a HALT file. Ever.
- It does not propose a patch. A patch proposal may follow a completed doctor run, as
  a **separate** artifact, and still may not be applied without owner approval.

---

## 8. Offline fixture harness (OD-4 deliverable 1)

Added 2026-09-17 under OD-4. The harness is what makes the doctor **testable without a
node**. It runs entirely in a temporary directory, creates no service, reads no live
path, and writes only inside its own temp tree and `receipts/`.

### 8.1 The one permitted import (and why it is not a hole)

§2 clause 6 and §3 Half A forbid importing the live `ofn` package. There is exactly one
exception, and it is bounded:

> **Tier 2 may import `ofn.kernel.halt` — and nothing else from `ofn`.**

Justification, verified 2026-09-17:
- `ofn/kernel/halt.py` imports only `__future__` and `typing`.
- `ofn/kernel/__init__.py` imports the rest of the kernel package, all of which is
  **contractually pure** and test-enforced: *"Hard rules, enforced by
  `tests/test_kernel_purity.py`: stdlib only — no third-party imports, ever; no I/O, no
  clock, no environment, no filesystem."*

The reason for the exception is a rule this project already holds: **testing a
reimplementation proves nothing.** A harness that re-typed `is_halted()` and then
asserted it agrees with itself would be the same defect as a fixture that embeds the
answer.

**Mechanical guard, not a promise** — Tier 2 must, at runtime:
1. assert the transitive import set of `ofn.kernel.halt` contains no non-stdlib module
   and none of `socket`, `subprocess`, `urllib`, `http`, `ssl`, `sqlite3`, `os`, `pathlib`;
2. assert importing it did **not** increase the set of open file descriptors or add a
   `socket`/`sqlite3` module to `sys.modules`;
3. refuse to run (fail-closed) if either assertion fails.

Any need for a second `ofn` import is a **stop condition**, not a config flag.

### 8.2 Tier 1 — resolver fixtures (no `ofn` import)

Synthetic trees under a temp dir; the harness drives the doctor's own resolver and
compares against the expected resolved path.

| Fixture | Tree | Expected |
|---|---|---|
| F1 | `$HOME/ofn/HALT-ALL` = `"1"` | resolves to canonical oracle; documented == code |
| F2 | only `$ROOT/HALT` exists (the ignition's convention) | **reported as legacy/orphan**; mismatch high |
| F3 | neither file exists | resolves; state `absent` ⇒ predicate RUNNING (correct, not an error) |
| F4 | documented oracle path does not exist while code oracle does | **path_divergence, severity high, owner_action_required true** — this is D-3 encoded as a test |
| F5 | two different halt files exist simultaneously | **undocumented, severity high** |

### 8.3 Tier 2 — predicate fixtures (uses the allowlisted predicate)

For each state, assert the predicate's verdict. These pin the fail-closed behaviour the
audit relies on, so a future edit that weakens it fails here.

| File state | Expected `is_halted` |
|---|---|
| absent | `False` (RUNNING — absence is the normal state) |
| `"1"` / `"true"` / `"yes"` / `"on"` | `True` |
| `"0"` / `"false"` / `"no"` / `"off"` | `False` |
| `""` (empty) | `True` — unparsable intent |
| `"maybe"` (foreign vocabulary) | `True` |
| random binary bytes (non-UTF-8) | `True` |
| symlink to a normal file | `True` — a planted link is not a verifiable flag |
| directory at the flag path | `True` — read raises, treated as unreadable |
| chmod 000 (unreadable) | `True` |

### 8.4 Tier 3 — coverage fixtures

Asserts that §4's coverage rows appear for consumers that consult **no** oracle. Fixture
F6 = a synthetic consumer list containing a known non-oracle consumer (modelled on
`node.py:3607`) plus a known oracle consumer (modelled on `outbound_worker.py:214`).
Expected: two rows, `consults_canonical_oracle` `false` and `true` respectively, both
present. A run that omits the `false` row is a **failed** harness, not a warning.

### 8.5 Non-mutation canary (the anti-arming test)

Before and after the whole harness run, hash every file in the fixture tree and record
`st_mtime_ns`. Assert both unchanged. Then **attempt** to arm a flag through the
doctor's API and assert `BLOCKED_BY_SAFETY`. Receipt field `mutations_performed` must be
`0` on every line (§5).

This is the test that would catch the doctor becoming a mutator — the failure mode that
matters most, because a "read-only" tool that can arm a switch is worse than no tool.

### 8.6 Determinism

Two runs over the same fixture tree must produce byte-identical receipts except
`observed_at_utc`. The harness must publish explicit pass/fail counts per tier; "no
errors" is not a result. Tier 1 and Tier 3 must run with **no** `ofn` import at all —
asserted by checking `sys.modules` for any `ofn*` key before and after.

