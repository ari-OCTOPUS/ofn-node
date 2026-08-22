#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RFC -> self-upgrade lab -> durable Telegram outbox. Fixture-only, no network."""
from __future__ import annotations

import ast
import importlib
import json
import os
import sys
import tempfile
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
_DOC = _OPS / "doctor"
_TG = _OPS / "telegram_center"
for _p in (str(_OPS), str(_DOC), str(_TG), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def _fresh_dirs():
    root = Path(tempfile.mkdtemp(prefix="evo-lab-bridge-"))
    state = root / "state"
    wt = root / "worktree"
    state.mkdir(parents=True, exist_ok=True)
    os.environ["OCTOPUS_STATE_DIR"] = str(state)
    os.environ["OCTOPUS_SUL_STATE_DIR"] = str(state / "sul")
    os.environ["OCTOPUS_SUL_WORKTREE"] = str(wt)
    os.environ["OCTOPUS_TG_DURABLE_OUTBOX"] = "1"
    os.environ.pop("OCTOPUS_TG_LOOP_KILL", None)
    import durable_loop
    dl = importlib.reload(durable_loop)
    return root, state, wt, dl


def _update(uid=91001, owner=777):
    return {
        "update_id": uid,
        "message": {
            "message_id": 3,
            "date": 1787366000,
            "from": {"id": owner},
            "chat": {"id": owner, "type": "private"},
            "text": "evolution propose fixture",
        },
    }


def _rfc():
    return {
        "rfc_id": "RFC-evobridge",
        "bottleneck": "lab and doctor were disconnected",
        "fix": "run one isolated lab cycle then queue a merge card",
        "organ": "doctor",
        "expected_lift": "automatic coding in a worktree",
    }


def t_a_rfc_invokes_lab_writes_artifact_and_outbox():
    root, state, wt, dl = _fresh_dirs()
    import lab_bridge
    lab_bridge = importlib.reload(lab_bridge)

    ctx = dl.begin_update(_update(), authorized=True)
    dl.bind_context(ctx)
    seen = []

    def fake_send():
        rows = list((state / "telegram" / "loop" / "outbox").glob("*.json"))
        assert rows, "outbox must exist before transport"
        seen.append(1)
        return {"ok": True, "result": {"message_id": 77001}}

    out = lab_bridge.run_rfc_through_lab(
        _rfc(), worktree=wt, state_dir=state / "sul",
        send_fn=fake_send, chat_id=777)
    assert out.get("experiment_id"), out
    assert out.get("worktree"), out
    assert Path(out["worktree"]).is_dir()
    arts = list(Path(out["worktree"]).rglob("rfc_artifacts/*.py"))
    assert arts, "expected RFC artifact in worktree: " + str(list(Path(out["worktree"]).rglob("*.py")))
    src = arts[0].read_text(encoding="utf-8")
    assert "RFC-evobridge" in src
    assert "disconnected" in src
    exp = state / "sul" / "experiments.jsonl"
    assert exp.is_file() and "RFC-evobridge" in exp.read_text(encoding="utf-8")
    assert out.get("test_outcome") in ("pass", "fail")
    assert isinstance(out.get("proposed_promote"), bool)
    assert out.get("live_promote") is False
    card = out.get("telegram_card") or {}
    assert card.get("rfc_id") == "RFC-evobridge"
    assert "[merge]" in (out.get("outbox") or {}).get("card_text", "")
    assert "[reject]" in (out.get("outbox") or {}).get("card_text", "")
    assert out.get("outbox_path")
    assert Path(out["outbox_path"]).is_file()
    queued = json.loads(Path(out["outbox_path"]).read_text(encoding="utf-8"))
    assert queued.get("state") in ("QUEUED", "CONFIRMED")
    assert queued.get("live_send") is False
    assert "RFC-evobridge" in queued.get("payload_text", "")
    deliver = (out.get("outbox") or {}).get("deliver") or {}
    assert deliver.get("deliver", {}).get("ok") is True
    assert seen == [1]
    # Isolated worktree is not the live vault.
    live = _OPS.parent.resolve()
    assert Path(out["worktree"]).resolve() != live
    dl.clear_context()


def t_b_evolution_propose_is_the_same_path():
    root, state, wt, dl = _fresh_dirs()
    import lab_bridge
    lab_bridge = importlib.reload(lab_bridge)
    ctx = dl.begin_update(_update(uid=91002), authorized=True)
    dl.bind_context(ctx)

    def fake_send():
        return {"ok": True, "result": {"message_id": 77002}}

    a = lab_bridge.evolution_propose(
        _rfc(), worktree=wt, state_dir=state / "sul",
        send_fn=fake_send, chat_id=777)
    b = lab_bridge.propose(
        _rfc(), worktree=wt, state_dir=state / "sul",
        send_fn=fake_send, chat_id=777)
    assert a.get("experiment_id")
    assert b.get("cached") or b.get("experiment_id") == a.get("experiment_id")
    dl.clear_context()


def t_c_doctor_hooks_call_bridge():
    src = (_DOC / "doctor.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    submit = next(n for n in ast.walk(tree)
                  if isinstance(n, ast.FunctionDef) and n.name == "submit_for_approval")
    propose = next(n for n in ast.walk(tree)
                   if isinstance(n, ast.FunctionDef) and n.name == "propose_rfc")
    blob_s = ast.dump(submit)
    blob_p = ast.dump(propose)
    assert "lab_bridge" in blob_s or "on_rfc_ready" in blob_s or "_bridge_to_lab" in blob_s
    assert "lab_bridge" in blob_p or "on_rfc_ready" in blob_p or "_bridge_to_lab" in blob_p


def t_d_controller_exposes_run_rfc_cycle():
    from self_upgrade_lab.controller import run_rfc_cycle
    from self_upgrade_lab.rfc_cycle import run_rfc_cycle as impl
    assert callable(run_rfc_cycle) and callable(impl)


def t_e_no_live_send_and_no_promote():
    src_b = (_DOC / "lab_bridge.py").read_text(encoding="utf-8")
    src_c = (_OPS / "self_upgrade_lab" / "rfc_cycle.py").read_text(encoding="utf-8")
    banned = ("sendMessage", "editMessageText", "getUpdates", "api.telegram.org")
    for blob in (src_b, src_c):
        for word in banned:
            assert word not in blob
    assert "from .promoter import" not in src_c
    assert "from self_upgrade_lab.promoter" not in src_c
    assert "promote(experiment" not in src_c


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_") and callable(v)]
    failed = []
    for fn in tests:
        try:
            fn()
            print("  OK  " + fn.__name__)
        except Exception as exc:
            failed.append(fn.__name__)
            print("  FAIL " + fn.__name__ + ": " + type(exc).__name__ + ": " + str(exc))
    print("\ntest_evo_lab_bridge: %d/%d" % (len(tests) - len(failed), len(tests)))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
