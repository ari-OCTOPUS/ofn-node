#!/usr/bin/env python3
"""test_rfc_submit_blocked.py — W7: چرا هیچ verdict وارد سیستم نشد.

بدونِ OCTOPUS_CB_SECRET کارتِ RFC اصلاً mint نمی‌شود (prepare_rfc_card → None) و
submit_for_approval بی‌صدا 'submit-failed' می‌گذاشت — یعنی RFC هرگز re-submit نمی‌شد و
مالک هیچ‌وقت دکمه‌ای برای تپیدن نداشت. $0 آفلاین، صفر شبکه، صفر ارسال.
"""
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "doctor"))
import harness
ENV = harness.setup("rfc-submit-blocked")

from doctor import Doctor, RFC   # noqa: E402
import outcomes.pending_card_recovery as pcr   # noqa: E402

_STATE = str(ENV["ops"] / "state")


class _WiredChannelNoSecret:
    """کانالِ wiredِ واقعی‌نما: rfc_card دقیقاً مثلِ تولید عمل می‌کند —
    بدونِ راز، prepare_rfc_card=None → False (هیچ POSTی در کار نیست)."""
    wired = True
    _owner = 12345

    def rfc_card(self, rfc_id, summary):
        return bool(pcr.prepare_rfc_card(state_dir=_STATE, rfc_id=rfc_id,
                                         summary=summary, owner=self._owner))


def _doctor(ch):
    return Doctor(state_dir=_STATE, approval_channel=ch, db=None)


def t_probe_reports_no_secret():
    os.environ.pop("OCTOPUS_CB_SECRET", None)
    ready, reason = pcr.card_delivery_ready(12345)
    assert ready is False and reason == "no-secret", (ready, reason)


def t_blocked_submit_stays_resubmittable():
    """بدونِ راز: status باید 'submitted-no-channel' باشد (نه submit-failed) تا
    _sweep_stale_rfcs بعد از provisioning دوباره submit کند."""
    os.environ.pop("OCTOPUS_CB_SECRET", None)
    doc = _doctor(_WiredChannelNoSecret())
    rfc = RFC(rfc_id="RFC-w7a", bottleneck="bn", fix="a long enough fix text",
              expected_lift="lift")
    doc._rfcs[rfc.rfc_id] = rfc
    assert doc.submit_for_approval(rfc) is False
    assert rfc.status == "submitted-no-channel", rfc.status


def t_card_is_minted_when_secret_present():
    """با راز: توکن mint می‌شود → rfc_card=True → status=submitted."""
    os.environ["OCTOPUS_CB_SECRET"] = "test-only-not-a-real-secret"
    try:
        doc = _doctor(_WiredChannelNoSecret())
        rfc = RFC(rfc_id="RFC-w7b", bottleneck="bn", fix="a long enough fix text",
                  expected_lift="lift")
        doc._rfcs[rfc.rfc_id] = rfc
        assert doc.submit_for_approval(rfc) is True
        assert rfc.status == "submitted", rfc.status
    finally:
        os.environ.pop("OCTOPUS_CB_SECRET", None)


if __name__ == "__main__":
    failed = harness.run([
        ("پروب: بدونِ راز → no-secret", t_probe_reports_no_secret),
        ("submit بلاک‌شده → submitted-no-channel", t_blocked_submit_stays_resubmittable),
        ("با راز → کارت mint و submitted", t_card_is_minted_when_secret_present),
    ])
    sys.exit(1 if failed else 0)
