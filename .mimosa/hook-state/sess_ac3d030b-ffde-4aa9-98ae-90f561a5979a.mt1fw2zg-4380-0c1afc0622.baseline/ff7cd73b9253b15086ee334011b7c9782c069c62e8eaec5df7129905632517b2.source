#!/usr/bin/env python3
"""test_panic_command.py — اهرمِ زندهٔ master-kill مالک از تلگرام (WP1).

اثبات می‌کند:
  * handle_command("/panic") مرزِ سختِ سراسری HALT-ALL را می‌نویسد
    (opslib.master_halted() == "HALT-ALL" پس از آن) — قرینهٔ /stop، ولی سراسری.
  * handle_command("/resume") آن را آزاد می‌کند (master_halted() دوباره None).
  * updateِ غیرِمالک (chat_id != owner) از allowlistِ poll_once رد می‌شود و
    هیچ HALT-ALL نمی‌نویسد — دقیقاً مثلِ رفتارِ /stop برای غیرِمالک.
  * /stop تضعیف نشده: kill_switch همچنان STOP-ORGANISM می‌نویسد.

صفر نوشتن روی مسیرهای زنده: همهٔ path constantهای opslib به یک tmp dir مونکی‌پچ می‌شوند.
اجرا: python -X utf8 test_panic_command.py
"""
from __future__ import annotations

import pathlib
import sys
import tempfile

_HERE = pathlib.Path(__file__).resolve().parent
for _p in (_HERE.parent / "budget", _HERE.parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import opslib            # noqa: E402
import approval_channel  # noqa: E402


def _tmp() -> pathlib.Path:
    return pathlib.Path(tempfile.mkdtemp(prefix="panic-test-"))


def _isolate_opslib(d: pathlib.Path) -> None:
    """همهٔ پرچم‌ها و مقصدهای نوشتنِ opslib را به tmp ببر — صفر لمسِ زنده."""
    opslib.HALT_ALL = d / "HALT-ALL"
    opslib.STOP_ARCHITECT = d / "STOP-ARCHITECT"
    opslib.STOP_ORGANISM = d / "STOP-ORGANISM"
    opslib.ALERTS_MD = d / "alerts.md"
    opslib.STATE_DIR = d / "state"        # poll_once نبضِ pulse را اینجا می‌نویسد


def _channel(owner: int, state_dir: pathlib.Path):
    """کانالِ تلگرامیِ wired بدونِ شبکه: http تزریق‌شده = no-op (هیچ فراخوانیِ واقعی)."""
    return approval_channel.TelegramApprovalChannel(
        token="test-token", owner_chat_id=owner,
        http_get=lambda url, timeout: {"ok": True, "result": []},
        http_post=lambda url, body, timeout=10.0: {"ok": True},
        state_dir=state_dir,
    )


def test_panic_writes_halt_all() -> None:
    d = _tmp()
    _isolate_opslib(d)
    ch = _channel(owner=123, state_dir=d / "state")
    assert opslib.master_halted() is None
    reply = ch.handle_command("/panic")
    assert opslib.HALT_ALL.exists()
    assert opslib.master_halted() == "HALT-ALL"
    assert "HALT-ALL" in reply and "🔴" in reply


def test_resume_clears_halt_all() -> None:
    d = _tmp()
    _isolate_opslib(d)
    ch = _channel(owner=123, state_dir=d / "state")
    opslib.raise_halt_all("test setup")
    assert opslib.master_halted() == "HALT-ALL"
    reply = ch.handle_command("/resume")
    assert not opslib.HALT_ALL.exists()
    assert opslib.master_halted() is None
    assert "🟢" in reply


def test_nonowner_panic_does_not_write() -> None:
    """updateِ غیرِمالک از allowlistِ poll_once رد می‌شود — هیچ HALT-ALL نوشته نمی‌شود."""
    d = _tmp()
    _isolate_opslib(d)
    owner = 123
    nonowner_update = {
        "ok": True,
        "result": [{
            "update_id": 1,
            "message": {"chat": {"id": 999}, "from": {"id": 999}, "text": "/panic"},
        }],
    }
    ch = approval_channel.TelegramApprovalChannel(
        token="test-token", owner_chat_id=owner,
        http_get=lambda url, timeout: nonowner_update,
        http_post=lambda url, body, timeout=10.0: {"ok": True},
        state_dir=d / "state",
    )
    processed = ch.poll_once()           # update پردازش می‌شود ولی به‌خاطرِ allowlist رد
    assert processed == 1                 # آفستِ جلو رفت، اما دستور اجرا نشد
    assert not opslib.HALT_ALL.exists()  # ← هستهٔ اثبات: غیرِمالک HALT-ALL نمی‌نویسد
    assert opslib.master_halted() is None


def test_group_member_cannot_clear_halt_all() -> None:
    """red-team GOV-P1: در یک گروهِ allowlisted، عضوی که مالک نیست (from_id != owner)
    نباید بتواند با /resume مرزِ سختِ سراسری را پاک کند — عضویتِ chat کافی نیست."""
    d = _tmp()
    _isolate_opslib(d)
    ch = _channel(owner=123, state_dir=d / "state")
    opslib.raise_halt_all("test setup")
    assert opslib.master_halted() == "HALT-ALL"
    # عضوِ گروه (from_id=999) — گروه در allowlist است ولی فرستنده مالک نیست
    reply = ch.handle_command("/resume", chat_id=555, from_id=999)
    assert opslib.HALT_ALL.exists(), "غیرِمالک نباید HALT-ALL را پاک کند"
    assert opslib.master_halted() == "HALT-ALL"
    assert reply is not None and "مالک" in reply
    # همان دستور، همان گروه، ولی از خودِ مالک → پاک می‌شود
    reply2 = ch.handle_command("/resume", chat_id=555, from_id=123)
    assert not opslib.HALT_ALL.exists()
    assert opslib.master_halted() is None
    assert "🟢" in reply2


def test_group_member_cannot_panic_or_stop() -> None:
    """/panic و /stop هم owner-only اند حتی داخلِ گروهِ allowlisted."""
    d = _tmp()
    _isolate_opslib(d)
    (d / "state").mkdir(parents=True, exist_ok=True)
    ch = _channel(owner=123, state_dir=d / "state")
    assert "مالک" in ch.handle_command("/panic", chat_id=555, from_id=999)
    assert not opslib.HALT_ALL.exists()
    assert "مالک" in ch.handle_command("/stop", chat_id=555, from_id=999)
    assert not (d / "STOP-ORGANISM").exists()
    # backward-compat: from_id=None (فراخوانیِ برنامه‌ایِ owner-trusted) گارد را رد نمی‌کند
    ch.handle_command("/panic")
    assert opslib.HALT_ALL.exists()


def test_stop_still_writes_organism() -> None:
    """/stop تضعیف نشده: kill_switch همچنان STOP-ORGANISM می‌نویسد (state_dir → _ops)."""
    d = _tmp()
    _isolate_opslib(d)
    (d / "state").mkdir(parents=True, exist_ok=True)   # ops_dir = state.parent = d
    ch = _channel(owner=123, state_dir=d / "state")
    reply = ch.handle_command("/stop")
    assert (d / "STOP-ORGANISM").exists()              # kill_switch → ops_dir/STOP-ORGANISM
    assert "KILL-SWITCH" in reply
    assert not opslib.HALT_ALL.exists()                # /stop سراسری نمی‌نویسد


if __name__ == "__main__":
    _tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for _t in _tests:
        _t()
        print(f"  ✓ {_t.__name__}")
    print(f"✅ test_panic_command: {len(_tests)}/{len(_tests)} سبز")
