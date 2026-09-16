# 🧪 NBB-CP-KRE REGISTRY

```yaml
entity_id: KreReality
name: nbb-cp-kre
version: 0.2.0
kind: read-only-viz-brain
owner: Ari
status: active
risk_level: low
risk_tier: R0
autonomy_floor: read-only analysis (no vault writes ever)
role_in_ecosystem: KNOWLEDGE_REALITY_VIZ
control_contract: ReadOnlyGuard (kernel/guard.py) — single write choke-point
adapter: streamlit + watchdog + plotly
runbook: README-FA.md
public_alias: Knowledge Reality
boss_alignment: read-only observability layer over the Octopus vault
safety_invariants: [INV-2, INV-4, INV-9, INV-11, INV-12]
```

---

## What it does (one line)

Walks the vault read-only, builds the real `[[wikilink]]` graph, runs a
representation bakeoff on held-out link prediction, and renders it as **18
graphical representations** (2D / 3D / animated / statistical / matrix).

---

## Hard contract

- **Vault is read-only.** The single filesystem write path is
  `ReadOnlyGuard.open_write`; writing inside the vault raises
  `ReadOnlyViolation` (fail closed).
- **Outputs live OUTSIDE the vault** (`F:\kre-out` by default).
- **Verdicts are advisory.** Approving a missing-link proposal writes to
  `verdicts.json` only — applying it to notes is a separate human act (INV-2).

---

## Live features (v0.2)

| feature | mechanism |
|---|---|
| file watcher | `watchdog` background thread over the vault |
| auto-refresh | `st.fragment(run_every=15)` polls `pending.json` |
| cache | bakeoff keyed on graph fingerprint (`cache_<fp>.json`) |
| live-click | `read_note_body()` opens one note for reading, quarantined (INV-9) |

---

## Launch

```bat
start.bat              REM one-click (UTF-8 console, streamlit run)
run_dashboard.bat      REM installs deps then runs
python -m pytest -q    REM 21 tests
```

Port: `8501` (Streamlit default).

---

## Current registry verdict

```text
Knowledge Reality is a pure read-only visualisation brain. It observes the
vault and renders 18 views; it never writes inside it. Safe to run at will.
```
