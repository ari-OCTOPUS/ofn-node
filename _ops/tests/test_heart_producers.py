"""test_heart_producers.py — HH-P1: سه سنجهٔ زندهٔ Gate-0.

fail-soft (منبعِ غایب)، شمارشِ درست با fixture در mini-vault، Δ_selfِ زنده روی
سری‌ای که دسترسیِ خصوصی واقعاً کمک می‌کند در برابرِ سریِ i.i.d، و گاردهای ساختاری.
ترتیبِ چک‌ها با پیشوندِ حرفی pin شده (state مشترکِ mini-vault).
"""
import json
import random
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness
ENV = harness.setup("heart-producers")

import importlib                     # noqa: E402
import heart.producers as producers  # noqa: E402
importlib.reload(producers)          # مسیرها بعد از setup env دوباره bind شوند
import opslib                        # noqa: E402


def _write_ledger(recs):
    p = Path(ENV["GENOME_DIR"]) / "ledger" / "ledger.jsonl"
    with open(p, "a", encoding="utf-8") as fh:
        for r in recs:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")


def t_a_fail_soft_all_absent():
    """هیچ منبعی → authoritative=False و Δ بدونِ استریم None؛ هرگز exception.
    (اول اجرا می‌شود — vault هنوز خالی است.)"""
    v = producers.velocity_meter()
    assert v["authoritative"] is False
    assert v["components"]["consolidation"] is None
    assert v["components"]["beats"] is None
    c = producers.internal_cpi()
    assert c["authoritative"] is False
    d = producers.delta_self_estimator()
    assert d["delta_self_live"] is None
    assert d["authoritative"] is False
    assert d["reason"] == "insufficient-stream"


def t_b_velocity_counts_confirmed_and_effects():
    """رویدادهای مصنوعیِ CONFIRMED + EFFECT_SETTLED در پنجره شمارش شوند (ledger تمیز)."""
    now = opslib.now_iso()
    _write_ledger([
        {"type": "MONEY_ATTRIBUTION", "ts": now,
         "payload": {"state": "CONFIRMED", "amount_aud": 50}},
        {"type": "MONEY_ATTRIBUTION", "ts": now,
         "payload": {"state": "ATTRIBUTED", "amount_aud": 50}},
        {"type": "MONEY_ATTRIBUTION", "ts": "2020-01-01T00:00:00",
         "payload": {"state": "CONFIRMED", "amount_aud": 5}},   # خارجِ پنجره
        {"type": "MONEY_ATTRIBUTION", "ts": now,
         "payload": {"state": "CLAIMED", "amount_aud": 5}},     # CONFIRMED نیست
        {"type": "NOTE", "ts": now, "payload": {"subtype": "EFFECT_SETTLED",
                                                "effect_id": "e1"}},
        {"type": "NOTE", "ts": now, "payload": {"subtype": "OTHER"}},
    ])
    v = producers.velocity_meter(window_hours=24)
    assert v["components"]["confirmed"] == 2, v["components"]
    assert v["components"]["effects"] == 1
    assert v["velocity_per_hr"] is not None and v["velocity_per_hr"] > 0
    assert "confirmed" in v["sources_available"]


def t_c_velocity_counts_consolidation():
    """فایلِ consolidation آرایه‌ای با timestamp اخیر → شمرده شود."""
    import time
    cons = Path(ENV["OPS_DIR"]) / "neural"
    cons.mkdir(parents=True, exist_ok=True)
    data = [{"cycle": i, "timestamp": time.time() - 60 * i} for i in range(5)]
    (cons / "consolidation.json").write_text(json.dumps(data), "utf-8")
    v = producers.velocity_meter(window_hours=24)
    assert v["components"]["consolidation"] == 5


def t_d_cpi_computes_with_enough_events():
    """CPI با رویدادِ کافی محاسبه و authoritative شود؛ مقدار در [0,1]."""
    now = opslib.now_iso()
    _write_ledger([{"type": "MONEY_ATTRIBUTION", "ts": now,
                    "payload": {"state": "CONFIRMED", "amount_aud": a}}
                   for a in (10, 200, 15, 300, 12, 250)])
    c = producers.internal_cpi()
    assert c["authoritative"] is True
    assert c["cpi_0_1"] is not None and 0.0 <= c["cpi_0_1"] <= 1.0
    assert "attribution_noise" in c["components"]


def t_e_delta_self_positive_when_private_state_helps():
    """سری با حالتِ پنهانِ خصوصی (سایهٔ نویزی، کوواریت=دسترسیِ اول‌شخص) → Δ>0.05."""
    rng = random.Random(42)
    rows, hidden = [], 0.0
    for _ in range(60):                          # burn-in تا stationarity
        hidden = 0.95 * hidden + rng.gauss(0, 0.312)
    for t in range(400):
        hidden = 0.95 * hidden + rng.gauss(0, 0.312)
        v = hidden + rng.gauss(0, 0.707)         # سایهٔ پرنویز — blind کم می‌بیند
        rows.append({"v": v, "cov": {"confirmed": hidden,   # سیگنالِ برون‌زادِ آگاه
                                     "effects": 0, "hour": t % 24}})
    d = producers.delta_self_estimator(min_samples=48, rows=rows)
    assert d["authoritative"] is True
    assert d["delta_self_live"] > 0.05, d
    assert d["ceiling_live"] >= d["delta_self_live"]   # کرانِ سازگاری، ساختاری


def t_f_delta_self_near_zero_on_iid():
    """سریِ i.i.d بدونِ ساختار → Δ نزدیکِ صفر (کفِ صفرِ clamp)."""
    rng = random.Random(7)
    rows = [{"v": rng.gauss(0, 1), "cov": {"confirmed": rng.gauss(0, 1),
                                           "effects": 0, "hour": t % 24}}
            for t in range(240)]
    d = producers.delta_self_estimator(min_samples=48, rows=rows)
    assert d["delta_self_live"] is not None
    assert d["delta_self_live"] < 0.05, d


def t_g_stream_append_and_compute_all():
    """append به استریم + compute_all → state-file اتمیک + gate0 صادقانه بسته +
    ساعتِ ثابتِ نمونه‌گیری (decision-frequency invariance)."""
    assert producers.should_sample() is True     # استریمِ خالی → نمونهٔ اول مجاز
    ok1 = producers.append_velocity_sample({"v": 1.0, "cov": {"confirmed": 0,
                                                              "effects": 0, "hour": 1}})
    assert ok1 is True
    # بلافاصله دوباره (شبیهِ ضربانِ تندتر): باید رد شود — نمونه به ساعت گره است نه ضربان
    ok2 = producers.append_velocity_sample({"v": 2.0, "cov": {"confirmed": 0,
                                                              "effects": 0, "hour": 1}})
    assert ok2 is False
    assert producers.should_sample() is False
    for t in range(9):                            # برای compute_all با force (تست)
        producers.append_velocity_sample({"v": 1.0 + 0.1 * t,
                                          "cov": {"confirmed": 0, "effects": 0,
                                                  "hour": t % 24}}, force=True)
    assert producers.STREAM_PATH.exists()
    out = producers.compute_all(write=True)
    assert producers.SIGNALS_PATH.exists()
    on_disk = producers.read_signals()
    assert on_disk["schema"] == "heart-signals.v1"
    assert out["gate0_live_producer"] is False   # ۱۰ نمونه < ۴۸ → Gate-0 بسته


def t_h_structural_no_money_imports_no_foreign_writes():
    """ساختاری: هیچ importِ گیتِ پول؛ هیچ نوشتنی جز استریم/state خودش."""
    src = Path(producers.__file__).read_text("utf-8")
    for bad in ("import organ_gate", "import money_gate", "import budget_gate",
                "from organ_gate", "from money_gate", "import reconcile",
                "import attribution"):
        assert bad not in src, f"import ممنوع: {bad}"
    assert src.count("append_jsonl(") == 1       # تنها append: استریمِ خودش
    assert "LockedJson(SIGNALS_PATH)" in src     # تنها state: فایلِ خودش
    assert "ledger_note(" not in src             # producer هرگز به ledger نمی‌نویسد
    assert "mode=ro" in src                      # chrono.db فقط read-only URI


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_heart_producers: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
