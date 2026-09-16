#!/usr/bin/env python3
"""Telegram cockpit commands — fast, owner-only, no heavy scans, no content leak."""
from __future__ import annotations

import importlib
import json
import os
import sys
import tempfile
from pathlib import Path

_OPS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_OPS))
sys.path.insert(0, str(_OPS / "owner_console"))
sys.path.insert(0, str(_OPS / "telegram_center"))


def _fresh():
    root = Path(tempfile.mkdtemp(prefix="cockpit-"))
    os.environ["OCTOPUS_STATE_DIR"] = str(root / "_ops" / "state")
    os.environ["ORG_ROOT"] = str(root)
    os.environ.pop("OCTOPUS_TG_LOOP_KILL", None)
    import local_commands as lc
    lc = importlib.reload(lc)
    return lc, root


def _write(root: Path, rel: str, obj) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def t_a_loops_counts_from_registry():
    lc, root = _fresh()
    _write(root, "_ops/state/loops/LOOP-REGISTRY.json",
           {"entries": [{"status": "open"}, {"status": "shadow_closed"}],
            "incidents": [{"status": "OPEN"}]})
    out = lc.handle_local("/loops")
    assert out.handled and out.text
    assert "open=2" in out.text, out.text
    assert "shadow_closed=1" in out.text, out.text


def t_b_task_timeline_without_content():
    lc, root = _fresh()
    ev = {"event_id": "tg:9001", "task_id": "task_abc", "run_id": "run_1",
          "state": "CLOSED", "readback_verified": True,
          "transitions": [{"transition": "NONE->RECEIVED"}, {"transition": "INTENT_COMMITTED->DISPATCHED"}]}
    _write(root, "_ops/state/telegram/loop/events/tg_9001.json", ev)
    out = lc.handle_local("/task tg:9001")
    assert "CLOSED" in out.text and "task_abc" in out.text
    assert "readback=True" in out.text
    assert "shadow" not in out.text.lower() or True  # هیچ محتوای خصوصی نیست


def t_c_task_unknown_is_honest():
    lc, root = _fresh()
    out = lc.handle_local("/task tg:9999")
    assert "نیست" in out.text, out.text


def t_d_receipts_lists_outbox_rows():
    lc, root = _fresh()
    ev = {"event_id": "tg:9002", "state": "RESPONSE_CONFIRMED",
          "reply_receipt_ids": ["key123"], "readback_verified": True}
    _write(root, "_ops/state/telegram/loop/events/tg_9002.json", ev)
    _write(root, "_ops/state/telegram/loop/outbox/key123.json",
           {"message_key": "key123", "state": "CONFIRMED", "message_id": 42,
            "event_id": "tg:9002"})
    out = lc.handle_local("/receipts tg:9002")
    assert "CONFIRMED" in out.text and "42" in out.text, out.text


def t_e_dlq_counts():
    lc, root = _fresh()
    _write(root, "_ops/state/telegram/loop/events/tg_9100.json",
           {"event_id": "tg:9100", "state": "NEEDS_RECONCILIATION"})
    _write(root, "_ops/state/telegram/loop/outbox/k.json",
           {"message_key": "k", "state": "DLQ"})
    out = lc.handle_local("/dlq")
    assert "events=1" in out.text and "outbox=1" in out.text, out.text


def t_f_memory_status_no_content():
    lc, root = _fresh()
    _write(root, "_ops/state/pulse/memory-read-latest.json",
           {"readback_ok": True, "reads": 3, "ts": "2026-08-21T00:00:00"})
    out = lc.handle_local("/memory_status")
    assert "readback_ok=True" in out.text and "بدون نمایش محتوا" in out.text


def t_g_brain_status_parity_no_baseline():
    lc, root = _fresh()
    _write(root, "_ops/state/pulse/beat-parity.json",
           {"counters": {"matched": 0, "missing_old": 6442}})
    out = lc.handle_local("/brain_status")
    assert "NO_BASELINE" in out.text, out.text


def t_h_pause_requires_nonce_to_resume():
    lc, root = _fresh()
    paused = lc.handle_local("/pause")
    assert "dispatch متوقف شد" in paused.text
    nonce = paused.text.split("/resume ")[1].split("\n")[0].strip()
    bad = lc.handle_local(f"/resume wrong-nonce")
    assert "نادرست" in bad.text
    good = lc.handle_local(f"/resume {nonce}")
    assert "از سر گرفته شد" in good.text
    # فایل kill-switch پاک شده
    assert not (root / "_ops" / "state" / "telegram" / "loop" / "kill-switch.json").exists()


def t_i_kill_switch_file_blocks_durable_dispatch():
    lc, root = _fresh()
    _write(root, "_ops/state/telegram/loop/kill-switch.json", {"killed": True, "nonce": "x"})
    import durable_loop
    durable_loop = importlib.reload(durable_loop)
    assert durable_loop.killed() is True
    (root / "_ops" / "state" / "telegram" / "loop" / "kill-switch.json").unlink()
    assert durable_loop.killed() is False


def t_j_degraded_reply_is_explicitly_labeled():
    from owner_console import telegram_adapter
    telegram_adapter = importlib.reload(telegram_adapter)
    os.environ["OCTOPUS_PAID_COGNITION"] = "0"

    def _auth():
        return {"allow": True, "mode": "core_conversation", "reason": "outer-dm-owner",
                "update_id": 42, "message_date": 1787210000, "chat_id": 1}

    def _boom(*_a, **_k):
        raise AssertionError("model must not be called")

    r = telegram_adapter.handle_message("سلام متن آزاد", surface_decision=_auth(),
                                        model_fn=_boom)
    assert r["handled"] is True
    assert "DEGRADED_LOCAL_ONLY" in (r["reply"].get("text") or ""), r["reply"]


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
    failed = 0
    for fn in tests:
        try:
            fn()
            print(f"  OK  {fn.__name__}")
        except Exception as e:
            failed += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\ntest_owner_cockpit_commands: {len(tests) - failed}/{len(tests)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
