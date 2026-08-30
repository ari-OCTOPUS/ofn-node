"""test_heart_cognition_wiring.py — reachabilityِ کانالِ «value» قلب (2026-07-21).

اثبات می‌کند: تأییدِ owner (live_loop.apply_ari_verdict approved=True) یک effectِ شناختیِ
external-validated ثبت می‌کند و producers._count_cognition آن را می‌خواند — بستنِ orphanِ
cognition_effect.record. flag خاموش = بایت‌به‌بایت؛ reject هیچ ثبت نمی‌کند؛ validator همیشه owner
(هرگز خودسنجی).
"""
import datetime as dt
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "heart"))

import harness
ENV = harness.setup("heart-cognition-wiring")

import importlib                     # noqa: E402
import opslib                        # noqa: E402
importlib.reload(opslib)
import live_loop                     # noqa: E402
importlib.reload(live_loop)
import heart.cognition_effect as ce  # noqa: E402
importlib.reload(ce)
import heart.producers as producers  # noqa: E402
importlib.reload(producers)


class _FakeBus:
    def __init__(self):
        self.published = []

    def publish(self, topic, payload, actor=None):
        self.published.append((topic, payload, actor))
        return {"ok": True}

    def subscribe(self, *a, **k):
        return None


def _ll():
    return live_loop.LiveLoop(bus=_FakeBus())


def _clear():
    os.environ.pop("OCTOPUS_WIRE_COGNITION_EFFECT", None)


def t_a_flag_off_no_cognition_recorded():
    """flag خاموش → apply_ari_verdict چیزی در استریمِ cognition نمی‌نویسد (parity)."""
    _clear()
    ll = _ll()
    ll.apply_ari_verdict("proposal-1", True, project="Lead-نقاشی")
    assert not ce.STREAM_PATH.exists(), "flag خاموش نباید cognition ثبت کند"


def t_b_flag_on_approve_records_and_producer_reads():
    """flag روشن + approve → effectِ cognition ثبت می‌شود (validator=owner) و producers می‌خواند."""
    os.environ["OCTOPUS_WIRE_COGNITION_EFFECT"] = "1"
    try:
        ll = _ll()
        ll.apply_ari_verdict("proposal-A", True, project="Lead")
        ll.apply_ari_verdict("proposal-B", True, project="Ziman")
    finally:
        _clear()
    recs = [json.loads(l) for l in open(ce.STREAM_PATH, encoding="utf-8")]
    assert len(recs) >= 2, recs
    assert all(r["validator"] == "owner" for r in recs)         # فقط بیرونی
    since = dt.datetime.now() - dt.timedelta(hours=1)
    assert producers._count_cognition(since) >= 2


def t_c_reject_records_no_cognition():
    """reject (approved=False) = صفر cognition (فقط تأییدِ بیرونی ارزش است)."""
    os.environ["OCTOPUS_WIRE_COGNITION_EFFECT"] = "1"
    before = sum(1 for _ in open(ce.STREAM_PATH, encoding="utf-8")) if ce.STREAM_PATH.exists() else 0
    try:
        ll = _ll()
        ll.apply_ari_verdict("proposal-R", False, project="Lead")
    finally:
        _clear()
    after = sum(1 for _ in open(ce.STREAM_PATH, encoding="utf-8")) if ce.STREAM_PATH.exists() else 0
    assert after == before, "reject نباید cognition ثبت کند"


def t_e_live_verdict_path_feeds_channel_and_idempotent():
    """مسیرِ زندهٔ رأی (record_proposal_outcome_by_token، دکمهٔ کارتِ تلگرام) کانالِ cognition را
    واقعاً تغذیه می‌کند (نه فقط apply_ari_verdictِ mock) — و گاردِ `decided` idempotency می‌دهد."""
    os.environ["OCTOPUS_WIRE_COGNITION_EFFECT"] = "1"
    try:
        ll = _ll()
        ll._proposal_cb["tok-1"] = {"proposal_id": "p-live-1", "leg_id": "lead", "amount": 120.0}
        r1 = ll.record_proposal_outcome_by_token("tok-1", "ok")     # approve
        r2 = ll.record_proposal_outcome_by_token("tok-1", "ok")     # double-tap → decided guard
    finally:
        _clear()
    assert r1 is not None
    assert r2 is None, "double-tap باید با گاردِ decided رد شود (idempotency)"
    recs = [json.loads(l) for l in open(ce.STREAM_PATH, encoding="utf-8")]
    live = [r for r in recs if r.get("artifact_id") == "p-live-1"]
    assert len(live) == 1, live                                    # دقیقاً یک ثبت، نه دو
    assert live[0]["validator"] == "owner" and live[0]["leg"] == "lead"


def t_d_structural_flag_gated_fail_soft():
    """ساختاری: هوکِ cognition پشتِ approved + lazy + try/except (هرگز مسیرِ verdict را نمی‌کشد)."""
    src = Path(live_loop.__file__).read_text("utf-8")
    seg = src.split("def apply_ari_verdict")[1].split("\n    def ")[0]
    assert "cognition_effect" in seg and "validator=\"owner\"" in seg
    assert "if approved:" in seg and "except Exception" in seg
    assert ce.enabled() is False                                # flag پیش‌فرض خاموش


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_heart_cognition_wiring: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
