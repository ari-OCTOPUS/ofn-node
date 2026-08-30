"""test_interview_unwired_4d_20260816 — UNWIRED cards 4/5 honesty (notify + git_watcher).

daemon.py / self_code.py لمس نشدند (TCB). ثبت در run_all نشده.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "4d_system"))

import config.settings as settings  # noqa: E402
from brain import git_watcher, notify  # noqa: E402


def t_flush_not_configured_reached_owner_false():
    orig = settings.OUTPUT_DIR
    td = tempfile.TemporaryDirectory()
    settings.OUTPUT_DIR = Path(td.name)
    had_tok = os.environ.pop("TELEGRAM_BOT_TOKEN", None)
    had_chat = os.environ.pop("TELEGRAM_CHAT_ID", None)
    try:
        notify.queue_for_digest("notify", "c1", "w", "r", "cons")
        res = notify.flush_digest(force=True)
        assert res["sent"] is False
        assert res.get("reached_owner") is False
        pkt = notify.send_packet("notify", "ctx", "why", "rec", "cons")
        assert pkt.get("reached_owner") is False
        assert "queued" in str(pkt.get("delivered"))
    finally:
        settings.OUTPUT_DIR = orig
        td.cleanup()
        if had_tok is not None:
            os.environ["TELEGRAM_BOT_TOKEN"] = had_tok
        if had_chat is not None:
            os.environ["TELEGRAM_CHAT_ID"] = had_chat


def t_git_watcher_armed_false_when_self_code_off():
    os.environ["GIT_WATCHER_ENABLED"] = "1"
    os.environ["SELF_CODE_ENABLED"] = "0"
    # module-level _GW_ENABLED captured at import — armed() still reads self_code.enabled()
    from brain import self_code
    assert self_code.enabled() is False
    # If GIT flag was captured True at import, armed must still be False
    assert git_watcher.armed() is False


if __name__ == "__main__":
    failed = 0
    for fn in (t_flush_not_configured_reached_owner_false,
               t_git_watcher_armed_false_when_self_code_off):
        try:
            fn()
            print("PASS", fn.__name__)
        except Exception as e:  # noqa: BLE001
            failed += 1
            print("FAIL", fn.__name__, type(e).__name__, e)
    raise SystemExit(1 if failed else 0)
