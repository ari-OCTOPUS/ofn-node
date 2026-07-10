"""test_needs_nudge.py — جلسه ۴۶: needs_digest (نیازها) + نوتیفِ هوشمندِ ضدِ اسپم.

فقط‌خواندنی بودن، آیتم‌های درست، throttle با hash، kill-switch، و flag-off = no-op.
"""
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness
ENV = harness.setup("needs-nudge")

import needs_digest   # noqa: E402
import wiring         # noqa: E402
import opslib         # noqa: E402


class _FakeChannel:
    wired = True

    def __init__(self, pending=0):
        self.sent: list[tuple[str, dict | None]] = []
        self._pending_n = pending

    def _count_pending(self):
        return self._pending_n

    def send_text(self, text, reply_markup=None):
        self.sent.append((text, reply_markup))
        return True


def t_a_digest_empty_when_nothing_needed():
    """vault موقتِ تازه: فقط آیتم‌های ساختاریِ صادق (CSV پولی + chrono absent)."""
    d = needs_digest.compute()
    assert d["n"] <= 5 and isinstance(d["items"], list)
    joined = " ".join(d["items"])
    assert "CSV" in joined            # دادهٔ پولی واقعاً غایب است — نیازِ صادق
    assert "chrono.db" in joined


def t_b_digest_picks_up_pending_and_questions():
    """کارتِ معلق + سوالِ تازهٔ AGENT_QUESTIONS → آیتم‌های اول."""
    aq = Path(ENV["root"]) / "00 - Inbox" / "AGENT_QUESTIONS.md"
    aq.write_text(f"# سوالات\n\n## {opslib.today()} — تست\n\n1. سوالِ تازه؟\n", "utf-8")
    d = needs_digest.compute(pending_count=2)
    joined = " ".join(d["items"])
    assert "2 کارتِ تأیید" in joined
    assert "AGENT_QUESTIONS" in joined
    assert d["hash"] != needs_digest.compute(pending_count=0)["hash"]


def t_c_nudge_flag_off_noop():
    os.environ.pop("OCTOPUS_WIRE_NEEDS_NUDGE", None)
    assert wiring.needs_nudge_beat(_FakeChannel(), beat=720) is None


def t_d_nudge_sends_once_then_throttles():
    """ارسال فقط وقتی نیازها عوض شده — همان نیازها دوباره اسپم نمی‌شوند."""
    os.environ["OCTOPUS_WIRE_NEEDS_NUDGE"] = "1"
    try:
        ch = _FakeChannel(pending=1)
        wiring._NUDGE_STATE["last_epoch"] = 0
        r1 = wiring.needs_nudge_beat(ch, beat=360)
        assert r1 is not None and r1["sent"] is True, r1
        assert len(ch.sent) == 1
        text, kb = ch.sent[0]
        assert "نیازت دارم" in text and "menu:now" in json.dumps(kb)
        # همان وضعیت، epoch بعد → hash تغییری نکرده → ارسال نه
        wiring._NUDGE_STATE["last_epoch"] = 0
        r2 = wiring.needs_nudge_beat(ch, beat=720)
        assert r2 is not None and r2["sent"] is False, r2
        assert len(ch.sent) == 1
        # نیازِ نو (pending بیشتر) → hash عوض → ارسالِ دوباره
        ch._pending_n = 3
        wiring._NUDGE_STATE["last_epoch"] = 0
        r3 = wiring.needs_nudge_beat(ch, beat=1080)
        assert r3 is not None and r3["sent"] is True
        assert len(ch.sent) == 2
    finally:
        os.environ.pop("OCTOPUS_WIRE_NEEDS_NUDGE", None)


def t_e_nudge_kill_switch_and_antialias():
    os.environ["OCTOPUS_WIRE_NEEDS_NUDGE"] = "1"
    try:
        ch = _FakeChannel(pending=1)
        opslib.STOP_ORGANISM.write_text("stop", "utf-8")
        try:
            assert wiring.needs_nudge_beat(ch, beat=360) is None
        finally:
            opslib.STOP_ORGANISM.unlink()
        # پنجرهٔ ضدِ aliasing: همان epoch دوباره fire نمی‌شود
        wiring._NUDGE_STATE["last_epoch"] = 0
        wiring.needs_nudge_beat(ch, beat=360)
        assert wiring.needs_nudge_beat(ch, beat=360) is None
    finally:
        os.environ.pop("OCTOPUS_WIRE_NEEDS_NUDGE", None)


def t_f_structural_read_only():
    """ساختاری: digest هیچ نوشتنی ندارد؛ nudge فقط state-file خودش + sendMessage."""
    src = Path(needs_digest.__file__).read_text("utf-8")
    for bad in ("LockedJson", "append_jsonl", "ledger_note", "write_text",
                "import organ_gate", "import money_gate"):
        assert bad not in src, f"needs_digest باید فقط‌خواندنی باشد: {bad}"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_needs_nudge: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
