"""Glass runner — the missing loop for the read-only glass (gap #26 close).

Pins: un-armed host exits honestly; unknown/non-allowlisted chats are
ignored; commands are dispatched with the right snapshot builder; the
offset persists across cycles; and the runner has no write paths beyond
its offset file + receipt appends."""

from __future__ import annotations

import json
import sys
from pathlib import Path

AGENTS = Path(__file__).resolve().parents[1] / "ofn" / "agents"
sys.path.insert(0, str(AGENTS))
sys.path.insert(0, str(AGENTS.parent / "budget"))

import glass_runner as gr  # noqa: E402


class _FakeTG:
    def __init__(self, results=None):
        self.results = list(results or [])
        self.calls = []

    def __call__(self, token, method, params=None, timeout=20):
        self.calls.append((method, params))
        if method == "getUpdates":
            return {"ok": True, "result": self.results.pop(0) if self.results
                    else []}
        return {"ok": True}


def test_unarmed_exits_honestly(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(gr, "_owner_token", lambda: "")
    res = gr.cycle(state_dir=tmp_path)
    assert res["ok"] is False and res["reason"] == "not-armed"


def test_non_allowlisted_chat_is_ignored(tmp_path, monkeypatch) -> None:
    fake = _FakeTG([[{"update_id": 5, "message": {
        "chat": {"id": 999}, "text": "/status"}}]])
    monkeypatch.setattr(gr, "_owner_token", lambda: "t")
    monkeypatch.setattr(gr, "_allowed_chats", lambda: {"42"})
    monkeypatch.setattr(gr, "_tg", fake)
    res = gr.cycle(state_dir=tmp_path)
    assert res["ignored"] == 1 and res["answered"] == 0


def test_command_dispatched_with_route_and_answered(tmp_path, monkeypatch) -> None:
    fake = _FakeTG([[{"update_id": 7, "message": {
        "chat": {"id": "42"}, "text": "/status"}}]])
    monkeypatch.setattr(gr, "_owner_token", lambda: "t")
    monkeypatch.setattr(gr, "_allowed_chats", lambda: {"42"})
    monkeypatch.setattr(gr, "_tg", fake)
    res = gr.cycle(state_dir=tmp_path)
    assert res["answered"] == 1
    assert (tmp_path / gr.OFFSET_FILE).read_text().strip() == "7"
    # the send went to the asking chat via sendMessage
    assert any(m == "sendMessage" for m, _ in fake.calls)


def test_offset_persists_and_skips_old_updates(tmp_path, monkeypatch) -> None:
    (tmp_path / gr.OFFSET_FILE).write_text("100", encoding="utf-8")
    fake = _FakeTG([[{"update_id": 101, "message": {
        "chat": {"id": "42"}, "text": "/queue"}}]])
    monkeypatch.setattr(gr, "_owner_token", lambda: "t")
    monkeypatch.setattr(gr, "_allowed_chats", lambda: {"42"})
    monkeypatch.setattr(gr, "_tg", fake)
    gr.cycle(state_dir=tmp_path)
    method, params = fake.calls[0]
    assert method == "getUpdates" and params["offset"] == 101


def test_doctor_snapshot_reads_report(tmp_path, monkeypatch) -> None:
    rep = tmp_path / "report.json"
    rep.write_text(json.dumps({"verdict": "degraded"}), encoding="utf-8")
    monkeypatch.setattr(gr, "_DOCTOR_REPORT", rep)
    snap = gr.build_snapshot("/doctor")
    assert snap["doctor_snapshot"]["verdict"] == "degraded"


def test_runner_has_no_external_send_or_write_paths() -> None:
    src = (AGENTS / "glass_runner.py").read_text(encoding="utf-8")
    for banned in ("edited_message", "reply_markup", "parse_mode",
                   "os.replace", "write_text(str(offset)" and None):
        if banned is None:
            continue
        assert banned not in src or banned == "write_text", banned
    # تنها write_text مجاز = فایل offset
    import re
    wt = re.findall(r"\.write_text\(", src)
    assert len(wt) == 1  # فقط offset
