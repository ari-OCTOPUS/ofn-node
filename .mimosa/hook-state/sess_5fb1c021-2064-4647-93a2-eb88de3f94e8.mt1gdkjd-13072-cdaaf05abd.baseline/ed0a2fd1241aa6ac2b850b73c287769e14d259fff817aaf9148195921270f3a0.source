"""test_release_send_separation.py — D6 (فاز D): جداسازیِ release از send (staleness واقعی).

اثبات می‌کند که:
  · release_only (در t0) فقط release می‌کند، settle نمی‌کند (ت۱).
  · settle_after_release (در t1) staleness را اعمال می‌کند (ت۲).
  · یک effect که release شده ولی بعد از window settle می‌شود → stale_refused (ت۳).
  · یک effect که در window settle می‌شود → settled (ت۴).
  · may_release deny → release_only هم deny (ت۵).
  · release_only + settle_after_release = همان release_and_settle اتمیک وقتی هم‌زمان (ت۶).

همه sandbox. flag/STOP/ACTIVATION زده نمی‌شود.
"""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "legs"))

import harness
ENV = harness.setup("release-send-sep-d6")

import importlib                          # noqa: E402
import uuid as _uuid                      # noqa: E402
import opslib                             # noqa: E402
importlib.reload(opslib)
import chrono                             # noqa: E402
importlib.reload(chrono)
import consent_firewall                   # noqa: E402
importlib.reload(consent_firewall)
import lead_effect_gate as leg            # noqa: E402
importlib.reload(leg)

_MS_PER_H = 3_600_000


def _gate():
    db = chrono.ChronoDB(str(opslib.STATE_DIR / f"chrono-d6-{_uuid.uuid4().hex[:8]}.db"))
    return chrono.EffectorGate(db), db


def _consented():
    return {"source": {"channel": "telegram_manual", "source_id": "owner", "external_id": "D6"},
            "candidate_type": "consented_inbound",
            "consent": {"basis": "explicit", "evidence": "owner_test"},
            "request": {"scope_text": "D6 test — repaint"}}


def _authz_effect(gate, lead_id="L1"):
    """یک effect بساز و authorize کن (آماده برای release)."""
    eid = gate.request("lead_outbound", lead_id, beat=1)
    leg.authorize(eid, lead_id, "owner-verdict-test")
    return eid


def t1_release_only_no_settle():
    """release_only فقط release می‌کند، settle نمی‌کند. status باید releasable، نه settled."""
    gate, _ = _gate()
    eid = _authz_effect(gate, "L1a")
    r = leg.release_only(eid, _consented(), gate=gate, now_ms=1_000_000)
    assert r["released"] is True, f"got {r}"
    assert gate.status_of(eid) == "releasable", "باید releasable باشد، نه settled"


def t2_settle_after_release_works_in_window():
    """settle_after_release در window → settled. staleness اعمال می‌شود."""
    gate, _ = _gate()
    eid = _authz_effect(gate, "L1b")
    t0 = 1_000_000
    leg.release_only(eid, _consented(), gate=gate, now_ms=t0)
    # ۱ ساعت بعد — داخلِ windowِ پیش‌فرض ۲۴h
    r = leg.settle_after_release(eid, gate=gate, now_ms=t0 + 1 * _MS_PER_H)
    assert r["settled"] is True, f"got {r}"
    assert gate.status_of(eid) == "settled"


def t3_stale_refused_beyond_window():
    """effect که بعد از window settle می‌شود → stale_refused."""
    gate, _ = _gate()
    eid = _authz_effect(gate, "L1c")
    t0 = 1_000_000
    leg.release_only(eid, _consented(), gate=gate, now_ms=t0)
    # ۴۸ ساعت بعد — بیرونِ windowِ پیش‌فرض ۲۴h
    r = leg.settle_after_release(eid, gate=gate, now_ms=t0 + 48 * _MS_PER_H)
    assert r["settled"] is False, "باید stale_refused باشد"
    assert "stale" in r["reason"], f"got {r['reason']}"
    assert gate.status_of(eid) == "releasable", "نباید settle شده باشد"


def t4_custom_window_allows():
    """max_age_hours سفارشی → می‌توان window را گستراند/تنگ کرد."""
    gate, _ = _gate()
    eid = _authz_effect(gate, "L1d")
    t0 = 1_000_000
    leg.release_only(eid, _consented(), gate=gate, now_ms=t0)
    # ۳ ساعت بعد با windowِ ۲h → stale
    r1 = leg.settle_after_release(eid, gate=gate, now_ms=t0 + 3 * _MS_PER_H, max_age_hours=2.0)
    assert r1["settled"] is False
    # effect جدید با windowِ ۱۰h → ۳ ساعت داخلِ window
    eid2 = _authz_effect(gate, "L1d2")
    leg.release_only(eid2, _consented(), gate=gate, now_ms=t0)
    r2 = leg.settle_after_release(eid2, gate=gate, now_ms=t0 + 3 * _MS_PER_H, max_age_hours=10.0)
    assert r2["settled"] is True, f"got {r2}"


def t5_may_release_deny_blocks_release_only():
    """may_release deny (مثلاً synthetic) → release_only هم deny. هیچ release."""
    gate, _ = _gate()
    eid = gate.request("lead_outbound", "L1e", beat=1)
    leg.authorize(eid, "L1e", "tok")
    syn = _consented()
    syn["source"]["channel"] = "synthetic_test"
    r = leg.release_only(eid, syn, gate=gate, now_ms=1_000_000)
    assert r["released"] is False
    assert "synthetic" in r["reason"] or "halt" in r["reason"], f"got {r['reason']}"
    assert gate.status_of(eid) == "pending"


def t6_release_then_immediate_settle_equals_atomic():
    """release_only(t0) + settle_after_release(t0) = همان release_and_settle اتمیک وقتی هم‌زمان.
    یعنی backward-compat: اگر t1==t0، staleness هیچ‌وقت fire نمی‌کند."""
    gate, _ = _gate()
    eid = _authz_effect(gate, "L1f")
    t0 = 5_000_000
    r1 = leg.release_only(eid, _consented(), gate=gate, now_ms=t0)
    r2 = leg.settle_after_release(eid, gate=gate, now_ms=t0)   # همان t0
    assert r1["released"] is True
    assert r2["settled"] is True, f"got {r2}"
    assert gate.status_of(eid) == "settled"


def t7_settle_without_release_refused():
    """settle_after_release بدونِ release_only قبلی → no_release_ts (fail-closed)."""
    gate, _ = _gate()
    eid = _authz_effect(gate, "L1g")
    # بدونِ release_only — مستقیم settle
    r = leg.settle_after_release(eid, gate=gate, now_ms=1_000_000)
    assert r["settled"] is False
    # status هنوز pending چون release_one صدا نشده
    # (authorize فقط allowlist را ست می‌کند، status را نه)
    assert "no_release_ts" in r["reason"] or "not_releasable" in r["reason"], f"got {r['reason']}"


def main():
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
    print(f"\ntest_release_send_separation: {passed}/{len(tests)}")
    if failed:
        for n, e in failed:
            print(f"  FAIL {n}: {e}")
        return 1
    return 0


if __name__ == "__main__":
    import sys as _sys
    _sys.exit(main())
