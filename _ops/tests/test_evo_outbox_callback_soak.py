#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""EVO-OUTBOX-CALLBACK-SOAK: outbox card -> callback token -> owner merge/reject.

End-to-end fixture soak (NO live Telegram send):
  1. synthetic RFC through lab_bridge / rfc_cycle -> QUEUED outbox with [merge]/[reject]
  2. callback token on outbox payload (or free-text [merge] RFC-id path)
  3. approval_channel dispatch / apply_owner_verdict
  4. with proofs -> apply_merge; without -> refuse; [reject] -> no promote

Fake HTTP transport only. Center PID untouched.
"""
from __future__ import annotations

import importlib
import json
import os
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_OPS), str(_OPS / "doctor"), str(_OPS / "budget"),
           str(_OPS / "cortex"), str(_OPS / "telegram_center")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import harness  # noqa: E402
ENV = harness.setup("evo-outbox-cb-soak")

_OWNER = 4242
_SECRET = "fixture-evo-outbox-cb-secret-not-real"
os.environ["OCTOPUS_CB_SECRET"] = _SECRET
os.environ["TELEGRAM_OWNER_CHAT_ID"] = str(_OWNER)
os.environ["OCTOPUS_TG_DURABLE_OUTBOX"] = "1"
os.environ.pop("OCTOPUS_TG_LOOP_KILL", None)

import approval_channel as ac  # noqa: E402
import doctor as _docmod  # noqa: E402
import lab_bridge as _lb  # noqa: E402


def _fake_http(*_a, **_k):
    return {"ok": True, "result": {}}


def _fresh_dirs(prefix="evo-ob-cb-"):
    root = Path(tempfile.mkdtemp(prefix=prefix))
    state = root / "state"
    wt = root / "worktree"
    state.mkdir(parents=True, exist_ok=True)
    os.environ["OCTOPUS_STATE_DIR"] = str(state)
    os.environ["OCTOPUS_SUL_STATE_DIR"] = str(state / "sul")
    os.environ["OCTOPUS_SUL_WORKTREE"] = str(wt)
    os.environ["OCTOPUS_CB_SECRET"] = _SECRET
    os.environ["TELEGRAM_OWNER_CHAT_ID"] = str(_OWNER)
    import durable_loop
    dl = importlib.reload(durable_loop)
    importlib.reload(_lb)
    return root, state, wt, dl


def _mk_evidence(root: Path, name: str = "proof.json") -> Path:
    p = root / name
    p.write_text(json.dumps({"schema": "evo-outbox-cb-proof/1", "ok": True}),
                 encoding="utf-8")
    return p


def _rfc(rid="RFC-obcb1"):
    return {
        "rfc_id": rid,
        "bottleneck": "outbox card lacked callback token roundtrip",
        "fix": "mint rfc:merge|deny token onto QUEUED evo outbox payload",
        "organ": "doctor",
        "expected_lift": "owner callback or free-text merge reaches apply_owner_verdict",
        "callback_owner": _OWNER,
        "owner": _OWNER,
    }


def t_a_outbox_card_carries_callback_token():
    """Synthetic RFC -> lab bridge -> outbox has [merge]/[reject] + token."""
    root, state, wt, dl = _fresh_dirs("evo-ob-token-")
    ctx = dl.begin_update({
        "update_id": 92001,
        "message": {"message_id": 1, "date": 1787367000,
                    "from": {"id": _OWNER},
                    "chat": {"id": _OWNER, "type": "private"},
                    "text": "evo soak"},
    }, authorized=True)
    dl.bind_context(ctx)

    def fake_send():
        return {"ok": True, "result": {"message_id": 88001}}

    out = _lb.run_rfc_through_lab(
        _rfc("RFC-obcb-tok"), worktree=wt, state_dir=state / "sul",
        send_fn=fake_send, chat_id=_OWNER)
    assert out.get("outbox_path"), out
    path = Path(out["outbox_path"])
    assert path.is_file()
    rec = json.loads(path.read_text(encoding="utf-8"))
    assert rec.get("live_send") is False
    assert "[merge]" in rec.get("payload_text", "")
    assert "[reject]" in rec.get("payload_text", "")
    assert rec.get("callback_token_missing") is False, rec
    assert rec.get("callback_token"), rec
    assert rec.get("callback_merge", "").startswith("rfc:merge:RFC-obcb-tok:")
    assert rec.get("callback_deny", "").startswith("rfc:deny:RFC-obcb-tok:")
    parsed = _lb.parse_outbox_callback(path)
    assert parsed and parsed["token"] == rec["callback_token"]
    assert parsed["callback_token_missing"] is False
    assert parsed["live_send"] is False
    dl.clear_context()


def t_b_callback_with_proofs_applies_merge():
    """Owner callback token from outbox -> persist verdict -> apply_merge."""
    root, state, wt, dl = _fresh_dirs("evo-ob-merge-")
    evidence = _mk_evidence(root)
    out = _lb.run_rfc_through_lab(
        _rfc("RFC-obcb-ok"), worktree=wt, state_dir=state / "sul")
    parsed = _lb.parse_outbox_callback(out["outbox_path"])
    assert parsed and not parsed["callback_token_missing"], parsed

    chan = ac.TelegramApprovalChannel(
        token="fake-token", owner_chat_id=_OWNER,
        http_get=_fake_http, http_post=_fake_http, state_dir=str(state))
    reply = chan.dispatch_callback(parsed["callback_merge"])
    assert "ثبت" in str(reply) or "merge" in str(reply).lower() or "✅" in str(reply), reply

    d = _docmod.Doctor(state_dir=str(state), approval_channel=chan)
    rfc = _docmod.RFC(
        rfc_id="RFC-obcb-ok", bottleneck="b", fix="f", expected_lift="x",
        status="submitted", rollback="revert obcb",
        sandbox_result={
            "test_ok": True,
            "test_outcome": "pass",
            "evidence_path": str(evidence),
            "rollback_plan": "revert obcb",
            "experiment_id": out.get("experiment_id") or "exp-obcb-ok",
            "worktree": out.get("worktree"),
            "proposed_promote": True,
        },
    )
    d._rfcs["RFC-obcb-ok"] = rfc
    calls = {"n": 0}
    real_apply = d.apply_merge

    def _wrap(r):
        calls["n"] += 1
        return real_apply(r)

    d.apply_merge = _wrap  # type: ignore[method-assign]
    os.environ["OCTOPUS_WIRE_APPLY_MERGE"] = "1"
    try:
        d.run_cycle(beat=1)
    finally:
        os.environ.pop("OCTOPUS_WIRE_APPLY_MERGE", None)
    assert calls["n"] == 1, calls
    assert d._rfcs["RFC-obcb-ok"].status == "merged"


def t_c_callback_without_proofs_refuses():
    """Owner callback merge with incomplete lab proofs -> refuse, no promote."""
    root, state, wt, dl = _fresh_dirs("evo-ob-refuse-")
    out = _lb.run_rfc_through_lab(
        _rfc("RFC-obcb-bad"), worktree=wt, state_dir=state / "sul")
    parsed = _lb.parse_outbox_callback(out["outbox_path"])
    assert parsed and parsed["token"], parsed

    chan = ac.TelegramApprovalChannel(
        token="fake-token", owner_chat_id=_OWNER,
        http_get=_fake_http, http_post=_fake_http, state_dir=str(state))
    reply = chan.dispatch_callback(parsed["callback_merge"])
    assert reply, reply

    d = _docmod.Doctor(state_dir=str(state), approval_channel=chan)
    rfc = _docmod.RFC(
        rfc_id="RFC-obcb-bad", bottleneck="b", fix="f", expected_lift="x",
        status="submitted",
        sandbox_result={
            "test_ok": False,
            "evidence_path": "",
            "rollback_plan": "",
            "experiment_id": "exp-obcb-bad",
            "worktree": out.get("worktree"),
        },
    )
    d._rfcs["RFC-obcb-bad"] = rfc
    calls = {"n": 0}
    real_apply = d.apply_merge

    def _wrap(r):
        calls["n"] += 1
        return real_apply(r)

    d.apply_merge = _wrap  # type: ignore[method-assign]
    os.environ["OCTOPUS_WIRE_APPLY_MERGE"] = "1"
    try:
        d.run_cycle(beat=1)
    finally:
        os.environ.pop("OCTOPUS_WIRE_APPLY_MERGE", None)
    assert calls["n"] == 0, "must refuse apply_merge without proofs"
    # Real durable ack with applied=False may park reconcile-required; never merged.
    assert d._rfcs["RFC-obcb-bad"].status != "merged"
    assert d._rfcs["RFC-obcb-bad"].status in ("submitted", "reconcile-required")


def t_d_reject_callback_never_promotes():
    """Owner [reject]/deny callback -> human-rejected, never apply_merge."""
    root, state, wt, dl = _fresh_dirs("evo-ob-rej-")
    evidence = _mk_evidence(root, "rej.json")
    out = _lb.run_rfc_through_lab(
        _rfc("RFC-obcb-rej"), worktree=wt, state_dir=state / "sul")
    parsed = _lb.parse_outbox_callback(out["outbox_path"])
    assert parsed and parsed["callback_deny"], parsed

    chan = ac.TelegramApprovalChannel(
        token="fake-token", owner_chat_id=_OWNER,
        http_get=_fake_http, http_post=_fake_http, state_dir=str(state))
    reply = chan.dispatch_callback(parsed["callback_deny"])
    assert "رد" in str(reply) or "deny" in str(reply).lower() or "❌" in str(reply), reply

    d = _docmod.Doctor(state_dir=str(state), approval_channel=chan)
    rfc = _docmod.RFC(
        rfc_id="RFC-obcb-rej", bottleneck="b", fix="f", expected_lift="x",
        status="submitted",
        sandbox_result={
            "test_ok": True,
            "evidence_path": str(evidence),
            "rollback_plan": "n/a",
            "experiment_id": "exp-obcb-rej",
        },
    )
    d._rfcs["RFC-obcb-rej"] = rfc
    calls = {"n": 0}
    real_apply = d.apply_merge

    def _wrap(r):
        calls["n"] += 1
        return real_apply(r)

    d.apply_merge = _wrap  # type: ignore[method-assign]
    os.environ["OCTOPUS_WIRE_APPLY_MERGE"] = "1"
    try:
        d.run_cycle(beat=1)
    finally:
        os.environ.pop("OCTOPUS_WIRE_APPLY_MERGE", None)
    assert calls["n"] == 0
    assert d._rfcs["RFC-obcb-rej"].status == "human-rejected"


def t_e_freetext_merge_roundtrip_also_works():
    """Free-text 'RFC-id [merge]' path still reaches apply_owner_verdict."""
    root, state, wt, dl = _fresh_dirs("evo-ob-ft-")
    evidence = _mk_evidence(root, "ft.json")
    # still produce outbox card (token present) but exercise free-text verb path
    out = _lb.run_rfc_through_lab(
        _rfc("RFC-obcb-ft"), worktree=wt, state_dir=state / "sul")
    assert Path(out["outbox_path"]).is_file()

    chan = ac.TelegramApprovalChannel(
        token="fake-token", owner_chat_id=_OWNER,
        http_get=_fake_http, http_post=_fake_http, state_dir=str(state))
    reply = chan.handle_command("RFC-obcb-ft [merge]", from_id=_OWNER)
    assert reply, reply

    d = _docmod.Doctor(state_dir=str(state), approval_channel=chan)
    rfc = _docmod.RFC(
        rfc_id="RFC-obcb-ft", bottleneck="b", fix="f", expected_lift="x",
        status="submitted", rollback="revert ft",
        sandbox_result={
            "test_ok": True,
            "test_outcome": "pass",
            "evidence_path": str(evidence),
            "rollback_plan": "revert ft",
            "experiment_id": "exp-obcb-ft",
        },
    )
    d._rfcs["RFC-obcb-ft"] = rfc
    calls = {"n": 0}
    real_apply = d.apply_merge

    def _wrap(r):
        calls["n"] += 1
        return real_apply(r)

    d.apply_merge = _wrap  # type: ignore[method-assign]
    os.environ["OCTOPUS_WIRE_APPLY_MERGE"] = "1"
    try:
        d.run_cycle(beat=1)
    finally:
        os.environ.pop("OCTOPUS_WIRE_APPLY_MERGE", None)
    assert calls["n"] == 1, calls
    assert d._rfcs["RFC-obcb-ft"].status == "merged"


def t_f_token_missing_when_no_secret_is_explicit():
    """Without OCTOPUS_CB_SECRET, outbox marks callback_token_missing (fail-soft)."""
    root, state, wt, dl = _fresh_dirs("evo-ob-nosec-")
    os.environ.pop("OCTOPUS_CB_SECRET", None)
    importlib.reload(_lb)
    out = _lb.run_rfc_through_lab(
        _rfc("RFC-obcb-nosec"), worktree=wt, state_dir=state / "sul")
    rec = json.loads(Path(out["outbox_path"]).read_text(encoding="utf-8"))
    assert rec.get("callback_token_missing") is True, rec
    assert not rec.get("callback_token")
    parsed = _lb.parse_outbox_callback(rec)
    assert parsed and parsed["callback_token_missing"] is True
    # restore for other tests if re-ordered
    os.environ["OCTOPUS_CB_SECRET"] = _SECRET
    importlib.reload(_lb)


def t_g_no_live_send_banned_apis():
    src = (_OPS / "doctor" / "lab_bridge.py").read_text(encoding="utf-8")
    for word in ("sendMessage", "editMessageText", "getUpdates", "api.telegram.org"):
        assert word not in src
    assert "attach_outbox_callback_token" in src
    assert "parse_outbox_callback" in src


def main() -> int:
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("t_") and callable(v)]
    failed = 0
    for fn in tests:
        try:
            fn()
            print("PASS", fn.__name__)
        except Exception as exc:
            failed += 1
            print("FAIL", fn.__name__, type(exc).__name__ + ":", exc)
    print("RESULT", "failed=" + str(failed),
          "passed=" + str(len(tests) - failed),
          "total=" + str(len(tests)))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
