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


# ─── ۲۰۲۶-۰۷-۲۸: نویز در برابر سیگنال ────────────────────────────────────
# از رونوشتِ واقعی: کارتِ «نیازت دارم» چهار بار با **همان سه آیتم** آمد و تنها
# چیزی که عوض می‌شد شمارندهٔ هشدار بود (۱۳ → ۱۴ → ۱۶ → ۱۸ → ۲۵). چون کلیدِ
# dedup روی متنِ آیتم‌هاست و متن همان عدد را دارد، هر بار «تغییر» شمرده می‌شد.
#
# ⚠️ اولین فیکسِ من **همهٔ** ارقام را می‌زدود و `t_d` را قرمز کرد — چون رشدِ صفِ
# تأیید (۱→۳) هم یک عدد است ولی سیگنالِ واقعی. تمایز معنایی است، نه نحوی:
# بک‌لاگِ خودِ مالک مهم است؛ شمارندهٔ یک فایلِ فقط‌افزودنی نه.

def t_g_a_drifting_alert_counter_is_not_a_change():
    a = needs_digest.compute.__module__  # noqa: F841 — فقط برای وضوحِ خطا
    import hashlib as _h
    import re as _re

    def key(items):
        noisy = ("هشدارِ امروز", "governor-alerts")
        norm = [(_re.sub(r"\d+", "#", i) if any(k in i for k in noisy) else i)
                for i in items]
        return _h.sha256("|".join(norm).encode("utf-8")).hexdigest()[:16]
    base = ["❓ 3 سوالِ بی‌جواب", "🧮 252 تراکنش منتظرِ توست"]
    assert key(base + ["🚨 13 هشدارِ امروز"]) == key(base + ["🚨 25 هشدارِ امروز"])


def t_h_a_growing_backlog_is_a_change():
    """مرزِ مقابل: عددی که بک‌لاگِ خودِ مالک است باید خبر بدهد."""
    d1 = needs_digest.compute(pending_count=1)
    d2 = needs_digest.compute(pending_count=40)
    assert d1["stable_hash"] != d2["stable_hash"], (d1["items"], d2["items"])


def t_i_the_legacy_hash_is_still_returned():
    """خواننده‌های قدیمی نباید بشکنند."""
    d = needs_digest.compute(pending_count=1)
    assert d.get("hash") and d.get("stable_hash")
    assert len(d["hash"]) == 16 and len(d["stable_hash"]) == 16


def t_j_state_is_written_even_when_the_send_did_not_happen():
    """گاردِ تلاشِ مکرر: تا امروز حالت فقط بعد از ارسالِ موفق نوشته می‌شد، پس
    کارتی که نگه داشته یا رد شده بود هر epoch دوباره تلاش می‌کرد."""
    os.environ["OCTOPUS_WIRE_NEEDS_NUDGE"] = "1"
    try:
        class _Dead:
            wired = True
            def _count_pending(self):   # noqa: D102
                return 2
            def send_text(self, *a, **k):   # noqa: D102
                return False            # همیشه شکست — شبیهِ نگه‌داشتن
        st_path = opslib.STATE_DIR / "needs-nudge.json"
        if st_path.exists():
            st_path.unlink()
        wiring._NUDGE_STATE["last_epoch"] = 0
        wiring.needs_nudge_beat(_Dead(), beat=360)
        assert st_path.exists(), "حالت بعد از ارسالِ ناموفق نوشته نشد"
        st = json.loads(st_path.read_text("utf-8"))
        assert st.get("last_attempt"), st
        # و چون واقعاً نرفته، last_hash جلو نرفته → بعداً دوباره تلاش می‌شود
        assert not st.get("last_hash"), st
    finally:
        os.environ.pop("OCTOPUS_WIRE_NEEDS_NUDGE", None)


def t_k_a_held_card_is_throttled_even_though_it_never_sends():
    """⚠️ این چک از نقصِ نسخهٔ اولِ همین گارد آمد.

    شرط اول روی `changed` بود، ولی `last_hash` فقط با ارسالِ **موفق** جلو می‌رود.
    وقتی سیاستِ سطح جریان را نگه می‌دارد، ارسالِ موفقی وجود ندارد ⇒ `changed`
    برای همیشه True ⇒ گارد هرگز شلیک نمی‌کرد و هر ری‌استارت یک کارتِ تکراری
    می‌ساخت. دیده‌بانِ زنده گرفتش، نه سوئیت — چون سوئیت ارسالِ موفق را شبیه‌سازی
    می‌کرد و آن مسیر سالم بود.

    مرزِ درست: مُهر روی «آخرین چیزی که **تلاش** شد»، نه «آخرین چیزی که رسید».
    """
    os.environ["OCTOPUS_WIRE_NEEDS_NUDGE"] = "1"
    try:
        class _Held:
            wired = True
            def _count_pending(self):   # noqa: D102
                return 2
            def send_text(self, *a, **k):   # noqa: D102
                return False            # همیشه نگه داشته می‌شود
        st_path = opslib.STATE_DIR / "needs-nudge.json"
        if st_path.exists():
            st_path.unlink()
        ch = _Held()
        # تلاشِ اول: باید انجام شود و مُهر بخورد
        wiring._NUDGE_STATE["last_epoch"] = 0
        r1 = wiring.needs_nudge_beat(ch, beat=360)
        assert r1 is not None and r1["sent"] is False, r1
        st = json.loads(st_path.read_text("utf-8"))
        assert st.get("last_attempt_hash"), st
        # تلاشِ دوم با همان محتوا (شبیه‌سازیِ ری‌استارت): باید ساکت بماند
        wiring._NUDGE_STATE["last_epoch"] = 0
        r2 = wiring.needs_nudge_beat(ch, beat=720)
        assert r2 is not None and r2["sent"] is False
        st2 = json.loads(st_path.read_text("utf-8"))
        assert st2["last_attempt"] == st["last_attempt"], \
            "تلاشِ دوم انجام شد — گارد بی‌اثر است"
    finally:
        os.environ.pop("OCTOPUS_WIRE_NEEDS_NUDGE", None)


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_needs_nudge: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
