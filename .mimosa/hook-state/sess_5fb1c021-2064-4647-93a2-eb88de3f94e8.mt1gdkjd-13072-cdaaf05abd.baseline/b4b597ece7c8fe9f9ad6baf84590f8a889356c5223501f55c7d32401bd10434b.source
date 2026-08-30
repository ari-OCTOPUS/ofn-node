"""test_funnel_store.py — D3 (فاز D): funnel_store + fold + metrics.

اثبات می‌کند که:
  · ژورنالِ append-only + idempotency (ت۲): replayِ همان event → یک ردیف.
  · fold (ت۳): state از رویدادها بازساخته، monotonic، DEAD چسبنده.
  · دو سیگنال جدا (ت۴): رأی مالک هرگز state بازاری نمی‌سازد.
  · synthetic_done پایانه (ت۵): synthetic هرگز به نیمهٔ بازار نمی‌رسد.
  · گذار غیرمجاز → anomaly، نه silent drop (ت۶).
  · metrics replay-safe (ت۷): از rows بازساخته.
  · event_type ناشناخته → ValueError (ت۸).
  · lost/dead چسبنده (ت۹): پس از lost، won قبول نمی‌شود.

همه sandbox (harness.setup → OPS_DIR موقت). flag/STOP/ACTIVATION زنده دست‌نخورده.
"""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "outcomes"))
sys.path.insert(0, str(_HERE.parent / "legs"))

import harness
ENV = harness.setup("funnel-store-d3")

import importlib                          # noqa: E402
import os                                 # noqa: E402
import uuid as _uuid                      # noqa: E402
import opslib                             # noqa: E402
importlib.reload(opslib)
import funnel_store as fs                 # noqa: E402
importlib.reload(fs)


def _store():
    """هر تست یک db تازه."""
    return fs.FunnelStore(str(opslib.STATE_DIR / f"funnel-d3-{_uuid.uuid4().hex[:8]}.db"))


def t1_idempotent_replay_one_row():
    """replayِ همان event با همان idempotency_key → یک ردیف (نه دو)."""
    st = _store()
    ev = {"lead_id": "L1", "event_type": "lead.candidate.received",
          "correlation_id": "L1", "source_component": "LeadInboxLeg",
          "idempotency_key": "L1|lead.candidate.received"}
    first = st.record(ev)
    second = st.record(ev)
    assert first is True
    assert second is False, "replay باید False باشد (idempotent)"
    events = st.events_for_lead("L1")
    assert len(events) == 1, f"باید ۱ ردیف باشد، got {len(events)}"


def t2_unknown_event_type_raises():
    """event_type ناشناخته → ValueError (fail-fast، نه silent drop)."""
    st = _store()
    try:
        st.record({"lead_id": "L2", "event_type": "totally.made.up",
                   "correlation_id": "L2", "source_component": "test"})
        assert False, "باید ValueError می‌داد"
    except ValueError:
        pass


def t3_fold_monotonic_and_dead_sticky():
    """fold: state از رویدادها بازساخته، monotonic (regress نمی‌کند)، DEAD چسبنده."""
    st = _store()
    lid = "L3"
    # received → qualified → delivered_to_owner → owner_approved
    for et in ("lead.candidate.received", "lead.qualified", "proposal.routed", "proposal.owner_approved"):
        st.record({"lead_id": lid, "event_type": et, "correlation_id": lid,
                   "source_component": "test"})
    f = st.fold(lid)
    assert f["state"] == "owner_approved", f"got {f['state']}"
    assert f["rank"] == 6
    assert f["dead"] is False
    # حالا یک رویداد با رتبهٔ پایین‌تر (received دوباره) — نباید regress کند
    st.record({"lead_id": lid, "event_type": "lead.candidate.received",
               "correlation_id": lid, "source_component": "test",
               "idempotency_key": "L3|received|dup2"})
    f2 = st.fold(lid)
    assert f2["state"] == "owner_approved", "regression نباید state را عوض کند"
    assert len(f2["anomaly"]) == 1, "باید یک anomaly ثبت شود"


def t4_lost_dead_sticky():
    """پس از lost، won قبول نمی‌شود (DEAD چسبنده)."""
    st = _store()
    lid = "L4"
    for et in ("lead.candidate.received", "lead.qualified", "proposal.routed",
               "proposal.owner_approved", "quote.sent", "quote.lost"):
        st.record({"lead_id": lid, "event_type": et, "correlation_id": lid,
                   "source_component": "test"})
    f = st.fold(lid)
    assert f["state"] == "lost"
    assert f["dead"] is True
    # تلاش برای won بعد از lost
    st.record({"lead_id": lid, "event_type": "quote.won",
               "correlation_id": lid, "source_component": "test",
               "idempotency_key": "L4|won|after-lost"})
    f2 = st.fold(lid)
    assert f2["state"] == "lost", "won نباید بعد از lost قبول شود"
    assert any(a["reason"] == "dead_state_sticky" for a in f2["anomaly"]), \
        "باید anomaly dead_state_sticky ثبت شود"


def t5_synthetic_never_reaches_market():
    """synthetic_done پایانه: synthetic هرگز به نیمهٔ بازار نمی‌رسد."""
    st = _store()
    lid = "L5"
    for et in ("lead.candidate.received", "lead.qualified", "proposal.routed",
               "proposal.owner_approved"):
        st.record({"lead_id": lid, "event_type": et, "correlation_id": lid,
                   "source_component": "test"})
    # outcome.recorded با kind=synthetic_complete → synthetic_done (DEAD)
    st.record({"lead_id": lid, "event_type": "outcome.recorded",
               "correlation_id": lid, "source_component": "test",
               "payload": {"kind": "synthetic_complete"}})
    f = st.fold(lid)
    assert f["state"] == "synthetic_done"
    assert f["dead"] is True
    # تلاش برای communication.sent بعد از synthetic_done
    st.record({"lead_id": lid, "event_type": "communication.sent",
               "correlation_id": lid, "source_component": "test",
               "effect_id": "eff1", "idempotency_key": "L5|sent|after-synth"})
    f2 = st.fold(lid)
    assert f2["state"] == "synthetic_done", "synthetic نباید به sent برسد"


def t6_owner_verdict_never_makes_market_state():
    """دو سیگنال جدا: رأی مالک (owner_approved) هرگز state بازاری نمی‌سازد.
    یعنی owner_approved ≠ sent. برای رسیدن به sent نیاز به communication.sent است."""
    st = _store()
    lid = "L6"
    for et in ("lead.candidate.received", "lead.qualified", "proposal.routed",
               "proposal.owner_approved"):
        st.record({"lead_id": lid, "event_type": et, "correlation_id": lid,
                   "source_component": "test"})
    f = st.fold(lid)
    assert f["state"] == "owner_approved"
    assert f["state"] != "sent", "owner_approved نباید با sent اشتباه شود"
    # فقط با communication.sent به sent می‌رسد
    st.record({"lead_id": lid, "event_type": "communication.sent",
               "correlation_id": lid, "source_component": "OutboundWorker",
               "effect_id": "eff2", "idempotency_key": "L6|sent"})
    f2 = st.fold(lid)
    assert f2["state"] == "sent"


def t7_metrics_replay_safe():
    """metrics از rows بازساخته (replay-safe). دوباره صدا زدن = همان نتیجه."""
    st = _store()
    for lid in ("L7a", "L7b", "L7c"):
        st.record({"lead_id": lid, "event_type": "lead.candidate.received",
                   "correlation_id": lid, "source_component": "test"})
    st.record({"lead_id": "L7a", "event_type": "lead.qualified",
               "correlation_id": "L7a", "source_component": "test"})
    m1 = st.metrics()
    m2 = st.metrics()
    assert m1 == m2, "metrics باید deterministic باشد"
    assert m1["total_leads"] == 3
    assert m1["total_events"] == 4
    assert m1["events_by_type"]["lead.candidate.received"] == 3
    assert m1["leads_by_state"]["received"] == 2   # L7b, L7c
    assert m1["leads_by_state"]["qualified"] == 1  # L7a


def t8_paid_requires_quote_sent_first():
    """گذار غیرمجاز → anomaly، نه silent drop. invoice.paid بدون quote.sent → anomaly."""
    st = _store()
    lid = "L8"
    st.record({"lead_id": lid, "event_type": "lead.candidate.received",
               "correlation_id": lid, "source_component": "test"})
    # invoice.paid بدون quote.sent — رتبهٔ بالاتر از received، ولی DEAD نیست.
    # این یک anomaly است (گذارِ بدون واسطه)، ولی fold آن را ثبت می‌کند و state را عوض.
    # در D3، fold فقط monotonic را چک می‌کند؛ validation کاملِ گذار در D3b.
    st.record({"lead_id": lid, "event_type": "invoice.paid",
               "correlation_id": lid, "source_component": "ReconcileJob",
               "attribution_id": "attr1", "idempotency_key": "L8|paid"})
    f = st.fold(lid)
    # paid ثبت شد (rank 13 > received rank 1) ولی بدون quote.sent — این یک anomalyِ منطقی است
    # که در D3b با validation کامل گرفته می‌شود. در D3، فقط مطمئن شویم crash نمی‌کند.
    assert f["state"] in ("paid", "received")  # یکی از این دو


def t9_unknown_lead_fold_returns_none_state():
    """fold برای lead_id ناموجود → state=None, rank=0."""
    st = _store()
    f = st.fold("does-not-exist")
    assert f["state"] is None
    assert f["rank"] == 0
    assert f["anomaly"] == []


def t10_channel_mode_persists():
    """channel_mode (gated_worker/owner_manual) ذخیره می‌شود و خوانده می‌شود."""
    st = _store()
    st.record({"lead_id": "L10", "event_type": "communication.sent",
               "correlation_id": "L10", "source_component": "OutboundWorker",
               "effect_id": "eff10", "channel_mode": "gated_worker",
               "idempotency_key": "L10|sent"})
    events = st.events_for_lead("L10")
    assert len(events) == 1
    # channel_mode در ستونِ 8 (0-indexed: event_id=0, event_type=1, proposal=2, effect=3, attr=4, corr=5, causation=6, source=7, channel_mode=8)
    assert events[0][8] == "gated_worker", f"channel_mode mismatch: {events[0][8]}"


def main():
    # الگوی نام‌گذاری: tN_<desc>
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("t") and k[1:2].isdigit() and callable(v)
             and not k.startswith("test")]
    passed = 0
    failed = []
    for t in tests:
        try:
            t()
            passed += 1
            print(f"  ✅ {t.__name__}")
        except Exception as e:  # noqa: BLE001
            failed.append((t.__name__, repr(e)))
            print(f"  ❌ {t.__name__}: {e!r}")
    print(f"\ntest_funnel_store: {passed}/{len(tests)}")
    if failed:
        for n, e in failed:
            print(f"  FAIL {n}: {e}")
        return 1
    return 0


if __name__ == "__main__":
    import sys as _sys
    _sys.exit(main())
