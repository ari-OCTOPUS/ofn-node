#!/usr/bin/env python3
"""mission_runner.py — Runner v0: اجرای ایزوله و evidence-محورِ missionهای کم‌ریسک.

حلقهٔ گم‌شدهٔ Mission Genome: تا امروز `mission.py` فقط state می‌ساخت و کارت نشان می‌داد؛
هیچ‌کس plan را «اجرا» نمی‌کرد. این ماژول آن گره را می‌بندد — اما فقط برای اکشن‌های
allowlisted و فقط در محیطِ ایزوله (git worktree)، با artifact و ثبتِ صادقانه.

قرارداد v0 (اصلِ دوکلیدی — بدون هر دو کلید apply ناممکن):
  * ALLOWLIST = code.plan / code.test / code.diff / doctor.review / epistemics.review
    (همه read/low-risk؛ هیچ‌کدام requires_approval نیستند).
  * هر اکشنِ دیگر (code.patch/code.apply/code.rollback/evolution.*/mission.next)
    **هرگز اجرا نمی‌شود** — فقط `skipped` با دلیل ثبت می‌شود (owner-gated / out-of-scope).
  * code.test فقط فایل‌های `test_*.py` را در worktree ایزوله (از HEAD همان vault) با
    `REAL_VAULT=<worktree>` اجرا می‌کند؛ درختِ زنده هرگز لمس نمی‌شود.
  * evidence: `_agent_reports/missions/<mid>/run-<stamp>/` (run.json + log هر تست + plan/diff).
  * ثبت از طریق APIِ خودِ mission: record_test / record_review / add_note / set_state /
    refresh_fitness — status بدون artifact هرگز «passed» نمی‌شود.

ناوردی‌ها (هم‌خانوادهٔ mission.py):
  * stdlib-only، import-time خالص، fail-soft، نوشتنِ اتمیک برای run.json.
  * subprocess فقط با argv ثابت (git worktree / git diff / python test)؛ هرگز shell از
    متنِ کاربر؛ هرگز push/commit/merge/branch-delete؛ هرگز شبکه؛ هرگز خواندنِ token.
  * containment: هیچ رشتهٔ ممنوع (_BANNED_ECHO) وارد artifact/state نمی‌شود.
  * ضدِ اجرای دوباره: run زندهٔ تازه (<۱۵ دقیقه) → refuse (idempotency در برابر retry).

تست: `_ops/tests/test_tg_mission_runner.py` (worktree/test-cmd تزریقی + یک ریپوی واقعی کوچک).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from dataclasses import asdict
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
if str(_OPS / "budget") not in sys.path:
    sys.path.insert(0, str(_OPS / "budget"))

try:
    import mission  # noqa: E402
except Exception:  # noqa: BLE001
    from . import mission  # type: ignore  # noqa: E402
try:
    import action_graph  # noqa: E402
except Exception:  # noqa: BLE001
    from . import action_graph  # type: ignore  # noqa: E402
try:
    import context_bundle as _context_bundle  # noqa: E402
except Exception:  # noqa: BLE001
    _context_bundle = None  # type: ignore

# ── قرارداد v0 ────────────────────────────────────────────────────────────────
ALLOWLIST = ("code.plan", "code.test", "code.diff", "doctor.review", "epistemics.review")
_ELIGIBLE_STATES = ("created", "planned", "approved")
_TESTFILE_RE = re.compile(r"^test_[A-Za-z0-9_]+\.py$")
_DEFAULT_TESTS = ("test_tg_actions.py",)   # کوچک/سریع/قطعی — وقتی plan تست مشخص ندارد
_RUN_STALE_S = 15 * 60                     # runِ «زنده» کهنه‌تر از این = مرده فرض می‌شود
_TEST_TIMEOUT_S = 300
_LOG_TAIL = 4000                           # سقفِ ذخیرهٔ خروجیِ هر تست در artifact

_BANNED = tuple(getattr(mission, "_BANNED_ECHO", ("اونلی", "onlyfans", "صبا")))


def _scrub(s: object, cap: int = 400) -> str:
    txt = str(s if s is not None else "")[:cap]
    low = txt.lower()
    for b in _BANNED:
        if b in low or b in txt:
            return "(redacted:containment)"
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", txt)


def _now_stamp() -> str:
    return time.strftime("%Y%m%d-%H%M%S", time.localtime())


def _atomic_write_json(path: Path, data: dict) -> bool:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
        os.replace(tmp, path)
        return True
    except (OSError, TypeError, ValueError):
        return False


def _vault_root(explicit: "Path | str | None") -> Path:
    if explicit:
        return Path(explicit).resolve()
    return _OPS.parent


def _runs_dir(vault: Path, mid: str) -> Path:
    return vault / "_agent_reports" / "missions" / mission._safe_id(mid)


# ── ایزولاسیون (hooks تزریق‌پذیر برای تست) ─────────────────────────────────────
def _real_worktree_add(vault: Path) -> "Path | None":
    """worktree تازه از HEAD همان vault در tmp. شکست → None (fail-soft)."""
    import tempfile
    wt = Path(tempfile.mkdtemp(prefix="octo-runner-wt-"))
    try:
        r = subprocess.run(["git", "worktree", "add", "--detach", str(wt), "HEAD"],
                           cwd=str(vault), capture_output=True, text=True, timeout=180)
        return wt if r.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def _real_worktree_remove(vault: Path, wt: Path) -> bool:
    try:
        r = subprocess.run(["git", "worktree", "remove", "--force", str(wt)],
                           cwd=str(vault), capture_output=True, text=True, timeout=120)
        return r.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def _real_run_test(wt: Path, test_name: str) -> tuple[int, str]:
    """اجرای یک فایل تست در worktree با REAL_VAULT=worktree. خروجی = (rc, tail)."""
    tf = wt / "_ops" / "tests" / test_name
    if not tf.exists():
        return (127, f"test file missing in worktree: {test_name}")
    env = dict(os.environ)
    env["REAL_VAULT"] = str(wt)
    try:
        r = subprocess.run([sys.executable, "-X", "utf8", str(tf)],
                           cwd=str(wt), capture_output=True, text=True,
                           timeout=_TEST_TIMEOUT_S, env=env)
        out = (r.stdout or "") + ("\n" + r.stderr if r.stderr else "")
        return (r.returncode, out[-_LOG_TAIL:])
    except subprocess.TimeoutExpired:
        return (124, f"timeout>{_TEST_TIMEOUT_S}s")
    except (OSError, subprocess.SubprocessError) as e:  # noqa: BLE001
        return (1, f"runner error: {e!r}"[:300])


def _real_diff_stat(wt: Path) -> str:
    try:
        r = subprocess.run(["git", "diff", "--stat"], cwd=str(wt),
                           capture_output=True, text=True, timeout=60)
        return (r.stdout or "").strip() or "(clean worktree — zero diff)"
    except (OSError, subprocess.SubprocessError):
        return "(diff unavailable)"


_DEFAULT_HOOKS = {
    "worktree_add": _real_worktree_add,
    "worktree_remove": _real_worktree_remove,
    "run_test": _real_run_test,
    "diff_stat": _real_diff_stat,
}


# ── هستهٔ Runner ──────────────────────────────────────────────────────────────
def runnable_missions(limit: int = 10) -> list[dict]:
    """missionهای واجدِ اجرا (state واجد + حداقل یک اکشنِ allowlisted)."""
    out = []
    for m in mission.list_missions(states=_ELIGIBLE_STATES, limit=limit):
        if any(a in ALLOWLIST for a in (m.get("actions") or [])):
            out.append(m)
    return out


def _duplicate_running(runs: Path) -> bool:
    """آیا runِ زندهٔ تازه‌ای هست؟ (idempotency در برابر retry/crash)"""
    try:
        if not runs.exists():
            return False
        for d in runs.iterdir():
            rj = d / "run.json"
            if rj.exists():
                try:
                    data = json.loads(rj.read_text("utf-8"))
                except (OSError, ValueError):
                    continue
                if data.get("status") == "running" and \
                        (time.time() - rj.stat().st_mtime) < _RUN_STALE_S:
                    return True
    except OSError:
        pass
    return False


def run_mission(mid: str, *, vault_root: "Path | str | None" = None,
                tests: "tuple[str, ...] | None" = None,
                hooks: "dict | None" = None,
                dry_run: bool = False) -> dict:
    """اجرای v0 یک mission: فقط اکشن‌های allowlisted، فقط در worktree، با artifact.

    خروجی همیشه dict با کلید `ok` است؛ هرگز raise نمی‌کند (fail-soft)."""
    hk = dict(_DEFAULT_HOOKS)
    hk.update(hooks or {})
    vault = _vault_root(vault_root)
    m = mission.get(mid)
    if not m:
        return {"ok": False, "refused": "mission_not_found", "mid": _scrub(mid, 80)}
    if m.get("state") not in _ELIGIBLE_STATES:
        return {"ok": False, "refused": "state_not_eligible", "state": m.get("state")}

    actions = [a for a in (m.get("actions") or [])]
    todo = [a for a in actions if a in ALLOWLIST]
    skipped = [{"action": a,
                "reason": ("owner-gated" if action_graph.requires_owner_approval(a)
                           else "out-of-scope-v0")}
               for a in actions if a not in ALLOWLIST]
    if not todo:
        return {"ok": False, "refused": "no_allowlisted_actions", "skipped": skipped}

    runs = _runs_dir(vault, m["id"])
    if _duplicate_running(runs):
        return {"ok": False, "refused": "duplicate_run"}

    if dry_run:
        return {"ok": True, "dry_run": True, "would_run": todo, "skipped": skipped}

    run_id = f"run-{_now_stamp()}"
    art = runs / run_id
    head = {"mid": m["id"], "run_id": run_id, "status": "running",
            "started_at": mission._now_iso(), "actions": todo, "skipped": skipped}
    if not _atomic_write_json(art / "run.json", head):
        return {"ok": False, "refused": "artifact_write_failed"}
    # Narrow machine handoff: task state is offloaded into a typed phase bundle rather
    # than replaying mission/chat history into every specialist.
    if _context_bundle is not None:
        try:
            bundle = _context_bundle.ContextBundle.create(
                mission_id=m.get("mission_id") or m["id"],
                task_id=m.get("task_id") or f"task-{m['id']}",
                trace_id=m.get("trace_id") or f"trace-{m['id']}",
                tenant_id=m.get("tenant_id") or "personal",
                project_id=m.get("project_id") or "octopus-core",
                agent_role="mission_runner", phase="verify",
                objective=m.get("owner_intent") or "verify mission",
                constraints=["allowlisted actions only", "no live-tree mutation"],
                verified_facts=[f"risk={m.get('risk')}", f"state={m.get('state')}"],
                tool_allowlist=["git-worktree", "python-test"],
                output_contract={"run.json": "required", "test logs": "on code.test"})
            _atomic_write_json(art / "context-bundle.json", asdict(bundle))
        except Exception:  # noqa: BLE001 — context packaging never weakens runner containment
            pass

    results: list[dict] = []
    wt = None
    test_names = tuple(t for t in (tests or ()) if _TESTFILE_RE.match(str(t)))
    all_tests_passed: "bool | None" = None

    try:
        for aid in todo:
            t0 = time.time()
            rec: dict = {"action": aid, "ok": False}
            if aid == "code.plan":
                ok = _atomic_write_json(art / "plan.json",
                                        {"mid": m["id"], "plan": m.get("plan") or []})
                rec.update(ok=ok, evidence="plan.json")
            elif aid == "code.test":
                if wt is None:
                    wt = hk["worktree_add"](vault)
                if wt is None:
                    rec.update(ok=False, error="worktree_unavailable")
                else:
                    names = test_names or _plan_tests(m) or _DEFAULT_TESTS
                    passed_all = True
                    for name in names:
                        rc, out = hk["run_test"](wt, name)
                        log = art / f"test-{mission._safe_id(name)}.log"
                        try:
                            log.parent.mkdir(parents=True, exist_ok=True)
                            log.write_text(_scrub(out, _LOG_TAIL), "utf-8")
                        except OSError:
                            pass
                        p = (rc == 0)
                        passed_all = passed_all and p
                        mission.record_test(m["id"], name, p,
                                            detail=f"exit={rc} run={run_id} evidence={log.name}")
                        rec.setdefault("tests", []).append({"name": name, "exit": rc, "passed": p})
                    all_tests_passed = passed_all
                    rec.update(ok=passed_all)
            elif aid == "code.diff":
                target = wt if wt is not None else vault
                txt = hk["diff_stat"](target)
                try:
                    (art / "diff.txt").write_text(_scrub(txt, 8000), "utf-8")
                    rec.update(ok=True, evidence="diff.txt")
                except OSError:
                    rec.update(ok=False)
            elif aid == "doctor.review":
                # read-only snapshot: doctor فقط از روی شواهدِ همین run قضاوت می‌کند.
                ok = bool(all_tests_passed) if all_tests_passed is not None else True
                n_rfc = _count_rfcs(vault)
                mission.record_review(m["id"], "doctor", ok,
                                      detail=f"read-only run={run_id} tests_ok={all_tests_passed} rfcs={n_rfc}")
                rec.update(ok=ok, rfcs=n_rfc)
            elif aid == "epistemics.review":
                # evidence-check واقعی: artifactها موجود، JSON سالم، صفر نشتِ containment.
                ok, why = _epistemic_check(art)
                mission.record_review(m["id"], "epistemics", ok,
                                      detail=f"run={run_id} {why}")
                rec.update(ok=ok, why=why)
            rec["seconds"] = round(time.time() - t0, 2)
            results.append(rec)
    finally:
        if wt is not None:
            hk["worktree_remove"](vault, wt)

    ok_all = all(bool(r.get("ok")) for r in results)
    tail = {"mid": m["id"], "run_id": run_id,
            "status": "done" if ok_all else "failed",
            "finished_at": mission._now_iso(),
            "results": results, "skipped": skipped}
    _atomic_write_json(art / "run.json", tail)

    mission.add_note(m["id"], f"runner {run_id}: {'green' if ok_all else 'red'} "
                              f"({len(results)} actions, {len(skipped)} skipped owner-gated)")
    mission.refresh_fitness(m["id"])
    final = mission.get(m["id"]) or {}
    if final.get("approval") == "required":
        mission.set_state(m["id"], "awaiting_owner", note=f"evidence:{run_id}")
    return {"ok": ok_all, "run_id": run_id, "artifacts": str(art),
            "results": results, "skipped": skipped}


def _plan_tests(m: dict) -> tuple[str, ...]:
    names: list[str] = []
    for step in (m.get("plan") or []):
        for t in (step.get("tests") or []):
            t = str(t)
            if _TESTFILE_RE.match(t) and t not in names:
                names.append(t)
    return tuple(names)


def _count_rfcs(vault: Path) -> int:
    try:
        p = vault / "_ops" / "state" / "doctor" / "rfcs.json"
        if p.exists():
            d = json.loads(p.read_text("utf-8"))
            return len(d) if isinstance(d, list) else len(d.get("rfcs", []) or [])
    except (OSError, ValueError):
        pass
    return 0


def _epistemic_check(art: Path) -> tuple[bool, str]:
    try:
        rj = art / "run.json"
        if not rj.exists():
            return False, "run.json missing"
        json.loads(rj.read_text("utf-8"))
        for p in art.iterdir():
            if p.is_file() and p.suffix in (".json", ".txt", ".log"):
                txt = p.read_text("utf-8", errors="replace")
                low = txt.lower()
                for b in _BANNED:
                    if b in low or b in txt:
                        return False, f"containment-leak:{p.name}"
        return True, "artifacts-ok"
    except (OSError, ValueError) as e:  # noqa: BLE001
        return False, f"check-error:{e.__class__.__name__}"


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Mission Runner v0 — allowlisted, isolated, evidence-first")
    ap.add_argument("--mid", help="run one mission by id")
    ap.add_argument("--all", action="store_true", help="run every runnable mission")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if a.mid:
        print(json.dumps(run_mission(a.mid, dry_run=a.dry_run), ensure_ascii=False, indent=2))
    elif a.all:
        outs = [run_mission(m["id"], dry_run=a.dry_run) for m in runnable_missions()]
        print(json.dumps(outs, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({"runnable": [m.get("id") for m in runnable_missions()]},
                         ensure_ascii=False, indent=2))
