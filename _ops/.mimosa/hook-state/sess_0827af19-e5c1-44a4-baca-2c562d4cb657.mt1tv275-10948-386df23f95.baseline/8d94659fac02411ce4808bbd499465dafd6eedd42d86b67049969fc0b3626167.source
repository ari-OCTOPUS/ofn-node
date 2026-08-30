#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_board_cp.py — Control Plane ویندوز (board-pull). ثبت در run_all.py نشود."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
for _p in (str(_OPS), str(_OPS / "owner_console"), str(_OPS / "telegram_center")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

_TMP = tempfile.mkdtemp(prefix="board-cp-")
os.environ["OCTOPUS_BOARD_CP_DB"] = str(Path(_TMP) / "commands.sqlite")
os.environ.pop("OCTOPUS_BOARD_CP", None)
os.environ.pop("OCTOPUS_BOARD_CONTROL_URL", None)
os.environ.pop("OCTOPUS_BOARD_CP_BEARER", None)

from board_cp import config, service  # noqa: E402
from board_cp import http as bhttp  # noqa: E402
from board_cp.schema import CommandState  # noqa: E402
from owner_console import conversation  # noqa: E402
import collaborator as col  # noqa: E402
from miniapp_gateway import _handle_core  # noqa: E402


def _arm(url="https://cp.example.com/api/board-cp/pull", bearer="test-bearer-token"):
    os.environ["OCTOPUS_BOARD_CP"] = "1"
    os.environ["OCTOPUS_BOARD_CONTROL_URL"] = url
    os.environ["OCTOPUS_BOARD_CP_BEARER"] = bearer


def _disarm():
    os.environ.pop("OCTOPUS_BOARD_CP", None)
    os.environ.pop("OCTOPUS_BOARD_CONTROL_URL", None)
    os.environ.pop("OCTOPUS_BOARD_CP_BEARER", None)


def t_gate0_rejects_board_hosts_and_8796():
    assert config.control_url_ok("") is False
    assert config.control_url_ok("http://cp.example.com/x") is False
    assert config.control_url_ok("https://ziman.master-painting.com/x") is False
    assert config.control_url_ok("https://panel.master-painting.com/x") is False
    assert config.control_url_ok("https://app.master-painting.com/x") is False
    assert config.control_url_ok("https://127.0.0.1:8796/x") is False
    assert config.control_url_ok("https://cp.example.com:8796/x") is False
    assert config.control_url_ok("https://cp.example.com/api/board-cp/pull") is True
    assert config.gate0_ready() is False


def t_default_flag_off_no_pull():
    _disarm()
    assert config.flag_on() is False
    assert config.is_armed() is False
    stored = service.enqueue(kind="ask", text="hi")
    assert stored["state"] == "received"
    assert stored["external_effect"] is False
    pulled = service.pull()
    assert pulled["ok"] is False and pulled["reason"] == "flag_off"
    assert pulled["commands"] == []


def t_task_always_owner_required():
    _arm()
    stored = service.enqueue(kind="task", text="do-it")
    assert stored["state"] == "received"
    assert stored["owner_required"] is True
    pulled = service.pull()
    assert pulled["ok"] is True and pulled["count"] == 0
    service.authorize(stored["message_id"])
    pulled2 = service.pull()
    assert pulled2["count"] == 1
    assert pulled2["commands"][0]["operation"] == "ofn.task.start"
    _disarm()


def t_ask_pull_ack_when_armed():
    _arm()
    stored = service.enqueue(kind="ask", text="what is ofn")
    assert stored["state"] == "authorized"
    pulled = service.pull()
    assert pulled["count"] == 1
    assert pulled["commands"][0]["operation"] == "ofn.ask"
    mid = pulled["commands"][0]["message_id"]
    ack = service.ack(mid, outcome="succeeded")
    assert ack["ok"] is True and ack["state"] == "succeeded"
    assert service.pull()["count"] == 0
    _disarm()


def t_source_has_no_board_sockets():
    root = _OPS / "board_cp"
    for p in root.glob("*.py"):
        src = p.read_text(encoding="utf-8")
        assert "urllib.request" not in src, p.name
        assert "socket.socket" not in src, p.name
        assert "http.client" not in src, p.name


def t_chat_intent_queues_not_sends():
    _disarm()
    r = conversation.handle("به برد بگو سلام")
    assert r["kind"] == "board-command", r["kind"]
    assert r["external_effect"] is False
    assert r["send_attempted"] is False
    assert r["data"]["status"] == "BOARD_COMMAND_QUEUED"
    assert ":8796" in r["text"]  # negation in footer
    assert "ارسال نشده" in r["text"]
    r2 = conversation.handle("این پیام را برای مشتری بفرست")
    assert r2["kind"] == "owner-gate"


def t_panel_callbacks_same_queue():
    _disarm()
    r = conversation.callback("oc:board:panel:ziman")
    assert r["kind"] == "board-command"
    assert r["data"]["kind"] == "panel"
    t = conversation.callback("oc:board:task")
    assert t["data"]["kind"] == "task"
    assert t["data"]["may_authorize"] is True


def t_legs_not_stolen():
    from owner_console import legs_status as ls
    ls._reset_cache()
    old = ls._default_fetch
    ls._default_fetch = lambda url, timeout: 200
    try:
        r = conversation.handle("وضعیت بیزنس‌های برد")
        assert r["kind"] == "legs", r["kind"]
    finally:
        ls._default_fetch = old
        ls._reset_cache()


def t_board_command_not_sent_to_model():
    assert "board-command" not in col._LLM_KINDS
    assert "board-command" not in col._EVIDENCE_KINDS


def t_http_owner_vs_bearer():
    _disarm()
    st, body, _ = bhttp.dispatch("POST", "/api/board/commands",
                                 {"_body": b'{"kind":"ask","text":"x"}'},
                                 owner_ok=False)
    assert st == 403
    st, body, _ = bhttp.dispatch("POST", "/api/board/commands",
                                 {"_body": b'{"kind":"status","text":"x"}'},
                                 owner_ok=True)
    assert st == 200
    st, body, _ = bhttp.dispatch("GET", "/api/board-cp/pull", {}, owner_ok=False)
    assert st == 401
    _arm()
    service.enqueue(kind="ask", text="pull-me")
    st, body, _ = bhttp.dispatch(
        "GET", "/api/board-cp/pull",
        {"Authorization": "Bearer test-bearer-token"},
    )
    assert st == 200
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    _disarm()


def t_gateway_allowlist_and_no_initdata_on_pull():
    st, _, _ = _handle_core("POST", "/api/board/commands", {"_body": b"{}"})
    assert st in (403, 503)
    st, body, _ = _handle_core("GET", "/api/board-cp/pull", {})
    assert st == 401
    payload = json.loads(body.decode("utf-8"))
    assert payload.get("reason") == "board_bearer_required"


def t_control_url_not_in_queue_payload_as_board_api():
    _arm()
    stored = service.enqueue(kind="ask", text="no-board-api")
    row = __import__("board_cp.queue", fromlist=["get"]).get(stored["message_id"])
    raw = row["payload_json"]
    assert "/api/v1/command" not in raw
    assert "/api/v1/brain/ask" not in raw
    assert ":8796" not in raw
    _disarm()


TESTS = [
    t_gate0_rejects_board_hosts_and_8796,
    t_default_flag_off_no_pull,
    t_task_always_owner_required,
    t_ask_pull_ack_when_armed,
    t_source_has_no_board_sockets,
    t_chat_intent_queues_not_sends,
    t_panel_callbacks_same_queue,
    t_legs_not_stolen,
    t_board_command_not_sent_to_model,
    t_http_owner_vs_bearer,
    t_gateway_allowlist_and_no_initdata_on_pull,
    t_control_url_not_in_queue_payload_as_board_api,
]


if __name__ == "__main__":
    failed = 0
    for _t in TESTS:
        try:
            _t()
            print(f"  PASS  {_t.__name__}")
        except Exception as exc:
            failed += 1
            print(f"  FAIL  {_t.__name__}: {exc}")
    print(("FAIL" if failed else "OK"), f"{len(TESTS) - failed}/{len(TESTS)}")
    raise SystemExit(1 if failed else 0)
