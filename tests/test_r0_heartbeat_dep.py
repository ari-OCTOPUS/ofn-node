"""Heartbeat dependency restore — outbound_worker was a lazy-import closure miss
in PR #101 (top-level-only import scan). This pins the regression: heartbeat
must import and emit its honest JSON pulse even when nothing is armed."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

AGENTS = Path(__file__).resolve().parents[1] / "ofn" / "agents"
sys.path.insert(0, str(AGENTS))
sys.path.insert(0, str(AGENTS.parent / "budget"))


def test_outbound_worker_imports() -> None:
    import outbound_worker  # noqa: F401


def test_heartbeat_pulse_is_honest_json() -> None:
    # 2026-09-03: «unarmed» باید خصوصیتِ تست باشد نه فرضِ میزبان — رویِ
    # میزبانِ مسلح (توکن واقعی در env) ارسالِ واقعیِ صادقانه ok=True می‌دهد
    # و آن هم درست است. پس توکن‌ها را از محیطِ فرزند حذف می‌کنیم تا مسیرِ
    # unarmed قطعی آزموده شود.
    import os
    import tempfile
    fake_home = tempfile.TemporaryDirectory()  # secrets فایل هم غایب شود
    child_env = {k: v for k, v in os.environ.items()
                 if k not in ("OFN_BOT_TOKEN_OWNER", "OFN_OWNER_USER_IDS")}
    child_env["HOME"] = fake_home.name
    proc = subprocess.run(
        [sys.executable, str(AGENTS / "heartbeat.py")],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=str(AGENTS),
        env=child_env,
    )
    assert proc.returncode == 0, proc.stderr[-400:]
    payload = json.loads(proc.stdout)
    assert "line" in payload
    assert payload.get("tg", {}).get("ok") is False  # unarmed host must not claim a send
    fake_home.cleanup()
