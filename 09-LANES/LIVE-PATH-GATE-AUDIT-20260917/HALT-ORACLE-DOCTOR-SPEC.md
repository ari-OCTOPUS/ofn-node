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
6. import the live `ofn` package in its static half (see §3, Half A).

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
