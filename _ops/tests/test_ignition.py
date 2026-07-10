"""test_ignition.py — GNWT ignition + re-entry (جلسه ۴۶، رأی مالک ۲۰۲۶-۰۷-۱۱).

winner-take-all واقعی؟ آستانهٔ آتش‌گیری؟ بازوروِد برنده را تقویت و بعد فرسایش می‌دهد؟
متریک‌ها (rate/stability/broadcast_width) درست؟ persist بدونِ فلگ no-op است؟
"""
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "cortex"))

import harness
ENV = harness.setup("ignition")

import ignition as ig   # noqa: E402
import opslib           # noqa: E402


def _cands():
    return [
        {"source": "money", "kind": "stress", "salience": 0.72, "summary": "spend"},
        {"source": "heart", "kind": "stress", "salience": 0.30, "summary": "sigma"},
        {"source": "innervation", "kind": "dead_spot", "salience": 0.80, "summary": "cortex dead"},
    ]


def t_a_winner_take_all():
    """دقیقاً یک برنده = بالاترین effective salience."""
    sel = ig.select_winner(_cands(), reentry_prior={}, threshold=0.5)
    assert sel["ignited"] is True
    assert sel["winner"]["source"] == "innervation"      # 0.80 بالاترین
    assert sel["winner"]["key"] == "innervation:dead_spot"


def t_b_ignition_threshold_quiet_cycle():
    """اگر برندهٔ effective زیرِ آستانه باشد → چرخهٔ خاموش، بدونِ برنده."""
    low = [{"source": "a", "kind": "stress", "salience": 0.20},
           {"source": "b", "kind": "stress", "salience": 0.10}]
    sel = ig.select_winner(low, reentry_prior={}, threshold=0.5)
    assert sel["ignited"] is False and sel["winner"] is None
    assert sel["margin"] > 0                               # فاصله تا آستانه


def t_c_reentry_boosts_prev_winner():
    """بازورود: برندهٔ قبلی در چرخهٔ بعد با boost برنده می‌شود حتی اگر پایه‌اش کمی کمتر باشد."""
    # دو نامزدِ نزدیک؛ پایهٔ B کمی بالاتر، ولی A priorِ بازورود دارد
    cands = [{"source": "A", "kind": "x", "salience": 0.55},
             {"source": "B", "kind": "x", "salience": 0.60}]
    rp = {"A:x": 0.15}                                     # A چرخهٔ قبل برنده بود
    sel = ig.select_winner(cands, reentry_prior=rp, threshold=0.5)
    assert sel["winner"]["source"] == "A"                 # 0.55+0.15=0.70 > 0.60
    assert sel["winner"]["reentry_boost"] == 0.15


def t_d_reentry_decays_not_locked():
    """prior رو-به-فرسایش است تا یک برنده تا ابد قفل نشود."""
    rp = {"A:x": 0.40}
    # چند چرخه بدونِ اینکه A دوباره ببرد → باید محو شود (decay 0.6 → ~۸ چرخه تا زیرِ آستانهٔ prune)
    for _ in range(10):
        rp = ig.next_reentry(rp, winner_key="B:x")
    assert rp.get("A:x", 0.0) == 0.0                      # فرسایش تا صفر
    assert rp["B:x"] > 0                                   # B اکنون priorِ فعال دارد


def t_e_reentry_capped():
    """boostِ بازورود از سقف نمی‌گذرد (رقابت بی‌معنی نشود)."""
    rp = {}
    for _ in range(20):
        rp = ig.next_reentry(rp, winner_key="A:x")
    assert rp["A:x"] <= ig.REENTRY_CAP + 1e-9


def t_f_metrics_rate_and_stability():
    """ignition_rate رولینگ؛ stability = چند چرخهٔ پیاپیِ برندهٔ یکسان."""
    prev = {}
    r1 = ig.step(prev, candidates=_cands())               # ignite → innervation
    assert r1["ignited"] and r1["stability"] == 1
    r2 = ig.step(r1, candidates=_cands())                 # همان برنده دوباره
    assert r2["stability"] == 2                            # پایداری بالا رفت
    assert 0.0 < r2["ignition_rate"] <= 1.0
    assert r2["broadcast_width"] >= 1


def t_g_persist_flag_gated_noop():
    """propose-only: بدونِ CORTEX_IGNITION هیچ فایلی نوشته نمی‌شود و رفتار عوض نمی‌شود."""
    os.environ.pop("CORTEX_IGNITION", None)
    out = ig.persist()
    assert out == {"enabled": False}
    assert not ig.LATEST.exists()


def t_h_persist_on_writes_and_broadcasts():
    """با فلگ: فایل نوشته می‌شود و آتش‌گیریِ برندهٔ نو یک رویدادِ پخش emit می‌کند."""
    import events
    os.environ["CORTEX_IGNITION"] = "1"
    # stress-latest بساز تا نامزد داشته باشیم
    p = opslib.STATE_DIR / "cortex" / "stress-latest.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"subsystems": {
        "money": {"name": "money", "stress": 0.9},
        "heart": {"name": "heart", "stress": 0.2}}}), "utf-8")
    rec = ig.persist()
    assert rec.get("ignited") is True and ig.LATEST.exists()
    assert any(e.get("agent_id") == "ignition" for e in events.recent(50))
    os.environ.pop("CORTEX_IGNITION", None)


def t_i_content_free():
    """بی‌محتوا: خروجی فقط source/kind/salience دارد، هیچ secret/محتوای خصوصی."""
    rec = ig.step({}, candidates=_cands())
    blob = json.dumps(rec, ensure_ascii=False)
    assert "wallet" not in blob and "seed" not in blob and "key" in blob  # key = ساختاری، نه secret


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_ignition: {len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
