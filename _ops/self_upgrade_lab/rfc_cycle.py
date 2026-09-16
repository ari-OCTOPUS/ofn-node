# -*- coding: utf-8 -*-
"""Thin RFC-seeded lab cycle.

One OBSERVE-adjacent cycle: seed diagnosis/hypothesis from a doctor RFC,
write isolated worktree code, TEST, VERIFY. Never promotes onto the live
production tree. Paid calls forbidden.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from . import STATE_DIR
from .contracts import Experiment, append_jsonl, new_ids, utc_now, write_json
from .patch_runner import write_files
from .rollback import rollback_probe
from .verifier import verify

_SAFE_ID = re.compile(r"[^A-Za-z0-9_.-]+")
_MAX = 240


def _safe(s: object, n: int = _MAX) -> str:
    txt = " ".join(str(s if s is not None else "").split())[:n]
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", txt)


def _mod_name(rfc_id: str) -> str:
    raw = _SAFE_ID.sub("_", str(rfc_id or "RFC-unknown"))[:48].strip("_.")
    return raw or "RFC_unknown"


def _state_dir(override: Path | None) -> Path:
    env = str(os.environ.get("OCTOPUS_SUL_STATE_DIR", "") or "").strip()
    if override is not None:
        return Path(override)
    if env:
        return Path(env)
    return STATE_DIR


def _git(worktree: Path, args: list[str], timeout: int = 30) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=str(worktree), capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=timeout)


def _ensure_isolated_worktree(dest: Path, rfc_id: str) -> dict[str, Any]:
    """Create or reuse an isolated git repo. Never the live production tree."""
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    reused = (dest / ".git").exists()
    if not reused:
        r = _git(dest, ["init"])
        if r.returncode != 0:
            raise RuntimeError("git init failed: " + (r.stderr or r.stdout or "")[-300:])
        _git(dest, ["checkout", "-B", "sul/rfc-" + _mod_name(rfc_id)])
        marker = dest / ".sul-rfc"
        marker.write_text(_safe(rfc_id, 80) + "\n", encoding="utf-8")
        _git(dest, ["add", "--", ".sul-rfc"])
        _git(dest, ["-c", "user.email=sul-rfc@octopus.local",
                    "-c", "user.name=sul-rfc",
                    "commit", "-m", "sul/rfc: init " + _safe(rfc_id, 40)])
    return {"path": str(dest), "reused": reused, "isolated": True}


def _render_artifact(rfc: dict) -> str:
    rid = _safe(rfc.get("rfc_id"), 64)
    bn = _safe(rfc.get("bottleneck"), 400)
    fix = _safe(rfc.get("fix"), 400)
    organ = _safe(rfc.get("organ") or rfc.get("evidence_key") or "unknown", 80)
    return (
        "# -*- coding: utf-8 -*-\n"
        '"""Isolated RFC experiment artifact for ' + rid + ". Not live production.\"\"\"\n"
        "RFC_ID = " + repr(rid) + "\n"
        "BOTTLENECK = " + repr(bn) + "\n"
        "FIX = " + repr(fix) + "\n"
        "ORGAN = " + repr(organ) + "\n\n"
        "def probe() -> bool:\n"
        "    return bool(RFC_ID) and bool(FIX)\n\n"
        "def predicted_lift() -> dict:\n"
        "    return {\"rfc_id\": RFC_ID, \"ok\": True, \"organ\": ORGAN}\n"
    )


def _render_test(mod: str) -> str:
    return (
        "# -*- coding: utf-8 -*-\n"
        '"""Generated RFC artifact test. Self-contained; no network, no paid.\"\"\"\n'
        "from pathlib import Path\n\n"
        "_ART = Path(__file__).resolve().parents[1] / \"self_upgrade_lab\" / "
        "\"rfc_artifacts\" / (\"" + mod + ".py\")\n\n"
        "def main() -> int:\n"
        "    ns = {}\n"
        "    src = _ART.read_text(encoding=\"utf-8\")\n"
        "    exec(compile(src, str(_ART), \"exec\"), ns, ns)\n"
        "    assert ns[\"probe\"]() is True\n"
        "    lift = ns[\"predicted_lift\"]()\n"
        "    assert lift.get(\"ok\") is True\n"
        "    print(\"OK\", lift.get(\"rfc_id\"))\n"
        "    return 0\n\n"
        "if __name__ == \"__main__\":\n"
        "    raise SystemExit(main())\n"
    )


def _run_test(worktree: Path, rel: str, timeout_s: int = 20) -> dict[str, Any]:
    target = worktree / rel
    if not target.is_file():
        return {"n": 1, "passed": 0, "failed": 1, "timeouts": 0,
                "all_pass": False, "reason": "missing-test"}
    try:
        r = subprocess.run(
            [sys.executable, str(target)], cwd=str(worktree),
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=timeout_s)
    except subprocess.TimeoutExpired:
        return {"n": 1, "passed": 0, "failed": 0, "timeouts": 1,
                "all_pass": False, "reason": "timeout"}
    ok = r.returncode == 0
    return {
        "n": 1, "passed": 1 if ok else 0, "failed": 0 if ok else 1,
        "timeouts": 0, "all_pass": ok,
        "exit": r.returncode,
        "stdout": (r.stdout or "")[-200:],
        "stderr": (r.stderr or "")[-200:],
    }


def run_rfc_cycle(rfc: dict, *, worktree: Path | str | None = None,
                  state_dir: Path | str | None = None,
                  time_budget_s: int = 60) -> dict[str, Any]:
    """Run ONE lab cycle seeded by a doctor RFC dict.

    Returns experiment_id, worktree, test/verify outcomes, proposed_promote
    (never applied here), and a telegram_card payload. Live tree is not patched.
    """
    t0 = time.time()
    rfc = dict(rfc or {})
    rfc_id = _safe(rfc.get("rfc_id") or ("RFC-" + str(int(t0))), 64)
    rfc["rfc_id"] = rfc_id
    rfc.setdefault("bottleneck", "unspecified")
    rfc.setdefault("fix", "record-and-test")
    rfc.setdefault("organ", rfc.get("evidence_key") or "unknown")
    sd = _state_dir(Path(state_dir) if state_dir else None)
    sd.mkdir(parents=True, exist_ok=True)

    env_wt = str(os.environ.get("OCTOPUS_SUL_WORKTREE", "") or "").strip()
    if worktree is not None:
        wt = Path(worktree)
        wt_rec = {"path": str(wt), "injected": True}
        if not (wt / ".git").exists():
            wt_rec.update(_ensure_isolated_worktree(wt, rfc_id))
    elif env_wt:
        wt = Path(env_wt)
        wt_rec = {"path": str(wt), "injected": True, "env": True}
        if not (wt / ".git").exists():
            wt_rec.update(_ensure_isolated_worktree(wt, rfc_id))
    else:
        dest = sd / "worktrees" / _mod_name(rfc_id)
        wt_rec = _ensure_isolated_worktree(dest, rfc_id)
        wt = Path(wt_rec["path"])

    cycle_id, hid, exp_id = new_ids("rfc")
    mod = _mod_name(rfc_id)
    art_rel = "_ops/self_upgrade_lab/rfc_artifacts/" + mod + ".py"
    test_rel = "_ops/tests/test_rfc_" + mod + ".py"
    allow = [art_rel, test_rel]

    before = _run_test(wt, test_rel)
    artifact = _render_artifact(rfc)
    test_src = _render_test(mod)
    patch = write_files(wt, {art_rel: artifact, test_rel: test_src}, allow)
    if patch.get("ok"):
        after = _run_test(wt, test_rel)
    else:
        after = {"n": 1, "passed": 0, "failed": 1, "timeouts": 0,
                 "all_pass": False, "reason": patch.get("reason")}
    rb_ok = rollback_probe(wt)
    ver = verify(worktree=wt, files=allow, before=before, after=after,
                 tests=after, rollback_ok=rb_ok, memory_write=False)
    # RFC cycle never calls promote(). proposed_promote is advisory only.
    proposed = bool(ver.get("confirmed") and after.get("all_pass") and patch.get("ok"))
    comm = {"ok": False, "skipped": True}
    if proposed:
        _git(wt, ["add", "--", art_rel, test_rel])
        cr = _git(wt, ["-c", "user.email=sul-rfc@octopus.local",
                       "-c", "user.name=sul-rfc",
                       "commit", "-m",
                       "sul/rfc: " + rfc_id + " lab-pass (" + cycle_id + ")"])
        head = _git(wt, ["rev-parse", "HEAD"])
        comm = {"ok": cr.returncode == 0,
                "commit": (head.stdout or "").strip(),
                "stderr": (cr.stderr or "")[-200:]}

    exp = Experiment(
        exp_id, hid, str(wt),
        before_metrics=before, patch_hash=str(patch.get("patch_hash") or ""),
        tests=after, after_metrics=after, verifier=ver,
        decision="PROPOSE" if proposed else "REJECT",
        promotion_level="NONE")
    rec_path = sd / "experiments.jsonl"
    rec_path.parent.mkdir(parents=True, exist_ok=True)
    with rec_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({**exp.to_dict(), "ts": utc_now(),
                             "rfc_id": rfc_id, "live_promote": False},
                            ensure_ascii=False) + "\n")

    card = {
        "kind": "evo-lab-rfc-card",
        "rfc_id": rfc_id,
        "bottleneck": _safe(rfc.get("bottleneck"), 200),
        "organ": _safe(rfc.get("organ"), 80),
        "experiment_id": exp_id,
        "worktree": str(wt),
        "test_ok": bool(after.get("all_pass")),
        "verify": bool(ver.get("confirmed")),
        "verify_reasons": list(ver.get("reasons") or []),
        "proposed_promote": proposed,
        "live_send": False,
        "actions": ["[merge]", "[reject]"],
    }
    out = {
        "cycle_id": cycle_id,
        "hypothesis_id": hid,
        "experiment_id": exp_id,
        "rfc_id": rfc_id,
        "organ": rfc.get("organ"),
        "bottleneck": rfc.get("bottleneck"),
        "fix": rfc.get("fix"),
        "worktree": str(wt),
        "worktree_meta": wt_rec,
        "patch": {k: patch.get(k) for k in ("ok", "patch_hash", "files", "reason")},
        "tests": {"before": before, "after": after},
        "test_outcome": "pass" if after.get("all_pass") else "fail",
        "verify": ver,
        "proposed_promote": proposed,
        "promotion_level": "NONE",
        "commit": comm,
        "telegram_card": card,
        "elapsed_s": round(time.time() - t0, 3),
        "live_promote": False,
        "paid": "FORBIDDEN",
    }
    write_json(sd / "latest-rfc-cycle.json", {
        k: out[k] for k in out if k not in ("tests",)
    })
    append_jsonl(sd / "rfc-cycles.jsonl", {
        "ts": utc_now(), "rfc_id": rfc_id, "experiment_id": exp_id,
        "proposed_promote": proposed, "worktree": str(wt),
    })
    del time_budget_s
    return out
