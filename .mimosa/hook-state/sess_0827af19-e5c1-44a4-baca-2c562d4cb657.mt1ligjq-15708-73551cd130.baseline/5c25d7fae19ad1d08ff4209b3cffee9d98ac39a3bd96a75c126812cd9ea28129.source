#!/usr/bin/env python3
"""M1 — ledger_integrity_probe: detection-only wrapper that runs the genome
ledger's OWN verifier from genesis and, on a broken/forked chain, opens an
incident. Additive · default-OFF · read-only-first.

Fixes (audit):
  FM-3  silent forked hash-chain in the genome ledger (row ~39) — never detected
        because nothing recomputes the chain from genesis on the running loop.
  FM-4  the /ops "incidents" card is permanently empty (open_incident is never
        called in production) — this probe gives it a real, self-refreshing feed.

WHY THIS IS PURELY ADDITIVE
  The genome ledger (07 - Knowledge/genome-system/ledger/ledger.py) ALREADY ships
  `Ledger.verify()` (full genesis recompute) and `Ledger.verify_scar_aware()` (a
  read-only torn-line diagnostic). The capability exists; it is simply never
  called periodically. This module is thin GLUE: it calls the existing verifier
  and routes a non-clean result into `events.open_incident(...)`. It writes
  NOTHING to the ledger/genome and computes no new chain of its own.

CONTAINMENT (§10)
  The verifiers return only positions + reasons (e.g. "chain break at record N:
  prev mismatch") — never row contents. `open_incident()` additionally scrubs.
  This module never reads, prints, stores, or echoes ledger row payloads.

VERDICTS
  clean    — strict verify() passes (chain roots to genesis, no tamper).
  scarred  — strict fails but verify_scar_aware() passes: a torn-but-anchored
             write; history is NOT rewritten, the chain honestly continues.
             Surfaced as risk R4-pending (recoverable, owner-aware), not R4.
  broken   — both verifiers fail: a genuine fork/tamper. Surfaced as risk R4.
  absent   — ledger file does not exist (treated ok).
  unknown  — verifier could not be loaded / unexpected error (fail-soft, no emit).

FLAG (default OFF — with it unset the organism behaves exactly as before)
  OCTOPUS_WIRE_LEDGER_PROBE=1    enable the per-beat hook (on_beat()).
  OCTOPUS_LEDGER_PROBE_EVERY_N   beats between checks on the beat path (default 720
                                 ≈ 12h at 1s beat). Edge-crossing throttle (house
                                 idiom: epoch = beat // every_n), so an exact
                                 multiple is never missed.
  OCTOPUS_LEDGER_PATH            override the ledger.jsonl DATA path (else resolved
                                 from GENOME_DIR env, else repo-relative).
  OCTOPUS_LEDGER_PY              override the ledger.py CODE path (else repo-relative).

READ-ONLY vs ACTION
  verify_ledger()   PURE read-only. Returns a content-free verdict dict. No writes.
  probe(emit=False) verify_ledger + (only if emit=True) one open_incident on a
                    non-clean chain. emit defaults False → read-only by default.
  on_beat(beat)     the flag-gated per-beat entry: honors the kill-switch, throttles,
                    then probe(emit=True). It runs ONLY when the owner has set
                    OCTOPUS_WIRE_LEDGER_PROBE=1 — i.e. the incident state-write is
                    gated behind an explicit human flag (§rule-6).
  acknowledge()     owner action: snapshot the current verdict as the accepted
                    baseline (writes one tiny state/now_moves/*.json; emits NOTHING).
                    Thereafter the probe alerts only on a chain strictly WORSE than
                    the accepted baseline — so a known scar does not re-alarm.
  CLI               default is read-only (verify only). --emit writes an incident
                    (only if worse than baseline). --acknowledge accepts current
                    state. Exit code: 1 only if verdict == "broken", else 0.

CALL-SITE (the single sanctioned edit — organism.py beat dispatch, flag-gated):
  if os.environ.get("OCTOPUS_WIRE_LEDGER_PROBE") == "1":
      __import__("now_moves.ledger_integrity_probe",
                 fromlist=["on_beat"]).on_beat(beat)

ROLLBACK
  1) Delete _ops/now_moves/ledger_integrity_probe.py.
  2) Remove the one flag-gated line at organism.py (grep OCTOPUS_WIRE_LEDGER_PROBE).
  Either alone — or simply leaving the flag unset — returns the system to its exact
  prior state: the flag defaults OFF and no other module imports this one.

$0 · stdlib-only · fail-soft · does not repair anything (repair = owner-only).
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent          # _ops/now_moves
_OPS = _HERE.parent                              # _ops
_ROOT = _OPS.parent                              # repo root (worktree or F:\backup)

FLAG = "OCTOPUS_WIRE_LEDGER_PROBE"
_EVERY_N_ENV = "OCTOPUS_LEDGER_PROBE_EVERY_N"
_DATA_ENV = "OCTOPUS_LEDGER_PATH"
_PY_ENV = "OCTOPUS_LEDGER_PY"
_DEFAULT_EVERY_N = 720

_LEDGER_REL = Path("07 - Knowledge") / "genome-system" / "ledger" / "ledger.jsonl"
_LEDGER_PY_REL = Path("07 - Knowledge") / "genome-system" / "ledger" / "ledger.py"

_beat_state = {"last_epoch": -1}
_ledger_class = None
_ledger_class_tried = False


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except (TypeError, ValueError):
        return default


def _ledger_data_path() -> Path:
    """Resolve the ledger.jsonl DATA path: explicit override → GENOME_DIR env →
    repo-relative. (Data path may be redirected in tests / on live.)"""
    p = os.environ.get(_DATA_ENV)
    if p:
        return Path(p)
    gd = os.environ.get("GENOME_DIR")
    if gd:
        return Path(gd) / "ledger" / "ledger.jsonl"
    return _ROOT / _LEDGER_REL


def _ledger_py_path() -> Path:
    """Resolve the ledger.py CODE path. The verifier code ships with the repo, so
    this is repo-relative by default (NOT tied to GENOME_DIR, which points at data)."""
    p = os.environ.get(_PY_ENV)
    return Path(p) if p else (_ROOT / _LEDGER_PY_REL)


def _load_ledger_class():
    """Import the genome Ledger class by file path (its dir name contains a space
    and is not a package). Cached. Returns the class or None (fail-soft)."""
    global _ledger_class, _ledger_class_tried
    if _ledger_class_tried:
        return _ledger_class
    _ledger_class_tried = True
    py = _ledger_py_path()
    if not py.exists():
        return None
    try:
        spec = importlib.util.spec_from_file_location("_genome_ledger_probe", str(py))
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod             # required before exec: @dataclass reads sys.modules[__module__]
        spec.loader.exec_module(mod)             # ledger.py is stdlib-only, side-effect-free
        _ledger_class = getattr(mod, "Ledger", None)
    except Exception:
        _ledger_class = None
    return _ledger_class


def verify_ledger(ledger_path=None) -> dict:
    """PURE READ-ONLY. Run the ledger's own verify() + verify_scar_aware() from
    genesis. Returns a content-free verdict. Never writes, never raises."""
    path = Path(ledger_path) if ledger_path else _ledger_data_path()
    out = {"path": str(path), "exists": path.exists(), "verdict": "unknown",
           "ok": None, "strict_ok": None, "scar_ok": None,
           "strict_msg": "", "scar_msg": "", "error": ""}
    if not path.exists():
        out.update(verdict="absent", ok=True, strict_ok=True, scar_ok=True)
        return out
    Ledger = _load_ledger_class()
    if Ledger is None:
        out.update(error="genome ledger verifier unavailable")
        return out
    try:
        lg = Ledger(path)
        s_ok, s_msg = lg.verify()
        out["strict_ok"], out["strict_msg"] = bool(s_ok), str(s_msg)[:200]
        try:
            sc_ok, sc_msg = lg.verify_scar_aware()
            out["scar_ok"], out["scar_msg"] = bool(sc_ok), str(sc_msg)[:200]
        except Exception as e:
            out["scar_ok"], out["scar_msg"] = None, f"scar-verify error: {type(e).__name__}"
        if s_ok:
            out.update(verdict="clean", ok=True)
        elif out["scar_ok"]:
            out.update(verdict="scarred", ok=True)     # torn-but-anchored, honest
        else:
            out.update(verdict="broken", ok=False)     # genuine fork/tamper
    except Exception as e:
        out.update(error=f"{type(e).__name__}: {e}"[:200])
    return out


def _emit_incident(v: dict, risk: str) -> bool:
    """Route a non-clean verdict into events.open_incident. Content-free, fail-soft.
    Lazy import: `events` is touched ONLY on an actual non-clean chain — never on a
    clean beat, and never at module import."""
    try:
        if str(_OPS) not in sys.path:
            sys.path.insert(0, str(_OPS))
        import events                                    # _ops/events.py
        msg = v.get("strict_msg") or v.get("scar_msg") or "ledger chain verify failed"
        events.open_incident(
            "ledger",
            what="genome ledger chain integrity failed",
            where="07 - Knowledge/genome-system/ledger/ledger.jsonl",
            risk=risk,
            policy="owner-only repair (re-root vs quarantine) — no auto-repair",
            evidence=str(msg)[:160],
            next_action="بررسیِ مالک — تعمیرِ ledger فقط با رأیِ انسان",
            summary=f"ledger integrity: {v.get('verdict')} — {msg}"[:200])
        return True
    except Exception:
        return False


# ── accepted-baseline (owner said "accept the line-40 scar + monitor future") ──
# The probe remembers the worst state it has already surfaced. It emits an
# incident ONLY when the current chain is strictly WORSE than that accepted
# baseline — so a known, acknowledged scar does not re-alarm every cycle, while a
# NEW break / extra scar / earlier break still fires. Baseline = one tiny JSON in
# state/now_moves/ (NOT the ledger/genome). Deleting it just re-arms a fresh alert.
_SEVERITY = {"clean": 0, "absent": 0, "unknown": -1, "scarred": 1, "broken": 2}


def _baseline_path():
    try:
        if str(_OPS / "budget") not in sys.path:
            sys.path.insert(0, str(_OPS / "budget"))
        import opslib
        return opslib.STATE_DIR / "now_moves" / "ledger-probe-baseline.json"
    except Exception:
        return None


def _parse_scar_count(scar_msg: str) -> int:
    m = re.search(r"\[([^\]]*)\]", scar_msg or "")
    return len([x for x in m.group(1).split(",") if x.strip()]) if m else 0


def _parse_break_record(strict_msg: str):
    m = re.search(r"record (\d+)", strict_msg or "")
    return int(m.group(1)) if m else None


def _signature(v: dict) -> dict:
    return {"verdict": v.get("verdict"),
            "severity": _SEVERITY.get(v.get("verdict"), -1),
            "scars": _parse_scar_count(v.get("scar_msg", "")),
            "break_record": _parse_break_record(v.get("strict_msg", ""))}


def _worse_than(cur: dict, base) -> bool:
    """cur strictly worse than the accepted baseline (None baseline = first sight)."""
    if base is None:
        return True
    if cur["severity"] > base.get("severity", -1):
        return True
    if cur["scars"] > base.get("scars", 0):
        return True
    cb, bb = cur.get("break_record"), base.get("break_record")
    if cb is not None and bb is not None and cb < bb:   # break moved earlier → more history affected
        return True
    return False


def _read_baseline():
    p = _baseline_path()
    if not p or not p.exists():
        return None
    try:
        return json.loads(p.read_text("utf-8"))
    except Exception:
        return None


def _write_baseline(sig: dict, acknowledged: bool) -> bool:
    p = _baseline_path()
    if not p:
        return False
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        rec = dict(sig); rec["acknowledged"] = acknowledged
        p.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
        return True
    except Exception:
        return False


def acknowledge(ledger_path=None) -> dict:
    """Owner action (read-only-first + explicit): snapshot the CURRENT verdict as
    the accepted baseline so the per-beat probe stays silent about it and only
    alerts on future WORSENING. Writes ONE tiny baseline file; emits NO incident."""
    v = verify_ledger(ledger_path)
    v["acknowledged"] = _write_baseline(_signature(v), acknowledged=True)
    return v


def probe(emit: bool = False, ledger_path=None) -> dict:
    """verify_ledger + (only if emit) open ONE incident when the chain is strictly
    worse than the accepted baseline. emit=False (default) → pure read-only.
    broken→R4, scarred→R4-pending. A known/acknowledged scar does not re-alarm."""
    v = verify_ledger(ledger_path)
    v["emitted"] = False
    if not emit:
        return v
    verdict = v.get("verdict")
    if verdict in ("clean", "absent", "unknown"):    # nothing to alert / can't judge
        return v
    cur = _signature(v)
    if _worse_than(cur, _read_baseline()):
        risk = "R4" if verdict == "broken" else "R4-pending"
        v["emitted"] = _emit_incident(v, risk=risk)
        _write_baseline(cur, acknowledged=False)     # remember what we alerted on → auto-quiets next cycle
    return v


def on_beat(beat: int = 0) -> dict | None:
    """Flag-gated per-beat entry. No-op unless OCTOPUS_WIRE_LEDGER_PROBE=1.
    Honors the kill-switch (parity with other beat reflexes), throttles by
    OCTOPUS_LEDGER_PROBE_EVERY_N, then read-only verify + incident-on-break."""
    if os.environ.get(FLAG) != "1":
        return None
    try:                                                 # kill-switch first (fail-soft)
        if str(_OPS / "budget") not in sys.path:
            sys.path.insert(0, str(_OPS / "budget"))
        import opslib
        if opslib.STOP_ORGANISM.exists() or opslib.halted():
            return None
    except Exception:
        pass
    every_n = _int_env(_EVERY_N_ENV, _DEFAULT_EVERY_N)
    if beat <= 0 or every_n <= 0:
        return None
    epoch = beat // every_n
    if epoch <= _beat_state["last_epoch"]:
        return None
    _beat_state["last_epoch"] = epoch
    try:
        return probe(emit=True)
    except Exception:
        return None


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    path = None
    if "--path" in argv:
        i = argv.index("--path")
        if i + 1 < len(argv):
            path = argv[i + 1]
    if "--acknowledge" in argv:
        v = acknowledge(ledger_path=path)          # accept current state, emit nothing
    else:
        v = probe(emit="--emit" in argv, ledger_path=path)
    print(json.dumps(v, ensure_ascii=False, indent=2))
    return 1 if v.get("verdict") == "broken" else 0


if __name__ == "__main__":
    sys.exit(main())
