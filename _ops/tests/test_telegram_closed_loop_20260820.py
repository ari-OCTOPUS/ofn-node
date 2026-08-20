#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_telegram_closed_loop_20260820.py — A10 typed contract + A14/A16/A17.

Zero paid calls. Unique name. Registered in run_all.py (OWNER #16 A9).
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))
if str(_OPS / "owner_console") not in sys.path:
    sys.path.insert(0, str(_OPS / "owner_console"))
if str(_OPS / "tests") not in sys.path:
    sys.path.insert(0, str(_OPS / "tests"))

# Unit 4 (2026-08-21): پیش‌شرط محیطیِ قطعی — ایزولاسیون از طریق harness تا
# تست هم زیر اجرای مستقیم و هم زیر run_all (با live-state guard) یکسان و
# قطعی بماند؛ «سبز با rerun» دیگر معنا ندارد چون مسیر هرگز state زنده را
# لمس نمی‌کند.
import harness  # noqa: E402
ENV = harness.setup("tg-closed-loop")  # noqa: E402
_TEST_STATE = Path(tempfile.mkdtemp(prefix="tg-closed-loop-"))
os.environ["OCTOPUS_STATE_DIR"] = str(_TEST_STATE / "_ops" / "state")
os.environ["ORG_ROOT"] = str(_TEST_STATE)

from owner_console import local_commands, telegram_adapter  # noqa: E402
from owner_console.local_commands import LocalCommandResult  # noqa: E402
from cognition_quota import (  # noqa: E402
    classify_receipt, forensic_scan_since, gate_paid_intent, stamp_new_receipt,
)


def _boom(*_a, **_k):
    raise AssertionError("model must not be called")


def _auth(**extra) -> dict:
    d = {"allow": True, "mode": "core_conversation", "reason": "outer-dm-owner",
         "update_id": 42, "message_date": 1787210000, "chat_id": 1}
    d.update(extra)
    return d


def test_status_reply_is_dict_not_string():
    os.environ["OCTOPUS_PAID_COGNITION"] = "0"
    r = telegram_adapter.handle_message("/status", surface_decision=_auth(),
                                        model_fn=_boom)
    assert r["handled"] is True
    assert r["reason"] == "local-command"
    assert isinstance(r["reply"], dict)
    assert r["reply"].get("kind") != "clarify"
    assert "beat=" in (r["reply"].get("text") or "")
    assert r["reply"].get("handler_schema_version") == "typed-v1"
    r["reply"].get("kind")


def test_typed_command_result():
    res = local_commands.handle_local("/help", model_fn=_boom)
    assert isinstance(res, LocalCommandResult)
    assert res.handled is True
    assert res.model_allowed is False
    assert isinstance(res.kind, str) and isinstance(res.text, str)
    d = res.as_dict()
    assert d.get("kind") == "local-command" or d.get("kind") == "local-help"


def test_string_coerce_once():
    before = telegram_adapter.LEGACY_COERCE_COUNT
    d = telegram_adapter._as_reply_dict("hello")
    assert d["kind"] == "local-command" and d["text"] == "hello"
    assert d.get("legacy_coerced") is True
    assert telegram_adapter.LEGACY_COERCE_COUNT == before + 1
    typed = LocalCommandResult(handled=True, kind="local-command", text="x")
    d2 = telegram_adapter._as_reply_dict(typed)
    assert d2.get("legacy_coerced") is None
    assert telegram_adapter.LEGACY_COERCE_COUNT == before + 1


def test_handler_exception_zero_model():
    old = local_commands.status_text
    local_commands.status_text = lambda: (_ for _ in ()).throw(RuntimeError("x"))
    try:
        r = telegram_adapter.handle_message("/status", surface_decision=_auth(),
                                            model_fn=_boom)
        assert r["reply"]["kind"] == "LOCAL_COMMAND_ERROR"
        assert r["reply"].get("model_allowed") is False
    finally:
        local_commands.status_text = old


def test_all_firewall_commands_zero_model():
    os.environ["OCTOPUS_PAID_COGNITION"] = "0"
    cmds = [
        "/status", "  /STATUS  ", "/status@intergrade2725_Bot",
        "/health", "/memory", "/help", "/capabilities",
        "/why", "/وضعیت",
        "/nosuch",
    ]
    for c in cmds:
        r = telegram_adapter.handle_message(c, surface_decision=_auth(),
                                            model_fn=_boom)
        assert r["handled"] is True, c
        assert isinstance(r["reply"], dict), c
        assert r["reply"].get("model_allowed") is False, c


def test_unknown_slash_is_local_help_not_model():
    r = telegram_adapter.handle_message("/xyzabc", surface_decision=_auth(),
                                        model_fn=_boom)
    assert r["reason"] == "local-command"
    assert "ناشناخته" in (r["reply"]["text"] or "")


def test_remember_then_recall_zero_model():
    store = Path(tempfile.mkdtemp()) / "memory.jsonl"
    res = local_commands.handle_local("/remember کلمه رمز: مرجان",
                                      model_fn=_boom, memory_store=store)
    assert isinstance(res, LocalCommandResult)
    assert res.handled and res.memory_id and res.memory_id.startswith("mem-")
    rec = local_commands.try_recall("کلمه رمز چه بود؟", store=store)
    assert rec is not None
    assert rec.text == "مرجان"
    assert rec.retrieved_id == rec.memory_id
    assert rec.used_in_context is True
    assert rec.future_filtered == 0


def test_correct_keeps_historical():
    store = Path(tempfile.mkdtemp()) / "memory.jsonl"
    a = local_commands.handle_local("/remember کلمه رمز: مرجان",
                                    model_fn=_boom, memory_store=store)
    t1 = local_commands.last_remember(store=store)["occurred_at"]
    b = local_commands.handle_local("/correct t-1 کلمه درست: صدف",
                                    model_fn=_boom, memory_store=store)
    assert b.memory_id and b.memory_id != a.memory_id
    cur = local_commands.try_recall("کلمه رمز چه بود؟", store=store)
    assert cur.text == "صدف"
    hist = local_commands.try_recall("کلمه رمز چه بود؟", store=store, as_of=t1)
    assert hist.text == "مرجان"
    rows = local_commands._iter_memory(store)
    assert len(rows) == 2


def test_quota_unattributed_not_eligible():
    c = classify_receipt({"task_id": "", "run_id": ""})
    assert c["attribution"] == "UNATTRIBUTED"
    assert c["cognitive_quota_eligible"] is False


def test_quota_overshoot_blocks_before_network():
    p = Path(tempfile.mkdtemp()) / "r.jsonl"
    row = stamp_new_receipt({"provider": "deepseek", "tokens": 1, "cost_aud": 0.0},
                            task_id="t1", run_id="r1", turn_id="u1",
                            bucket="telegram_normal")
    p.write_text(json.dumps(row) + "\n", encoding="utf-8")
    os.environ["OCTOPUS_PAID_COGNITION"] = "1"
    os.environ["OCTOPUS_COGNITION_CAP_TELEGRAM_NORMAL"] = "1"
    os.environ["OCTOPUS_RUN_ID"] = "r1"
    g = gate_paid_intent(task="t2", run_id="r1", bucket="telegram_normal",
                         receipts_path=p, paid_paused=False)
    assert g["allow"] is False and g["reason"] == "QUOTA_EXHAUSTED"
    os.environ["OCTOPUS_PAID_COGNITION"] = "0"
    g2 = gate_paid_intent(task="t2", run_id="r1", bucket="telegram_normal",
                          receipts_path=p)
    assert g2["allow"] is False and g2["mode"] == "LOCAL_DEGRADED_MODE"


def test_post_migration_coverage_ignores_historic():
    p = Path(tempfile.mkdtemp()) / "r.jsonl"
    old = {"task_id": "", "run_id": "", "created_at": "2026-08-01T00:00:00Z"}
    new = stamp_new_receipt({"provider": "deepseek", "tokens": 0, "cost_aud": 0.0,
                             "created_at": "2026-08-20T12:00:00Z"},
                            task_id="t9", run_id="r9", turn_id="u9",
                            bucket="telegram_normal")
    p.write_text(json.dumps(old) + "\n" + json.dumps(new) + "\n", encoding="utf-8")
    cov = forensic_scan_since(p, since_iso="2026-08-20T11:00:00Z")
    assert cov["n"] == 1 and cov["attributed"] == 1
    assert cov["attribution_ratio"] == 1.0


def test_local_commands_when_quota_exhausted():
    os.environ["OCTOPUS_PAID_COGNITION"] = "0"
    r = telegram_adapter.handle_message("/status", surface_decision=_auth(),
                                        model_fn=_boom)
    assert r["handled"] is True and "beat=" in r["reply"]["text"]


def test_free_text_hears_brains_without_model():
    os.environ["OCTOPUS_PAID_COGNITION"] = "0"
    r = telegram_adapter.handle_message("سلام این یک پیام آزاد است",
                                        surface_decision=_auth(), model_fn=_boom)
    assert r["reason"] == "local-degraded-paid-paused"
    assert r["reply"]["kind"] == "local-degraded"
    assert "hc_wm" in r
    assert r["hc_wm"]["executable"] is False
    assert "deltas" in r["hc_wm"]
    a5 = (r.get("brains") or {}).get("a5_receipts") or []
    assert a5, "A5 receipts must exist for free-text"
    assert any(x.get("heard") for x in a5)
    assert all(x.get("executable") is False for x in a5)


def test_unauthorized_silent():
    r = telegram_adapter.handle_message("/status",
                                        surface_decision={"allow": False, "mode": "deny"},
                                        model_fn=_boom)
    assert r["handled"] is False and r["reply"] is None


def test_process_identity_fields():
    sys.path.insert(0, str(_OPS / "telegram_center"))
    import process_identity as pi  # noqa: WPS433
    ident = pi.build(poller_lease_id="test")
    for k in ("process_id", "started_at", "git_commit", "center_py_sha256",
              "handler_schema_version", "bot_id", "poller_lease_id"):
        assert k in ident
    assert ident["bot_id"] == 7992324219
    assert ident["handler_schema_version"] == "typed-v1"


def main() -> int:
    failed = []
    tests = [
        test_status_reply_is_dict_not_string,
        test_typed_command_result,
        test_string_coerce_once,
        test_handler_exception_zero_model,
        test_all_firewall_commands_zero_model,
        test_unknown_slash_is_local_help_not_model,
        test_remember_then_recall_zero_model,
        test_correct_keeps_historical,
        test_quota_unattributed_not_eligible,
        test_quota_overshoot_blocks_before_network,
        test_post_migration_coverage_ignores_historic,
        test_local_commands_when_quota_exhausted,
        test_free_text_hears_brains_without_model,
        test_unauthorized_silent,
        test_process_identity_fields,
    ]
    for fn in tests:
        try:
            fn()
            print(f"  ok  {fn.__name__}")
        except Exception as e:  # noqa: BLE001
            failed.append(fn.__name__)
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(tests) - len(failed)}/{len(tests)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
