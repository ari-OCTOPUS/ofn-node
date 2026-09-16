#!/usr/bin/env python3
"""M6 — module_self_manifest: a read-only registry of Octopus's OWN code black
boxes. Fixes audit Axis-1 (Black-Box Mapping 2/5): the module named "registry"
governs vault PROJECTS, not the ~140 code modules; self_model maps imports but not
trust-boundaries and is stale. This builds ONE queryable manifest, per module:
purpose · entrypoints · depends_on · imported_by (reverse dep) · wire_flags — plus
a global resolved wire_flag_state (which subsystems are actually armed right now)
and an innervation freshness snapshot. Additive · default-OFF · read-only.

WHY THIS IS PURELY ADDITIVE
  It REUSES self_model.build_model() (the existing, tested, read-only AST scan) and
  augments it — no new parser, no edits to self_model. Output goes to a NEW file
  state/cortex/module-manifest.json (never touches self-model.json). Standalone,
  like M3: it adds ZERO edits to any existing file → the running system is
  byte-identical until the owner runs it (or wires the optional beat hook).

FLAG (default OFF)
  OCTOPUS_WIRE_MODULE_MANIFEST=1   gate the optional per-beat auto-refresh
  (on_beat()). The CLI / RUN-MODULE-MANIFEST.bat always works on demand (an
  explicit owner action). With no flag AND no manual run, nothing happens.

READ-ONLY: build_manifest() only reads code + flags + innervation; the only write
  is the manifest file itself, produced when the owner runs it (or arms on_beat).

CLI
  RUN-MODULE-MANIFEST.bat        → build + write state/cortex/module-manifest.json + summary.
  python module_self_manifest.py --dry   → build + print summary, write NOTHING.

OPTIONAL beat hook (NOT wired — documented delta; add if you want auto-refresh):
  if os.environ.get("OCTOPUS_WIRE_MODULE_MANIFEST")=="1":
      __import__("now_moves.module_self_manifest", fromlist=["on_beat"]).on_beat(beat)

ROLLBACK: delete _ops/now_moves/module_self_manifest.py (+ RUN-MODULE-MANIFEST.bat).
  No existing file changes.

$0 · stdlib-only · fail-soft.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent          # _ops/now_moves
_OPS = _HERE.parent                              # _ops

FLAG = "OCTOPUS_WIRE_MODULE_MANIFEST"
_EVERY_N_ENV = "OCTOPUS_MODULE_MANIFEST_EVERY_N"
_DEFAULT_EVERY_N = 1440
_beat_state = {"last_epoch": -1}


def _self_model():
    try:
        p = str(_OPS / "cortex")
        if p not in sys.path:
            sys.path.insert(0, p)
        import self_model
        return self_model
    except Exception:
        return None


def _opslib():
    try:
        p = str(_OPS / "budget")
        if p not in sys.path:
            sys.path.insert(0, p)
        import opslib
        return opslib
    except Exception:
        return None


def _flag_on(flag: str) -> bool:
    """Resolve a wire flag's current state: env==1 OR _ops/<flag>.flag exists."""
    try:
        if os.environ.get(flag) == "1":
            return True
        return (_OPS / f"{flag}.flag").exists()
    except Exception:
        return False


def _organ_freshness() -> dict:
    try:
        p = str(_OPS / "cortex")
        if p not in sys.path:
            sys.path.insert(0, p)
        import innervation
        chk = innervation.check()
        return {o.get("id"): {"status": o.get("status"), "age_min": o.get("age_min"),
                              "connected": o.get("connected")}
                for o in chk.get("organs", [])}
    except Exception:
        return {}


def _modname(rel: str) -> str:
    return rel.rsplit("/", 1)[-1][:-3] if rel.endswith(".py") else rel.rsplit("/", 1)[-1]


def build_manifest(root=None) -> dict:
    """Read-only. Reuse self_model.build_model(), augment with reverse-deps +
    resolved wire_flag_state + innervation freshness. Never raises."""
    sm = _self_model()
    if sm is None:
        return {"error": "self_model unavailable", "schema": "module-manifest.v1"}
    try:
        model = sm.build_model(Path(root) if root else None)
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}", "schema": "module-manifest.v1"}
    modules = model.get("modules", {}) or {}

    imported_by: dict = {}
    for rel, info in modules.items():
        who = _modname(rel)
        for dep in (info.get("house_imports") or []):
            imported_by.setdefault(dep, set()).add(who)

    flags = model.get("wire_flags", []) or []
    flag_state = {f: _flag_on(f) for f in flags}

    out_modules = {}
    for rel, info in modules.items():
        out_modules[rel] = {
            "purpose": info.get("purpose", ""),
            "entrypoints": info.get("top_defs", []),
            "n_funcs": info.get("n_funcs", 0),
            "wire_flags": info.get("wire_flags", []),
            "depends_on": info.get("house_imports", []),
            "imported_by": sorted(imported_by.get(_modname(rel), [])),
        }

    ops = _opslib()
    ts = ops.now_iso() if ops is not None else ""
    return {
        "ts": ts, "schema": "module-manifest.v1",
        "n_modules": model.get("n_modules", len(modules)),
        "self_awareness_pct": model.get("self_awareness_pct"),
        "n_wire_flags": len(flags),
        "n_flags_armed": sum(1 for v in flag_state.values() if v),
        "wire_flag_state": flag_state,
        "organs": _organ_freshness(),
        "undocumented": model.get("undocumented", []),
        "modules": out_modules,
    }


def _manifest_path():
    ops = _opslib()
    if ops is None:
        return None
    try:
        return ops.STATE_DIR / "cortex" / "module-manifest.json"
    except Exception:
        return None


def write_manifest(root=None, path=None) -> dict:
    """Build + write the manifest. Returns the manifest (with 'written': path|None)."""
    import json
    m = build_manifest(root)
    p = Path(path) if path else _manifest_path()
    m["written"] = None
    if p:
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
            m["written"] = str(p)
        except Exception:
            pass
    return m


def on_beat(beat: int = 0) -> dict | None:
    """Optional flag-gated per-beat auto-refresh (NOT wired by default)."""
    if os.environ.get(FLAG) != "1":
        return None
    try:
        every_n = int(os.environ.get(_EVERY_N_ENV, str(_DEFAULT_EVERY_N)))
    except (TypeError, ValueError):
        every_n = _DEFAULT_EVERY_N
    if beat <= 0 or every_n <= 0:
        return None
    epoch = beat // every_n
    if epoch <= _beat_state["last_epoch"]:
        return None
    _beat_state["last_epoch"] = epoch
    try:
        return write_manifest()
    except Exception:
        return None


def main(argv=None) -> int:
    import json
    argv = list(sys.argv[1:] if argv is None else argv)
    m = build_manifest() if "--dry" in argv else write_manifest()
    armed = [f for f, v in (m.get("wire_flag_state") or {}).items() if v]
    dead = [k for k, o in (m.get("organs") or {}).items() if o.get("connected") is False]
    print(json.dumps({"n_modules": m.get("n_modules"),
                      "self_awareness_pct": m.get("self_awareness_pct"),
                      "n_flags_armed": m.get("n_flags_armed"), "armed": sorted(armed),
                      "dead_organs": dead, "written": m.get("written"),
                      "error": m.get("error", "")},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
