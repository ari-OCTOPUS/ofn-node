# -*- coding: utf-8 -*-
"""Coordinator + cycle runner.

OBSERVE → DIAGNOSE → HYPOTHESIZE → REPRODUCE → PATCH → TEST → VERIFY
→ SHADOW → PROMOTE_OR_ROLLBACK → LEARN

Experimental patches land only in isolated git worktrees. Paid calls forbidden.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

_OPS = Path(__file__).resolve().parent.parent
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

from self_upgrade_lab import LAB_DIR, ROOT, STATE_DIR
from self_upgrade_lab.api_router import inventory as api_inventory
from self_upgrade_lab.contracts import (
    Experiment, MAX_CYCLE_MINUTES, append_jsonl, ensure_state_dirs,
    new_ids, utc_now, write_json,
)
from self_upgrade_lab.diagnoser import diagnose
from self_upgrade_lab.experiment import ensure_worktree, record_experiment
from self_upgrade_lab.hypothesis import make_hypothesis
from self_upgrade_lab.learning_writer import write_learning
from self_upgrade_lab.patch_runner import apply_splices, apply_unified_diff, write_files
from self_upgrade_lab.promoter import promote
from self_upgrade_lab.rollback import rollback, rollback_probe
from self_upgrade_lab.scanner import scan as scan_self
from self_upgrade_lab.test_runner import run_many, run_one
from self_upgrade_lab.verifier import verify


BRAIN_TEST = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S-A03: improve must consume calibration-latest (propose-only, never auto)."""
import inspect
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE.parent), str(_HERE.parent / "cortex"), str(_HERE.parent / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import harness  # noqa: E402
harness.setup("improve-calibration")
import improve  # noqa: E402


def t_a_generate_proposals_emits_calibration():
    signals = {
        "matrix": {"gaps": []},
        "doctor_rfcs": [],
        "smallest_fix": "",
        "synthesis": {},
        "idea": {},
        "calibration": {"n": 12, "brier": 0.21, "ungraded": 3, "ts": "t"},
    }
    props = improve.generate_proposals(signals)
    cal = [p for p in props if p.get("source") == "calibration"]
    assert cal, {"n": len(props), "sources": [p.get("source") for p in props[:8]]}
    assert cal[0].get("auto_applicable") is False
    assert cal[0].get("change_level") == "tune"
    assert "calibration-latest.json" in str(cal[0].get("evidence"))


def t_b_source_reads_calibration_latest():
    assert "calibration-latest.json" in inspect.getsource(improve.gather_signals)
    assert "calibration" in inspect.getsource(improve.generate_proposals)


if __name__ == "__main__":
    failed = 0
    for name, fn in sorted((n, f) for n, f in globals().items() if n.startswith("t_")):
        try:
            fn()
            print(f"  OK  {name}")
        except Exception as e:
            failed += 1
            print(f"  FAIL {name}: {type(e).__name__}: {e}")
    print(f"\ntest_improve_reads_calibration: {2 - failed}/2")
    sys.exit(1 if failed else 0)
'''

HEART_OBSERVE_TEST = '''

def t_g_observe_only_never_restarts_missing_gateway():
    w, root = _fresh()
    rows = [{"Pid": 50, "Parent": 1, "Cmd": "launcher"}]
    rep = w.tick(rows=rows, state={}, now=1000.0, observe_only=True)
    kinds = [a["kind"] for a in rep["actions"]]
    assert "restart" not in kinds, rep
    assert "missing_gateway_observed" in kinds, rep
    st = json.loads(w.state_path().read_text(encoding="utf-8")) if w.state_path().is_file() else {}
    assert int(st.get("restarts") or 0) == 0


def t_h_observe_only_orphan_child_still_not_restarted():
    w, root = _fresh()
    rep = w.tick(rows=_rows(parent_alive=False), state={}, now=1000.0, observe_only=True)
    kinds = [a["kind"] for a in rep["actions"]]
    assert "orphan_receipt" in kinds and "restart" not in kinds, rep
'''

ORGANISM_HOOK = '''        try:
            import orphan_watchdog as _ow_obs  # noqa: WPS433
            _ow_obs.tick(observe_only=True)
        except Exception:  # noqa: BLE001 — observe-only, never kill the beat
            pass
'''


def _lease_path(layer: str) -> Path:
    return STATE_DIR / f"lease-{layer}.json"


def acquire_lease(layer: str, minutes: int = MAX_CYCLE_MINUTES) -> bool:
    p = _lease_path(layer)
    now = time.time()
    if p.is_file():
        try:
            rec = json.loads(p.read_text(encoding="utf-8"))
            if float(rec.get("until") or 0) > now and rec.get("pid") != os.getpid():
                return False
        except (OSError, ValueError):
            pass
    write_json(p, {"layer": layer, "pid": os.getpid(), "until": now + minutes * 60,
                   "ts": utc_now()})
    return True


def release_lease(layer: str) -> None:
    p = _lease_path(layer)
    try:
        p.unlink()
    except OSError:
        pass


def _git(worktree: Path, args: list[str], timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=str(worktree), capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=timeout)


def shadow_memory_reads(n: int = 10) -> dict:
    db = _OPS / "state" / "memory" / "memory.db"
    if not db.is_file():
        return {"n": 0, "mutations": 0, "note": "memory.db-missing"}
    import hashlib
    import sqlite3
    h1 = hashlib.sha256(db.read_bytes()).hexdigest()[:16]
    queries = ["calibration", "telegram", "brain", "doctor", "memory",
               "self", "event", "wave", "owner", "loop"]
    hits = []
    uri = "file:" + db.resolve().as_posix() + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    try:
        for q in queries[:n]:
            try:
                rows = conn.execute(
                    "SELECT memory_id FROM memory WHERE content LIKE ? OR mkey LIKE ? LIMIT 3",
                    (f"%{q}%", f"%{q}%")).fetchall()
            except sqlite3.Error as exc:
                hits.append({"q": q, "n": 0, "err": type(exc).__name__})
                continue
            hits.append({"q": q, "n": len(rows), "non_empty": bool(rows)})
    finally:
        conn.close()
    h2 = hashlib.sha256(db.read_bytes()).hexdigest()[:16]
    return {
        "n": n, "hits": hits, "non_empty": sum(1 for h in hits if h.get("non_empty")),
        "hash_before": h1, "hash_after": h2,
        "mutations": 0 if h1 == h2 else 1, "mode": "sqlite-uri-ro",
    }


def _patch_memory(worktree: Path, allow: list[str]) -> dict:
    diff = LAB_DIR / "patches" / "memory-gate-tests.diff"
    if diff.is_file():
        return apply_unified_diff(worktree, diff, allow)
    # fallback: copy live passing test (still allowlisted)
    src = ROOT / "_ops/tests/test_memory_gate.py"
    return write_files(worktree, {"_ops/tests/test_memory_gate.py": src.read_text(encoding="utf-8")},
                       allow)


def _patch_brain_test_only(worktree: Path, allow: list[str]) -> dict:
    return write_files(worktree, {
        "_ops/tests/test_improve_reads_calibration.py": BRAIN_TEST,
    }, allow)


BRAIN_CAL_READ = '''    # 2026-08-20 — S-A03: calibration-latest was DEAD-OUTPUT for improve.
    # Read-only, propose-only. Missing/corrupt file → {}.
    calibration = {}
    try:
        cal = _read(STATE / "cortex" / "calibration-latest.json") or {}
        if isinstance(cal, dict) and (
                cal.get("n") is not None or cal.get("brier") is not None):
            calibration = {
                "n": cal.get("n"), "brier": cal.get("brier"),
                "aurc": cal.get("aurc"), "ungraded": cal.get("ungraded"),
                "n_claims": cal.get("n_claims"), "ts": cal.get("ts"),
            }
    except Exception:  # noqa: BLE001
        calibration = {}
'''

BRAIN_CAL_PROP = '''    # ۲.۶b) 2026-08-20 S-A03 — calibration-latest → propose-only (never auto).
    cal = signals.get("calibration") or {}
    if cal.get("brier") is not None or cal.get("n") is not None:
        brier = cal.get("brier")
        n_cal = cal.get("n")
        ungraded = cal.get("ungraded")
        out.append({
            "id": _pid("calibration:latest"), "source": "calibration",
            "category": "ops", "priority": "P1", "_rank": 0.9,
            "title": f"کالیبراسیون: n={n_cal} brier={brier} ungraded={ungraded}",
            "rationale": "Brier/n/ungraded از calibration-latest — تا امروز به improve نمی‌رسید.",
            "evidence": "cortex/calibration-latest.json",
            "suggested_action": "رتبهٔ پیشنهادها را با Brier و پوشش ungraded وزن بده (propose-only).",
            "change_level": "tune", "auto_applicable": False, "status": "proposed",
            "calibration": cal,
        })
'''


def _patch_brain_improve(worktree: Path, allow: list[str]) -> dict:
    rel = "_ops/cortex/improve.py"
    p = worktree / rel
    if not p.is_file():
        return {"ok": False, "reason": "missing", "file": rel}
    text = p.read_text(encoding="utf-8")
    if "calibration-latest.json" in text and 'source": "calibration"' in text:
        return {"ok": True, "already": True, "files": [rel]}
    splices: list[tuple[str, str]] = []
    if "calibration-latest.json" not in text:
        needle = (
            "    except Exception:  # noqa: BLE001\n"
            "        math_control = {}\n"
            "    return {\"matrix\": matrix,"
        )
        if needle not in text:
            return {"ok": False, "reason": "anchor-not-found", "file": rel,
                    "anchor": "math_control-return"}
        splices.append((
            needle,
            needle.replace(
                "    return {\"matrix\": matrix,",
                BRAIN_CAL_READ + "    return {\"matrix\": matrix,",
            ),
        ))
    if '"calibration": calibration}' not in text:
        old_ret = '            "math_control": math_control}'
        if old_ret not in text:
            return {"ok": False, "reason": "anchor-not-found", "file": rel,
                    "anchor": "math_control-key"}
        splices.append((
            old_ret,
            '            "math_control": math_control,\n            "calibration": calibration}',
        ))
    if 'source": "calibration"' not in text:
        syn = "    # ۲.۵) از سنتزِ مغز"
        if syn not in text:
            return {"ok": False, "reason": "anchor-not-found", "file": rel,
                    "anchor": "synthesis"}
        splices.append((syn, BRAIN_CAL_PROP + syn))
    return apply_splices(worktree, rel, splices, allow)


def _patch_heart_failing_test(worktree: Path, allow: list[str]) -> dict:
    rel = "_ops/tests/test_orphan_watchdog.py"
    p = worktree / rel
    text = p.read_text(encoding="utf-8")
    if "t_g_observe_only_never_restarts_missing_gateway" in text:
        return {"ok": True, "already": True, "files": [rel]}
    needle = "\ndef main() -> int:\n"
    if needle not in text:
        return {"ok": False, "reason": "anchor-not-found", "file": rel}
    return write_files(worktree, {rel: text.replace(needle, HEART_OBSERVE_TEST + needle, 1)}, allow)


def _patch_heart_impl(worktree: Path, allow: list[str]) -> dict:
    a = apply_splices(worktree, "_ops/orphan_watchdog.py", [
        (
            "def recovery_plan(gateways: list[dict], rows: list[dict],\n"
            "                  state: dict | None = None, now: float | None = None) -> list[dict]:",
            "def recovery_plan(gateways: list[dict], rows: list[dict],\n"
            "                  state: dict | None = None, now: float | None = None,\n"
            "                  observe_only: bool = False) -> list[dict]:",
        ),
        (
            "    if not gateways:\n"
            "        if now - float(state.get(\"window_start\") or 0) >= WINDOW_S:",
            "    if not gateways:\n"
            "        if observe_only:\n"
            "            actions.append({\"kind\": \"missing_gateway_observed\",\n"
            "                            \"restart\": False, \"observe_only\": True})\n"
            "            _save_state(state)\n"
            "            return actions\n"
            "        if now - float(state.get(\"window_start\") or 0) >= WINDOW_S:",
        ),
        (
            "def tick(rows: list[dict] | None = None, state: dict | None = None,\n"
            "         now: float | None = None) -> dict:\n"
            "    \"\"\"One watchdog pass: snapshot → classify → plan → receipts → report.\"\"\"\n"
            "    rows = rows if rows is not None else _cim_rows()\n"
            "    gateways = snapshot(rows)\n"
            "    actions = recovery_plan(gateways, rows, state=state, now=now)",
            "def tick(rows: list[dict] | None = None, state: dict | None = None,\n"
            "         now: float | None = None, observe_only: bool = False) -> dict:\n"
            "    \"\"\"One watchdog pass: snapshot → classify → plan → receipts → report.\"\"\"\n"
            "    rows = rows if rows is not None else _cim_rows()\n"
            "    gateways = snapshot(rows)\n"
            "    actions = recovery_plan(gateways, rows, state=state, now=now,\n"
            "                            observe_only=observe_only)",
        ),
    ], allow)
    if not a.get("ok"):
        return a
    b = apply_splices(worktree, "_ops/organism.py", [
        (
            "        except Exception:  # noqa: BLE001 — ضربانِ سایه هرگز ضربانِ اصلی را نمی‌کشد\n"
            "            pass\n"
            "        try:\n",
            "        except Exception:  # noqa: BLE001 — ضربانِ سایه هرگز ضربانِ اصلی را نمی‌کشد\n"
            "            pass\n"
            + ORGANISM_HOOK +
            "        try:\n",
        ),
    ], allow)
    if not b.get("ok"):
        return b
    return {"ok": True, "files": ["_ops/orphan_watchdog.py", "_ops/organism.py"],
            "patch_hash": (a.get("patch_hash") or "") + (b.get("patch_hash") or "")}


def _commit_worktree(worktree: Path, files: list[str], message: str) -> dict:
    _git(worktree, ["add", "--", *files])
    r = _git(worktree, ["commit", "-m", message])
    head = _git(worktree, ["rev-parse", "HEAD"])
    return {
        "ok": r.returncode == 0,
        "stderr": (r.stderr or "")[-300:],
        "stdout": (r.stdout or "")[-200:],
        "commit": (head.stdout or "").strip(),
    }


def run_lane(layer: str, diagnosis: dict, scan: dict,
             time_budget_s: int = MAX_CYCLE_MINUTES * 60) -> dict:
    t0 = time.time()
    if not acquire_lease(layer):
        rec = {"layer": layer, "blocked": True, "reason": "lease-held", "ts": utc_now()}
        append_jsonl(STATE_DIR / "failures.jsonl", rec)
        return rec
    cycle_id, _, exp_id = new_ids(layer)
    hyp = make_hypothesis(layer, diagnosis)
    try:
        wt = ensure_worktree(layer, cycle_id, base="HEAD")
        worktree = Path(wt["path"])
        allow = list(hyp.files_allowed)
        tests = list(hyp.tests_required)

        # REPRODUCE (before)
        if layer == "brain":
            _patch_brain_test_only(worktree, allow)
        if layer == "heart":
            _patch_heart_failing_test(worktree, allow)
        before = run_many(worktree, tests, timeout_s=90)
        st = _git(worktree, ["status", "--porcelain", "--", *allow, *tests])
        dirty = bool((st.stdout or "").strip())
        if before.get("all_pass") and not dirty:
            rec = {
                "cycle_id": cycle_id, "layer": layer, "target": hyp.target_id,
                "decision": "ALREADY_FIXED", "promotion_level": "NONE",
                "verifier": {"confirmed": False, "reasons": ["already-green-on-head"],
                             "label": "ALREADY_FIXED",
                             "note": "Worktree HEAD already satisfies the targeted tests; lab will not restage it."},
                "tests": {"before": before, "after": before},
                "elapsed_s": round(time.time() - t0, 2), "blockers": [],
                "worktree": str(worktree),
            }
            write_json(STATE_DIR / "latest-cycle.json", rec)
            append_jsonl(STATE_DIR / "cycles.jsonl", rec)
            return rec

        # PATCH
        if layer == "memory":
            patch = _patch_memory(worktree, allow)
        elif layer == "brain":
            patch = _patch_brain_improve(worktree, allow)
        else:
            patch = _patch_heart_impl(worktree, allow)
        if not patch.get("ok"):
            rb = rollback(worktree, allow, reason=str(patch.get("reason")))
            exp = Experiment(exp_id, hyp.hypothesis_id, str(worktree),
                             before_metrics=before, tests={}, after_metrics={},
                             verifier={"confirmed": False, "reasons": [patch]},
                             decision="REJECT")
            record_experiment(exp)
            lid = write_learning(
                layer=layer, hypothesis=hyp.to_dict(), experiment=exp.to_dict(),
                predicted_ok=False,
                statement=f"patch apply failed: {patch.get('reason')}",
                evidence_refs=hyp.evidence_refs, confidence=0.4)
            return {"cycle_id": cycle_id, "layer": layer, "decision": "REJECT",
                    "patch": patch, "learning_id": lid, "elapsed_s": round(time.time() - t0, 2)}

        after = run_many(worktree, tests, timeout_s=90)
        extra = {}
        if layer == "memory":
            extra["timeout_isolation"] = {
                "read_loop": run_one(worktree, "_ops/tests/test_memory_read_loop.py", timeout_s=60),
            }
        shadow = shadow_memory_reads(10) if layer == "memory" and after.get("all_pass") else None
        rb_ok = rollback_probe(worktree)
        files = list(dict.fromkeys(
            (patch.get("files") or allow) + (tests if layer != "memory" else [])
        ))
        if layer == "memory":
            files = ["_ops/tests/test_memory_gate.py"]
        if layer == "brain":
            files = ["_ops/cortex/improve.py", "_ops/tests/test_improve_reads_calibration.py"]
        if layer == "heart":
            files = ["_ops/orphan_watchdog.py", "_ops/organism.py",
                     "_ops/tests/test_orphan_watchdog.py"]
        ver = verify(worktree=worktree, files=files, before=before, after=after,
                     tests=after, rollback_ok=rb_ok, memory_write=False)
        if ver.get("confirmed"):
            comm = _commit_worktree(
                worktree, files,
                f"sul/{layer}: {hyp.target_id} lab-pass ({cycle_id})")
            promo = promote(experiment_id=exp_id, verifier=ver, shadow=shadow,
                            canary_ok=False)
            decision = "PROMOTE"
            level = promo["level"]
        else:
            rollback(worktree, [f for f in files if f.exists()] if False else files,
                     reason=";".join(ver.get("reasons") or ["verifier-false"]))
            comm = {"ok": False, "skipped": True}
            promo = {"level": "NONE"}
            decision = "REJECT"
            level = "NONE"
        exp = Experiment(
            exp_id, hyp.hypothesis_id, str(worktree),
            before_metrics=before, patch_hash=str(patch.get("patch_hash") or ""),
            tests=after, after_metrics={**after, **extra},
            verifier=ver, decision=decision, promotion_level=level)
        predicted_ok = after.get("all_pass") is True
        lid = write_learning(
            layer=layer, hypothesis=hyp.to_dict(), experiment=exp.to_dict(),
            predicted_ok=predicted_ok,
            statement=hyp.predicted_result if predicted_ok else hyp.root_cause_candidate,
            evidence_refs=hyp.evidence_refs + [str(worktree)],
            confidence=0.86 if predicted_ok else 0.55)
        exp.learning_id = lid
        record_experiment(exp)
        out = {
            "cycle_id": cycle_id,
            "layer": layer,
            "target": hyp.target_id,
            "hypothesis_id": hyp.hypothesis_id,
            "experiment_id": exp_id,
            "root_cause": hyp.root_cause_candidate,
            "hypothesis": hyp.predicted_result,
            "patch": {k: patch.get(k) for k in ("ok", "patch_hash", "files", "reason") if k in patch or True},
            "tests": {"before": before, "after": after, "extra": extra},
            "before_metrics": before,
            "after_metrics": after,
            "verifier": ver,
            "decision": decision,
            "promotion_level": level,
            "rollback": rb_ok,
            "learning_id": lid,
            "commit": comm,
            "shadow": shadow,
            "worktree": str(worktree),
            "elapsed_s": round(time.time() - t0, 2),
            "blockers": [] if ver.get("confirmed") else ver.get("reasons"),
        }
        write_json(STATE_DIR / "latest-cycle.json", out)
        append_jsonl(STATE_DIR / "cycles.jsonl", {k: out[k] for k in out if k != "tests"})
        return out
    finally:
        release_lease(layer)



def run_rfc_cycle(rfc: dict, **kwargs) -> dict:
    """Thin RFC-seeded cycle. Isolated worktree only; never promotes to live."""
    from self_upgrade_lab.rfc_cycle import run_rfc_cycle as _impl
    return _impl(rfc, **kwargs)

def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    ensure_state_dirs()
    execute = "--execute" in argv or not argv
    apis = api_inventory()
    observed = scan_self()
    diag = diagnose(observed)
    write_json(STATE_DIR / "latest-scan.json", {"scan": {"ts": observed.get("ts"),
                                                         "n_files": len(observed.get("files") or []),
                                                         "open_loops": len(observed.get("open_loops") or [])},
                                                "diagnosis": {"weakest": (diag.get("weakest") or {}).get("id"),
                                                              "ranked": [(r["id"], r["priority_score"])
                                                                         for r in diag.get("ranked") or []]}})
    if not execute:
        print(json.dumps({"scan_ts": observed.get("ts"), "weakest": diag.get("weakest"),
                          "apis": apis["local"]}, ensure_ascii=False, indent=2))
        return 0
    # Memory first (P0), then heart + brain. Independent leases. Don't idle on a blocker.
    order = ["memory", "heart", "brain"]
    reports = []
    for layer in order:
        try:
            reports.append(run_lane(layer, diag, observed))
        except Exception as exc:  # noqa: BLE001 — one lane must not halt the others
            rec = {"layer": layer, "error": type(exc).__name__, "msg": str(exc)[:300],
                   "ts": utc_now()}
            append_jsonl(STATE_DIR / "failures.jsonl", rec)
            reports.append(rec)
    milestone = {
        "MILESTONE": "SELF_UPGRADE_LAB_CYCLE",
        "ts": utc_now(),
        "accepted_checkpoint": "3200e8f",
        "weakest": diag.get("weakest"),
        "api": {"paid_calls": "FORBIDDEN", "local": apis["local"]},
        "lanes": reports,
    }
    write_json(STATE_DIR / "milestone-SELF_UPGRADE_LAB_CYCLE.json", milestone)
    print(json.dumps(milestone, ensure_ascii=False, indent=2, default=str))
    return 0 if any(r.get("decision") in ("PROMOTE", "ALREADY_FIXED")
                    for r in reports if isinstance(r, dict)) else 1


if __name__ == "__main__":
    raise SystemExit(main())
