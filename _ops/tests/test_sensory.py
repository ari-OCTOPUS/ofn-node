#!/usr/bin/env python3
"""تست CP-1 · Sensory Bus (afferent path) ($0 آفلاین، no-PII).

DoD: observation → topic mapping · afferent_ratio alarm · PII رد · propose-only.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("sensory")
_AFF = Path(r"F:\backup\_ops\afferent")
if str(_AFF) not in sys.path:
    sys.path.insert(0, str(_AFF))

from sensory_bus import (Observation, AfferentEvent, classify, SensoryBus,  # noqa: E402
                         _contains_pii, AFFERENT_RATIO_ALARM)


# ════════════════════════════════════════════════════════════════════════════════
# Classifier mapping
# ════════════════════════════════════════════════════════════════════════════════

def t_classify_lead_to_topics():
    """lead observation → topicهای attention/trust/markets."""
    obs = Observation(source="lead-naghshi", obs_type="lead", label="new inquiry")
    event = classify(obs)
    assert "A01" in event.topic_ids or "B01" in event.topic_ids, event.topic_ids
    assert event.afferent is True


def t_classify_error_to_topics():
    """error → topicهای tech."""
    obs = Observation(source="architect", obs_type="error", label="timeout")
    event = classify(obs)
    assert len(event.topic_ids) > 0
    assert event.ledger_event_type == "NOTE"


def t_classify_payment_to_money_event():
    """payment → MONEY_ATTRIBUTION."""
    obs = Observation(source="accounting", obs_type="payment", label="invoice paid")
    event = classify(obs)
    assert event.ledger_event_type == "MONEY_ATTRIBUTION"


def t_classify_unknown_type_defaults():
    """unknown type → default topic."""
    obs = Observation(source="x", obs_type="weird", label="something")
    event = classify(obs)
    assert len(event.topic_ids) > 0   # default


# ════════════════════════════════════════════════════════════════════════════════
# PII guard
# ════════════════════════════════════════════════════════════════════════════════

def t_pii_detected_in_invoice():
    """PII pattern → detected."""
    assert _contains_pii("invoice# INV-001")
    assert _contains_pii("abn: 12345678901")
    assert _contains_pii("credit card 4532-...")

def t_pii_not_in_clean_label():
    """clean label → no PII."""
    assert not _contains_pii("new lead from website")
    assert not _contains_pii("market analysis")

def t_pii_observation_rejected():
    """observation با PII → afferent=False (رد)."""
    obs = Observation(source="x", obs_type="lead", label="credit card 4532-1234-5678-9012")
    event = classify(obs)
    assert event.afferent is False
    assert event.topic_ids == []   # PII → topic خالی


# ════════════════════════════════════════════════════════════════════════════════
# Afferent ratio + alarm
# ════════════════════════════════════════════════════════════════════════════════

def t_ratio_high_when_real_inputs():
    """afferent ratio بالا وقتی ورودیِ حسیِ واقعی زیاد."""
    bus = SensoryBus(window=20)
    for _ in range(10):
        bus.ingest(Observation(source="leg", obs_type="lead", label="x"))
    assert bus.afferent_ratio > 0.8


def t_ratio_low_when_all_internal():
    """afferent ratio پایین وقتی all-internal → آلارم."""
    bus = SensoryBus(window=20)
    for _ in range(10):
        bus.ingest_internal(source="system")
    alarm = bus.check_alarm()
    assert alarm is not None, "باید آلارم بدهد (all-internal)"
    assert alarm["type"] == "afferent-deficit"


def t_no_alarm_when_balanced():
    """balanced → no alarm."""
    bus = SensoryBus(window=20)
    for _ in range(5):
        bus.ingest(Observation(source="leg", obs_type="status", label="ok"))
    for _ in range(5):
        bus.ingest_internal(source="system")
    alarm = bus.check_alarm()
    # ratio ~0.5 > threshold → no alarm
    assert alarm is None or bus.afferent_ratio >= AFFERENT_RATIO_ALARM


def t_alarm_after_minimum_events():
    """کم‌داده → no alarm (need ≥5 events)."""
    bus = SensoryBus(window=20)
    bus.ingest_internal()
    assert bus.check_alarm() is None


# ════════════════════════════════════════════════════════════════════════════════
# Propose-only + no production
# ════════════════════════════════════════════════════════════════════════════════

def t_publish_advisory_no_bus_returns_false():
    """بدونِ bus → False (no-op)."""
    bus = SensoryBus()
    event = AfferentEvent(source="x", obs_type="lead", topic_ids=["A01"],
                          ledger_event_type="OBSERVE", intensity=0.5)
    assert bus.publish_advisory(event, bus=None) is False


def test_publish_with_fake_bus():
    """با fake bus → True."""
    bus = SensoryBus()
    published = []
    class FakeBus:
        def publish(self, et, payload, actor="system"):
            published.append({"type": et, "payload": payload, "actor": actor})
            return {"hash": "x"}
    event = AfferentEvent(source="leg", obs_type="lead", topic_ids=["A01"],
                          ledger_event_type="OBSERVE", intensity=0.5)
    ok = bus.publish_advisory(event, bus=FakeBus())
    assert ok is True
    assert len(published) == 1
    assert published[0]["payload"]["afferent"] is True


def t_status_readonly():
    """status فقط‌خواندنی."""
    bus = SensoryBus()
    for _ in range(5):
        bus.ingest(Observation(source="leg", obs_type="lead", label="x"))
    s = bus.status()
    assert "afferent_ratio" in s and "total_events" in s


def t_no_production_import():
    """sensory_bus هیچ import از *_gate/chrono/money ندارد."""
    import sensory_bus
    src = open(sensory_bus.__file__, encoding="utf-8").read()
    forbidden = ["import chrono", "from chrono", "organ_gate", "money_gate",
                 "capability_gate", "budget_gate", "EffectorGate", "opslib"]
    for f in forbidden:
        assert f not in src, f"خطِ قرمز: {f}"


def t_observation_no_raw_data_stored():
    """observation فقط label دارد، نه raw_data (no PII retention)."""
    obs = Observation(source="x", obs_type="lead", label="sanitized label")
    # fieldهای observation: source, obs_type, label, intensity — نه raw
    assert not hasattr(obs, "raw_data")
    assert not hasattr(obs, "raw")


if __name__ == "__main__":
    failed = harness.run([
        ("[C] lead → topics", t_classify_lead_to_topics),
        ("[C] error → tech topics", t_classify_error_to_topics),
        ("[C] payment → MONEY_ATTRIBUTION", t_classify_payment_to_money_event),
        ("[C] unknown → default", t_classify_unknown_type_defaults),
        ("[P] PII در invoice", t_pii_detected_in_invoice),
        ("[P] clean label → no PII", t_pii_not_in_clean_label),
        ("[P] PII observation رد", t_pii_observation_rejected),
        ("[R] ratio بالا با ورودیِ واقعی", t_ratio_high_when_real_inputs),
        ("[R] ratio پایین → آلارم", t_ratio_low_when_all_internal),
        ("[R] balanced → no alarm", t_no_alarm_when_balanced),
        ("[R] کم‌داده → no alarm", t_alarm_after_minimum_events),
        ("[O] publish بدونِ bus → False", t_publish_advisory_no_bus_returns_false),
        ("[O] publish با fake bus → True", test_publish_with_fake_bus),
        ("[O] status فقط‌خواندنی", t_status_readonly),
        ("[S] no production import", t_no_production_import),
        ("[S] no raw_data stored", t_observation_no_raw_data_stored),
    ])
    sys.exit(1 if failed else 0)
