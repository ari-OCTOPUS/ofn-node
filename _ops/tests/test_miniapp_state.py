#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_miniapp_state.py â€” ØªØ³Øªâ€ŒÙ‡Ø§ÛŒ ÙˆØ§Ø­Ø¯ Ø¨Ø±Ø§ÛŒ MiniApp read-only state helpers.

Ù‚Ø±Ø§Ø±Ø¯Ø§Ø¯ (PHASE 4 megaprompt): read-onlyØŒ secret-scrubbedØŒ fail-closedØŒ JSON-safe.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_OPS), str(_HERE), str(_OPS / "legs"), str(_OPS / "telegram_center"), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import harness  # noqa: E402
ENV = harness.setup("miniapp-state")

import miniapp_state  # noqa: E402


def t_state_missing_returns_unknown_not_fake():
    # remove ORGANISM-STATE â†’ must be unknown, not ok with fake zeros
    with tempfile.TemporaryDirectory() as d:
        miniapp_state.STATE_DIR = Path(d)
        s = miniapp_state.get_miniapp_state()
    assert s["status"] == "unknown", s


def t_state_scrubs_secrets():
    # put a token-bearing state file and confirm scrub
    with tempfile.TemporaryDirectory() as d:
        sd = Path(d)
        (sd / "ORGANISM-STATE.json").write_text(
            json.dumps({"ts":"x","bot_token":"123456789:AAGxxxxxxxxxxxxxxxxxxxxxxxx",
                        "chat_id":999,"beat":1,"halted":False}), "utf-8")
        miniapp_state.STATE_DIR = sd
        s = miniapp_state.get_miniapp_state()
    blob = json.dumps(s)
    assert "AAGxxxx" not in blob, "token leaked!"
    assert "123456789:AAG" not in blob, "token pattern leaked!"


def t_dispatch_unknown_path_is_404():
    st, body, ct = miniapp_state.dispatch_api("/api/nope")
    assert st == 404, st


def t_dispatch_known_paths_return_200():
    for p in ["/api/state", "/api/outbound", "/api/legs", "/api/value",
              "/api/ui-registry", "/api/current-truth", "/api/ops"]:
        st, body, ct = miniapp_state.dispatch_api(p)
        assert st == 200, f"{p} -> {st}"
        # must be valid JSON
        json.loads(body)


def t_outbound_missing_db_is_honest():
    with tempfile.TemporaryDirectory() as d:
        miniapp_state._RUNTIME = Path(d)
        s = miniapp_state.get_outbound_state()
    assert s["status"] == "no_wal_db", s


def t_scrub_redacts_email():
    assert "<EMAIL_REDACTED>" in miniapp_state._scrub("contact armin@example.com now")


def t_scrub_redacts_token():
    out = miniapp_state._scrub("tok 9999999:AAGqwertyuiopasdfghjklzxcvbnm123")
    assert "9999999:AAG" not in out


CHECKS = [
    ("state missing â†’ unknown (not fake)", t_state_missing_returns_unknown_not_fake),
    ("state scrubs secrets", t_state_scrubs_secrets),
    ("dispatch unknown â†’ 404", t_dispatch_unknown_path_is_404),
    ("dispatch known â†’ 200 + valid JSON", t_dispatch_known_paths_return_200),
    ("outbound missing db â†’ honest", t_outbound_missing_db_is_honest),
    ("scrub redacts email", t_scrub_redacts_email),
    ("scrub redacts token", t_scrub_redacts_token),
]


if __name__ == "__main__":
    failed = harness.run(CHECKS)
    print(f"\n{'âœ…' if not failed else 'âŒ'} test_miniapp_state: {len(CHECKS) - failed}/{len(CHECKS)} passed")
    sys.exit(1 if failed else 0)
