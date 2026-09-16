# -*- coding: utf-8 -*-
"""F-NEW-3 acceptance: every OPS_B_BLOCKED emit must carry a request identifier
(so blockers are joinable to the queue without manual matching)."""
import re
from pathlib import Path

SRC = Path(__file__).with_name("base_fnew3.py")


def test_every_blocked_emit_carries_request():
    text = SRC.read_text(encoding="utf-8")
    emits = [l for l in text.splitlines() if 'receipt("OPS_B_BLOCKED"' in l]
    assert emits, "no OPS_B_BLOCKED emits found"
    for e in emits:
        assert "request=" in e, f"emit lacks request provenance: {e.strip()}"


def test_no_blocked_emit_without_request_context():
    text = SRC.read_text(encoding="utf-8")
    bad = re.findall(r'receipt\("OPS_B_BLOCKED"[^)]*\)', text)
    assert bad and all("request=" in b for b in bad)
