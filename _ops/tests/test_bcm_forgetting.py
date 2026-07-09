#!/usr/bin/env python3
"""test_bcm_forgetting.py — تستِ Blueprint Phase 3: BCM forgetting.

متریک‌های پیش‌ثبت‌شده (state/phase-metrics.jsonl → blueprint-phase-3-bcm):
  memory_decay_rate = β > 0 · memory_saturation ≤ 1.0 · no_regression (flag خاموش).
$0 آفلاین: همهٔ persistها tmpdir. هیچ لمسِ state واقعی.
"""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
import harness

import numpy as np
from neural.bcm import BCMStabilizer, BCMReport
from neural.latent_space import SharedLatentSpace
from neural.consolidation import ConsolidatedInsight


def _tmp_path(name="bcm-test.json"):
    return Path(tempfile.mkdtemp()) / name


def _make_bcm(**kw):
    kw.setdefault("persist_path", _tmp_path())
    return BCMStabilizer(**kw)


# ─── هستهٔ ریاضی BCM ────────────────────────────────────────────────────────

def t_decay_unactivated():
    """حافظهٔ فعال‌نشده باید زوالِ یکنواخت کند و در گام‌های کران‌دار هرس شود."""
    b = _make_bcm(beta=0.5, eta=0.5, w_floor=0.05)
    ws = []
    pruned_at = None
    for step in range(1, 10):
        r = b.step({}, known_keys=["m1"])
        w = b.weight("m1")
        if w is None:
            assert "m1" in r.pruned or pruned_at is not None
            pruned_at = pruned_at or step
            break
        ws.append(w)
    assert pruned_at is not None, f"باید هرس می‌شد؛ وزن‌ها: {ws}"
    # β=0.5 → w هر گام نصف: 1→0.5→0.25→0.125→0.0625→0.031<0.05 → گام ۵
    assert pruned_at == 5, f"انتظار هرس در گام ۵، شد {pruned_at}"
    # زوال یکنواخت
    assert all(ws[i] > ws[i + 1] for i in range(len(ws) - 1)), f"زوال باید یکنواخت باشد: {ws}"


def t_reinforced_persists():
    """حافظه‌ای که مرتب بازیابی می‌شود (y=0.8) باید بالای کف بماند."""
    b = _make_bcm(beta=0.05, eta=0.5, theta_alpha=0.1, w_floor=0.05)
    for _ in range(50):
        b.step({"m1": 0.8}, known_keys=["m1"])
    w = b.weight("m1")
    assert w is not None, "حافظهٔ فعال نباید هرس شود"
    assert w > 0.5, f"وزنِ حافظهٔ فعال باید معنادار بماند، شد {w}"


def t_homeostasis_no_runaway():
    """ضدِ reward-hacking حافظه: فعال‌سازیِ اشباع‌شدهٔ دائمی (y=1.0) runaway نمی‌گیرد —
    θ→1 بالا می‌رود و رشد را سرکوب می‌کند؛ w همیشه ≤ cap."""
    b = _make_bcm(beta=0.02, eta=0.5, theta_alpha=0.5, w_cap=4.0)
    peak = 0.0
    for _ in range(100):
        b.step({"m1": 1.0}, known_keys=["m1"])
        w = b.weight("m1")
        assert w is not None and w <= 4.0 + 1e-9, f"w نباید از cap بگذرد: {w}"
        peak = max(peak, w)
    theta = b.theta("m1")
    assert theta is not None and theta >= 0.95, f"θ باید به E[y²]=1 برسد، شد {theta}"
    # بعد از اشباعِ θ، φ→0 و زوال غالب می‌شود → وزنِ نهایی زیر peak
    assert b.weight("m1") < peak, "فعال‌سازیِ اشباع‌شده باید سرکوب شود (هومئوستاز)"


def t_moving_threshold_ema():
    """θ باید دقیقاً EMA(y²) باشد: θ_n = y²·(1 − (1−α)^n) برای y ثابت."""
    b = _make_bcm(theta_alpha=0.5, beta=0.01, eta=0.5)
    for _ in range(3):
        b.step({"m1": 0.6}, known_keys=["m1"])
    expected = 0.36 * (1 - 0.5 ** 3)   # 0.315
    got = b.theta("m1")
    assert got is not None and abs(got - expected) < 1e-9, f"θ={got} ≠ {expected}"


def t_prune_below_floor():
    """کلیدِ زیرِ کف باید در pruned گزارش شود و از weights حذف شود."""
    b = _make_bcm(beta=0.99, eta=0.5, w_floor=0.5)
    r = b.step({}, known_keys=["dead"])
    assert "dead" in r.pruned, f"pruned={r.pruned}"
    assert b.weight("dead") is None
    assert b.keys() == []


def t_saturation_bounded():
    """متریکِ پیش‌ثبت‌شده: memory_saturation همیشه ≤ 1.0؛ ضعیف‌ترین‌ها هرس می‌شوند."""
    b = _make_bcm(beta=0.01, eta=0.5, max_keys=10, w_floor=0.001)
    keys = [f"k{i:02d}" for i in range(15)]
    acts = {k: (i + 1) / 20.0 for i, k in enumerate(keys)}   # k00 ضعیف‌ترین
    r = b.step(acts, known_keys=keys)
    assert r.weights_count <= 10, f"count={r.weights_count} > max_keys"
    assert r.saturation <= 1.0 + 1e-9, f"saturation={r.saturation} > 1.0"
    assert len(r.pruned) == 5
    # ضعیف‌ترین‌ها (فعال‌سازی کمتر) باید حذف شده باشند
    for k in ["k00", "k01", "k02", "k03", "k04"]:
        assert k in r.pruned, f"{k} باید هرس می‌شد؛ pruned={r.pruned}"


def t_deterministic():
    """همان دنباله → همان وزن‌ها (هیچ تصادفی در BCM نیست)."""
    seq = [{"a": 0.3, "b": 0.9}, {"a": 0.0, "b": 0.7}, {"b": 1.0}]
    results = []
    for _ in range(2):
        b = _make_bcm(beta=0.05, eta=0.5, theta_alpha=0.1)
        for acts in seq:
            b.step(acts, known_keys=["a", "b"])
        results.append((b.weight("a"), b.weight("b"), b.theta("a"), b.theta("b")))
    assert results[0] == results[1], f"باید deterministic باشد: {results}"


def t_never_invents_keys():
    """BCM هرگز خودش key نمی‌سازد — فقط از known_keys (دانش gate-passed)."""
    b = _make_bcm()
    b.step({"ghost": 1.0}, known_keys=["real"])
    assert b.weight("ghost") is None, "activation برای key ناشناخته نباید وزن بسازد"
    assert b.weight("real") is not None


def t_sync_removed_keys():
    """کلیدی که از ایندکس retrieval حذف شده → از weights هم drop می‌شود."""
    b = _make_bcm(beta=0.01)
    b.step({"a": 0.5, "b": 0.5}, known_keys=["a", "b"])
    assert set(b.keys()) == {"a", "b"}
    b.step({"a": 0.5}, known_keys=["a"])   # b دیگر در ایندکس نیست
    assert b.weight("b") is None
    assert b.weight("a") is not None


def t_persist_roundtrip():
    """persist اتمیک + reload باید وزن‌ها و step را حفظ کند."""
    p = _tmp_path("roundtrip.json")
    b1 = BCMStabilizer(persist_path=p, beta=0.05, eta=0.5)
    b1.step({"m1": 0.8}, known_keys=["m1"])
    b1.step({"m1": 0.6}, known_keys=["m1"])
    w1, th1, s1 = b1.weight("m1"), b1.theta("m1"), b1.step_count
    b2 = BCMStabilizer(persist_path=p, beta=0.05, eta=0.5)
    assert b2.weight("m1") == w1
    assert b2.theta("m1") == th1
    assert b2.step_count == s1 == 2


def t_corrupt_persist_fail_soft():
    """فایل خراب → شروع تازه بدون crash (fail-soft)."""
    p = _tmp_path("corrupt.json")
    p.write_text("{not json", "utf-8")
    b = BCMStabilizer(persist_path=p)
    assert b.keys() == []
    assert b.step_count == 0


def t_env_override():
    """پارامترِ صریح بر env می‌چربد؛ env بر پیش‌فرض."""
    old = os.environ.get("OCTOPUS_BCM_BETA")
    try:
        os.environ["OCTOPUS_BCM_BETA"] = "0.33"
        assert _make_bcm().decay_rate == 0.33
        assert _make_bcm(beta=0.11).decay_rate == 0.11
        os.environ["OCTOPUS_BCM_BETA"] = "junk"
        assert _make_bcm().decay_rate == 0.02   # پیش‌فرض
    finally:
        if old is None:
            os.environ.pop("OCTOPUS_BCM_BETA", None)
        else:
            os.environ["OCTOPUS_BCM_BETA"] = old


def t_decay_rate_metric():
    """متریکِ پیش‌ثبت‌شده: memory_decay_rate = β > 0 (فراموشی کنترل‌شده، نه صفر)."""
    b = _make_bcm()
    assert b.decay_rate > 0, "β باید مثبت باشد"
    assert b.decay_rate <= 0.1, "β پیش‌فرض باید محافظه‌کارانه باشد"
    r = b.step({}, known_keys=["m1"])
    assert r.decay_rate == b.decay_rate


# ─── سیم‌کشی (wiring) ────────────────────────────────────────────────────────

def _make_stack(latent_space=None, cycle_n=1):
    cycle = MagicMock()
    cycle.run.return_value = ConsolidatedInsight(
        cycle=cycle_n, insights=["test"], verified_sources=["acquisition"],
        discarded_sources=[])
    return {"consolidation": cycle, "latent_space": latent_space}


def t_wiring_bcm_fields_set():
    """canonical_consolidation با bcm → گزارش BCM در result + هرسِ ایندکس."""
    import wiring
    ls = SharedLatentSpace(dim=32, persist_path=str(_tmp_path("ls1.json")))
    # کلیدِ کهنه که باید فراموش شود (β تهاجمی برای تست)
    stale_vec = np.zeros(32); stale_vec[0] = 1.0
    ls.embed("stale-key", stale_vec, layer="test", source="old")
    b = BCMStabilizer(persist_path=_tmp_path("w1.json"),
                      beta=0.9, eta=0.5, w_floor=0.5)
    stack = _make_stack(latent_space=ls)
    result = wiring.canonical_consolidation(
        stack, acquisition_data={"rev": 42.0}, latent_space=ls, bcm=b)
    assert result is not None
    assert result.bcm_pruned is not None, "bcm_pruned باید گزارش شود"
    assert result.bcm_theta is not None
    assert result.bcm_saturation is not None and result.bcm_saturation <= 1.0
    assert "stale-key" in result.bcm_pruned, f"کلید کهنه باید هرس می‌شد: {result.bcm_pruned}"
    assert ls.get("stale-key") is None, "کلید هرس‌شده باید از ایندکس retrieval حذف شود"
    # کلیدهای همین cycle (فعال=1.0) باید زنده بمانند
    assert ls.get("cycle-1") is not None, "حافظهٔ تازه نباید هرس شود"


def t_wiring_backward_compat():
    """bcm=None → فیلدهای bcm همه None (صفر تغییر رفتار — no_regression)."""
    import wiring
    ls = SharedLatentSpace(dim=32, persist_path=str(_tmp_path("ls2.json")))
    stack = _make_stack(latent_space=ls)
    result = wiring.canonical_consolidation(
        stack, acquisition_data={"rev": 42.0}, latent_space=ls, bcm=None)
    assert result is not None
    assert result.bcm_pruned is None
    assert result.bcm_theta is None
    assert result.bcm_saturation is None


def t_wiring_bare_no_bcm():
    """بدون source (bare, cycle=0) → BCM اصلاً اجرا نمی‌شود (قرارداد فاز ۱ حفظ)."""
    import wiring
    ls = SharedLatentSpace(dim=32, persist_path=str(_tmp_path("ls3.json")))
    b = BCMStabilizer(persist_path=_tmp_path("w3.json"))
    stack = _make_stack(latent_space=ls)
    result = wiring.canonical_consolidation(stack, latent_space=ls, bcm=b)
    assert result is not None and result.cycle == 0
    assert result.bcm_pruned is None
    assert b.step_count == 0, "cycleِ خالی نباید گامِ BCM مصرف کند"


def t_wiring_fail_soft():
    """اگر bcm.step crash کند → consolidation هنوز result معتبر برمی‌گرداند."""
    import wiring
    ls = SharedLatentSpace(dim=32, persist_path=str(_tmp_path("ls4.json")))
    broken = MagicMock()
    broken.step.side_effect = RuntimeError("boom")
    stack = _make_stack(latent_space=ls)
    result = wiring.canonical_consolidation(
        stack, acquisition_data={"rev": 42.0}, latent_space=ls, bcm=broken)
    assert result is not None
    assert isinstance(result, ConsolidatedInsight)
    assert result.bcm_pruned is None   # گزارش ست نشده ولی crash هم نه


def t_flag_gate_structural():
    """ساختاری: BCM در consolidation_beat فقط پشتِ OCTOPUS_WIRE_BCM؛ پیش‌فرض خاموش؛
    عمداً در PAPER_FULL_FLAGS نیست (فعال‌سازی = verdict انسانی)."""
    import inspect
    import wiring
    src = inspect.getsource(wiring.consolidation_beat)
    assert 'flag("OCTOPUS_WIRE_BCM")' in src, "گیتِ flag باید در consolidation_beat باشد"
    assert "OCTOPUS_WIRE_BCM" not in wiring.PAPER_FULL_FLAGS, \
        "BCM نباید بدونِ verdict مالک در profile روشن شود"
    old = os.environ.pop("OCTOPUS_WIRE_BCM", None)
    try:
        assert wiring.flag("OCTOPUS_WIRE_BCM") is False, "پیش‌فرض باید خاموش باشد"
    finally:
        if old is not None:
            os.environ["OCTOPUS_WIRE_BCM"] = old


def t_report_dataclass():
    """BCMReport فیلدهای متریک را دارد (برای persist در consolidation history)."""
    b = _make_bcm(beta=0.02)
    r = b.step({"m1": 0.5}, known_keys=["m1"])
    assert isinstance(r, BCMReport)
    assert r.step == 1
    assert r.weights_count == 1
    assert isinstance(r.pruned, list)
    assert r.decay_rate == 0.02


if __name__ == "__main__":
    failed = harness.run([
        ("زوال حافظهٔ فعال‌نشده + هرس کران‌دار", t_decay_unactivated),
        ("حافظهٔ بازیابی‌شونده می‌ماند", t_reinforced_persists),
        ("هومئوستاز — ضد runaway/reward-hacking", t_homeostasis_no_runaway),
        ("آستانهٔ متحرک θ = EMA(y²)", t_moving_threshold_ema),
        ("هرس زیر کف", t_prune_below_floor),
        ("اشباع کران‌دار ≤ 1.0", t_saturation_bounded),
        ("deterministic", t_deterministic),
        ("هرگز key اختراع نمی‌کند", t_never_invents_keys),
        ("sync با ایندکس retrieval", t_sync_removed_keys),
        ("persist roundtrip", t_persist_roundtrip),
        ("فایل خراب → fail-soft", t_corrupt_persist_fail_soft),
        ("env override", t_env_override),
        ("متریک decay_rate = β > 0", t_decay_rate_metric),
        ("wiring: گزارش BCM + هرس ایندکس", t_wiring_bcm_fields_set),
        ("wiring: backward compat (bcm=None)", t_wiring_backward_compat),
        ("wiring: bare cycle → بدون گام BCM", t_wiring_bare_no_bcm),
        ("wiring: fail-soft", t_wiring_fail_soft),
        ("ساختاری: flag گیت + پیش‌فرض خاموش", t_flag_gate_structural),
        ("BCMReport dataclass", t_report_dataclass),
    ])
    sys.exit(1 if failed else 0)
