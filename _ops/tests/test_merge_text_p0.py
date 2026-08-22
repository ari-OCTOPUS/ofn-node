#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P0 MERGE-TEXT: free-text [merge]/[reject] -> apply_owner_verdict human-append path.

Fixture-only. Fake HTTP transport. No live Telegram send.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_OPS), str(_OPS / "doctor"), str(_OPS / "budget"), str(_OPS / "cortex")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import harness  # noqa: E402
ENV = harness.setup("merge-text-p0")

import approval_channel as ac  # noqa: E402
import doctor as _docmod  # noqa: E402
import lab_bridge as _lb  # noqa: E402


def _fake_http(*_a, **_k):
    return {"ok": True, "result": {}}


def _mk_evidence(root: Path, name: str = "proof.json") -> Path:
    p = root / name
    p.write_text(json.dumps({"schema": "merge-text-proof/1", "ok": True}),
                 encoding="utf-8")
    return p


def t_parser_extracts_rfc_and_verbs_including_fa():
    m = _lb.parse_owner_verdict_text("please RFC-MT-1 [merge] now")
    assert m and m["verb"] == "merge" and m["rfc_id"] == "RFC-MT-1", m
    r = _lb.parse_owner_verdict_text("[reject] RFC-MT-2")
    assert r and r["verb"] == "reject" and r["rfc_id"] == "RFC-MT-2", r
    fa_m = _lb.parse_owner_verdict_text("RFC-MT-3 [ادغام]")
    assert fa_m and fa_m["verb"] == "merge", fa_m
    fa_r = _lb.parse_owner_verdict_text("RFC-MT-4 [رد]")
    assert fa_r and fa_r["verb"] == "reject", fa_r
    assert _lb.parse_owner_verdict_text("no tags here") is None


def t_handle_command_freetext_persists_and_doctor_applies_merge():
    """Fake transport: free-text [merge] -> persist -> doctor apply_owner_verdict."""
    root = Path(tempfile.mkdtemp(prefix="merge-text-ok-"))
    evidence = _mk_evidence(root)
    state = root / "state"
    state.mkdir(parents=True, exist_ok=True)
    chan = ac.TelegramApprovalChannel(
        token="fake-token", owner_chat_id=42,
        http_get=_fake_http, http_post=_fake_http, state_dir=str(state))
    reply = chan.handle_command("RFC-MT-OK [merge]", from_id=42)
    assert reply and "ثبت" in str(reply), reply

    d = _docmod.Doctor(state_dir=str(state), approval_channel=chan)
    rfc = _docmod.RFC(
        rfc_id="RFC-MT-OK", bottleneck="b", fix="f", expected_lift="x",
        status="submitted", rollback="revert mt",
        sandbox_result={
            "test_ok": True,
            "test_outcome": "pass",
            "evidence_path": str(evidence),
            "rollback_plan": "revert mt",
            "experiment_id": "exp-mt-ok",
        },
    )
    d._rfcs["RFC-MT-OK"] = rfc
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
    assert d._rfcs["RFC-MT-OK"].status == "merged"


def t_freetext_merge_lab_without_proofs_refuses():
    """Reject-without-proofs: lab RFC free-text [merge] still refuses promote."""
    root = Path(tempfile.mkdtemp(prefix="merge-text-refuse-"))
    state = root / "state"
    state.mkdir(parents=True, exist_ok=True)
    chan = ac.TelegramApprovalChannel(
        token="fake-token", owner_chat_id=7,
        http_get=_fake_http, http_post=_fake_http, state_dir=str(state))
    reply = chan.handle_command("[merge] RFC-MT-BAD", from_id=7)
    assert reply and "ثبت" in str(reply), reply

    d = _docmod.Doctor(state_dir=str(state), approval_channel=chan)
    d._rfcs["RFC-MT-BAD"] = _docmod.RFC(
        rfc_id="RFC-MT-BAD", bottleneck="b", fix="f", expected_lift="x",
        status="submitted",
        sandbox_result={
            "test_ok": False,
            "evidence_path": "",
            "rollback_plan": "",
            "experiment_id": "exp-mt-bad",
        },
    )
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
    assert calls["n"] == 0, "lab merge without proofs must refuse apply_merge"
    assert d._rfcs["RFC-MT-BAD"].status != "merged", d._rfcs["RFC-MT-BAD"].status


def t_freetext_reject_never_calls_apply_merge():
    root = Path(tempfile.mkdtemp(prefix="merge-text-rej-"))
    state = root / "state"
    state.mkdir(parents=True, exist_ok=True)
    chan = ac.TelegramApprovalChannel(
        token="fake-token", owner_chat_id=9,
        http_get=_fake_http, http_post=_fake_http, state_dir=str(state))
    reply = chan.handle_command("RFC-MT-REJ [reject]", from_id=9)
    assert reply and "رد" in str(reply), reply

    d = _docmod.Doctor(state_dir=str(state), approval_channel=chan)
    d._rfcs["RFC-MT-REJ"] = _docmod.RFC(
        rfc_id="RFC-MT-REJ", bottleneck="b", fix="f", expected_lift="x",
        status="submitted",
        sandbox_result={
            "test_ok": True,
            "evidence_path": str(_mk_evidence(root)),
            "rollback_plan": "n/a",
            "experiment_id": "exp-mt-rej",
        },
    )
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
    assert d._rfcs["RFC-MT-REJ"].status == "human-rejected"


def t_parser_feeds_apply_owner_verdict_directly():
    """Parsed free-text verb must be accepted by apply_owner_verdict."""
    root = Path(tempfile.mkdtemp(prefix="merge-text-unit-"))
    evidence = _mk_evidence(root)
    parsed = _lb.parse_owner_verdict_text("RFC-U1 [merge]")
    assert parsed and parsed["verb"] == "merge"
    seen = []

    def _fake_apply(rfc):
        seen.append(getattr(rfc, "rfc_id", rfc))
        if hasattr(rfc, "status"):
            rfc.status = "merged"
        return True

    rfc = _docmod.RFC(rfc_id="RFC-U1", bottleneck="b", fix="f", expected_lift="x",
                      status="submitted")
    out = _lb.apply_owner_verdict(
        verb="[" + parsed["verb"] + "]" if False else parsed["verb"],
        apply_merge_fn=_fake_apply, rfc=rfc,
        test_ok=True, evidence_path=str(evidence),
        rollback_plan="roll", require_gate=True)
    assert out.get("applied") and out.get("promoted"), out
    assert seen == ["RFC-U1"]

    parsed_r = _lb.parse_owner_verdict_text("[reject] RFC-U2")
    rfc2 = _docmod.RFC(rfc_id="RFC-U2", bottleneck="b", fix="f", expected_lift="x",
                       status="submitted")
    seen.clear()
    rej = _lb.apply_owner_verdict(
        verb=parsed_r["verb"], apply_merge_fn=_fake_apply, rfc=rfc2,
        test_ok=True, evidence_path=str(evidence), rollback_plan="roll",
        require_gate=True)
    assert rej.get("applied") is False and seen == []
    assert rfc2.status == "human-rejected"


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
    print("RESULT", "failed=" + str(failed), "passed=" + str(len(tests) - failed))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())