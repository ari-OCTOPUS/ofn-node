#!/usr/bin/env python3
"""تستِ مرحلهٔ ۳ نقشهٔ لید (2026-07-15): پلِ ایمیل → صندوقِ discovery.

اثبات می‌کند:
  (الف) parse_lead_from_email: ایمیلِ نقاشی → dictِ لید؛ ایمیلِ بی‌ربط → None.
  (ب) bridge_leads_to_inbox: لیدِ ایمیلی → فایلِ کاندید در lead-inbox با description
      (نگاشتِ subject+snippet) — و idempotent (همان email_id دوبار → یک فایل).
  (پ) end-to-end: کاندیدِ پل‌شده توسط lead_discovery_beat امتیاز می‌خورد.
  (ت) poll_and_digest بدونِ flag → no-op (بدونِ token هم fail-soft []).
$0 آفلاین؛ هیچ tokenِ واقعی؛ state ایزوله (harness).
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
ENV = harness.setup("email-lead-bridge")

_OPS = harness.SELF_OPS
for _p in (str(_OPS), str(_OPS / "legs"), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib          # noqa: E402
import wiring          # noqa: E402
import email_inbound   # noqa: E402

PAINT_MSG = {"id": "msg-abc123", "subject": "Quote for painting 3-bedroom unit",
             "from": "Jane Citizen <jane@example.com>",
             "date": "Wed, 15 Jul 2026 10:00:00 +1000",
             "snippet": "Hi, we need interior repaint of our apartment in Pyrmont…"}
SPAM_MSG = {"id": "msg-zzz", "subject": "Your invoice from CloudCo",
            "from": "billing@cloudco.example", "snippet": "monthly subscription receipt"}


class FakeLeg:
    def __init__(self):
        self.calls = []

    def intake(self, lead_name, expected_aud, cell="lead.doer", description="", day=None):
        self.calls.append(lead_name)
        return {"ok": True, "attribution_id": "LEAD-TEST-001",
                "cell": cell, "expected_aud": expected_aud}


def t_a_parse_detects_painting_lead():
    lead = email_inbound.parse_lead_from_email(PAINT_MSG)
    assert lead is not None and lead["source"] == "email", lead
    assert lead["email_id"] == "msg-abc123"
    assert email_inbound.parse_lead_from_email(SPAM_MSG) is None


def t_b_bridge_writes_candidate_idempotent():
    lead = email_inbound.parse_lead_from_email(PAINT_MSG)
    n1 = email_inbound.bridge_leads_to_inbox([lead])
    n2 = email_inbound.bridge_leads_to_inbox([lead])   # همان ایمیل دوباره
    assert (n1, n2) == (1, 0), (n1, n2)
    box = opslib.STATE_DIR / "legs" / "lead-inbox"
    p = box / "email-msg-abc123.json"
    assert p.exists(), list(box.glob("*"))
    cand = json.loads(p.read_text("utf-8"))
    assert cand["description"].startswith("Quote for painting"), cand
    assert cand["applicant"].startswith("Jane Citizen"), cand


def t_c_bridged_candidate_flows_through_discovery():
    """کاندیدِ ایمیلی (interior repaint apartment → paint_scope) واردِ discovery می‌شود."""
    os.environ["OCTOPUS_WIRE_LEAD_DISCOVERY"] = "1"
    try:
        leg = FakeLeg()
        wiring._EPOCH_STATE.clear()   # epoch-gate: beat=30 = پنجرهٔ ۱
        r = wiring.lead_discovery_beat(leg, beat=30)
        assert r is not None and r["sensed"] == 1, r
        # امتیازش هرچه باشد، پردازش شده و آرشیو شده — نه گم
        box = opslib.STATE_DIR / "legs" / "lead-inbox"
        assert not list(box.glob("*.json")), "کاندیدِ ایمیلی باید پردازش/منتقل شده باشد"
        results = [p for p in (box / "processed").glob("*.result.json")]
        assert len(results) == 1, results
    finally:
        os.environ.pop("OCTOPUS_WIRE_LEAD_DISCOVERY", None)


def t_d_poll_noop_without_flag():
    os.environ.pop("OCTOPUS_WIRE_EMAIL", None)
    d = email_inbound.poll_and_digest()
    assert d["n_unread"] == 0 and d["leads"] == [], d
    # پردازشِ پل هم بدونِ ورودی امن است
    assert email_inbound.bridge_leads_to_inbox([]) == 0


if __name__ == "__main__":
    for f in (t_a_parse_detects_painting_lead, t_b_bridge_writes_candidate_idempotent,
              t_c_bridged_candidate_flows_through_discovery, t_d_poll_noop_without_flag):
        f()
        print("ok", f.__name__)
    print("PASS test_email_lead_bridge")
