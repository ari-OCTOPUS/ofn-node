#!/usr/bin/env python3
"""تست D3 — SHADOW, alert-only drawdown guard (enforcement owner-gated، این‌جا ساخته نشده).

اثبات:
  • MODULE (drawdown_guard، pure):
      - breach در shadow → advisory alert؛ صفر اثرِ پول/بلاک (reserve/settle صدا زده نمی‌شود)
      - بدونِ breach → هیچ alert
      - threshold از تک‌منبعِ owner-tunable (budgets.yaml global.spike_pct) خوانده می‌شود؛
        غیاب → کفِ placeholderِ مستند
      - deterministic: ورودیِ یکسان → statusِ یکسان
      - structural: صفر network/effector/money-move import روی مسیرِ alert
  • INTEGRATION (budget_gate):
      - flag OFF (پیش‌فرض) → گارد no-op؛ رفتارِ خرج byte-identical؛ هیچ فایلِ advisory
      - flag ON + breach → advisory تولید می‌شود ولی هیچ halt/بلاک (reserveِ بعدی مجاز)
      - flag ON + no breach → هیچ advisory
"""
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("drawdown-shadow")
sys.path.insert(0, os.environ["SCRIPTS_DIR"])
import budget_gate     # noqa: E402 — تنها enforcer، از scripts/ واقعی
import drawdown_guard  # noqa: E402 — ماژولِ گاردِ shadow، sibling در scripts/

FLAG = drawdown_guard.FLAG_ENFORCE   # "HH_DRAWDOWN_ENFORCE"


# ── helpers ──────────────────────────────────────────────────────────────────────
def _default_yaml() -> None:
    budget_gate.BUDGETS_YAML.write_text(harness.TEST_BUDGETS, "utf-8")   # spike_pct=25


def _reset_all() -> None:
    for p in (budget_gate.STATE, budget_gate.LOCK, budget_gate.DRAWDOWN_ADVISORY_LOG):
        try:
            Path(p).unlink()
        except OSError:
            pass
    os.environ.pop(FLAG, None)


def _breach_est_usd(c: dict) -> float:
    """کوچک‌ترین reserve (USD) که spent_today را از spike_pct عبور می‌دهد ولی
    زیرِ سقفِ روزانه می‌ماند (پس allow می‌شود)."""
    thr = c["spike_pct"] if c["spike_pct"] is not None else drawdown_guard.DEFAULT_DRAWDOWN_PCT_PLACEHOLDER
    aud_needed = c["day_aud"] * (thr / 100.0) * 1.05      # ۵٪ حاشیهٔ اطمینان
    return aud_needed / c["aud"]


# ── MODULE: pure drawdown_guard ────────────────────────────────────────────────────
def t_breach_produces_advisory_zero_money():
    """breach → advisory alert؛ و مسیرِ alert هیچ تابعِ پولی را صدا نمی‌زند."""
    caps = {"spike_pct": 25.0}
    st = drawdown_guard.evaluate(window_spend_aud=1.0, day_cap_aud=2.0, caps=caps)  # 50% ≥ 25%
    assert st["breach"] is True and st["enforced"] is False and st["mode"] == "shadow", st

    # اگر مسیرِ alert اشتباهاً به مسیرِ پول دست بزند، این stubها منفجر می‌شوند.
    calls = {"reserve": 0, "settle": 0, "release": 0}
    orig = (budget_gate.reserve, budget_gate.settle, budget_gate.release)

    def _boom(name):
        def _f(*a, **k):
            calls[name] += 1
            raise AssertionError(f"alert path called money fn: {name}")
        return _f
    budget_gate.reserve, budget_gate.settle, budget_gate.release = (
        _boom("reserve"), _boom("settle"), _boom("release"))
    try:
        seen = []
        out = drawdown_guard.observe(1.0, 2.0, caps, agent="ZIMAN",
                                     now_iso="2026-07-21T00:00:00", sink=seen.append)
    finally:
        budget_gate.reserve, budget_gate.settle, budget_gate.release = orig

    assert out["alert"] is not None, out
    assert out["alert"]["kind"] == "drawdown-advisory", out["alert"]
    assert out["alert"]["severity"] == "advisory" and out["alert"]["enforced"] is False, out["alert"]
    assert len(seen) == 1 and seen[0] is out["alert"], seen
    assert calls == {"reserve": 0, "settle": 0, "release": 0}, calls   # صفر تماسِ پولی


def t_no_breach_no_alert():
    """زیرِ threshold → هیچ alert."""
    caps = {"spike_pct": 25.0}
    st = drawdown_guard.evaluate(window_spend_aud=0.2, day_cap_aud=2.0, caps=caps)  # 10% < 25%
    assert st["breach"] is False, st
    assert drawdown_guard.build_alert(st) is None, st
    out = drawdown_guard.observe(0.2, 2.0, caps, sink=lambda a: (_ for _ in ()).throw(
        AssertionError("sink must not fire without breach")))
    assert out["alert"] is None, out


def t_threshold_single_owner_tunable_source():
    """threshold فقط از تک‌منبعِ budgets.yaml:global.spike_pct؛ غیاب → placeholderِ مستند."""
    # مقدارِ متمایز از placeholder (۲۵) تا اثباتِ «read from source» بدونِ ابهام
    thr, src = drawdown_guard.threshold_pct({"spike_pct": 17})
    assert thr == 17.0 and src == "budgets.yaml:global.spike_pct", (thr, src)
    # غیابِ کلید → کفِ placeholderِ مستند (ثابتِ نام‌دار، نه عددِ سیاستِ تصمیم‌شده)
    thr2, src2 = drawdown_guard.threshold_pct({})
    assert thr2 == drawdown_guard.DEFAULT_DRAWDOWN_PCT_PLACEHOLDER == 25.0, (thr2,)
    assert src2.startswith("placeholder-constant"), src2
    # مقدارِ خراب هم fail-soft به placeholder می‌رود
    thr3, src3 = drawdown_guard.threshold_pct({"spike_pct": "garbage"})
    assert thr3 == 25.0 and src3.startswith("placeholder-constant"), (thr3, src3)


def t_deterministic():
    """ورودیِ یکسان → statusِ یکسان (بدونِ ts/تصادف)."""
    caps = {"spike_pct": 20.0}
    a = drawdown_guard.evaluate(0.7, 2.0, caps)
    b = drawdown_guard.evaluate(0.7, 2.0, caps)
    assert a == b, (a, b)
    assert a["window_pct"] == 35.0 and a["threshold_pct"] == 20.0, a


def t_structural_zero_money_network_imports():
    """اسکنِ سورس: هیچ import شبکه/effector/money-move و هیچ call به reserve/settle/halt."""
    src = Path(drawdown_guard.__file__).read_text("utf-8")
    forbidden_import = re.compile(
        r"^\s*(?:import|from)\s+"
        r"(requests|urllib|http|httplib|socket|ssl|smtplib|ftplib|asyncio|"
        r"effector|money_gate|capability_gate|budget_gate|organ_gate|opslib)\b",
        re.M)
    m = forbidden_import.search(src)
    assert m is None, f"forbidden import: {m.group(0) if m else ''}"
    for call in (r"\.reserve\s*\(", r"\.settle\s*\(", r"\.release\s*\(",
                 r"\.halt\s*\(", r"EffectorGate", r"\.request_idempotent\s*\("):
        assert re.search(call, src) is None, f"money/effector call present: {call}"


# ── INTEGRATION: budget_gate wiring ────────────────────────────────────────────────
def t_flag_off_byte_identical_no_advisory():
    """flag OFF (پیش‌فرض): reserveِ breach-اندازه → allow؛ state دقیقاً مثلِ قبل؛ هیچ فایلِ advisory."""
    _default_yaml(); _reset_all()
    c = budget_gate._caps()
    est = _breach_est_usd(c)
    r = budget_gate.reserve("ZIMAN", est)
    assert r == {"allow": True, "reserved": est}, r          # مقدار/allow دقیقاً رفتارِ legacy
    d = budget_gate._roll(budget_gate._load())
    assert abs(d["spent_today_usd"] - est) < 1e-12, d
    assert abs(d["spent_month_aud"] - est * c["aud"]) < 1e-12, d
    assert d["halted"] is False, d
    assert not budget_gate.DRAWDOWN_ADVISORY_LOG.exists(), "flag OFF نباید فایلِ advisory بسازد"


def t_flag_on_breach_advisory_but_zero_money_effect():
    """flag ON + breach: advisory تولید می‌شود ولی هیچ halt/بلاک — reserveِ بعدی مجاز می‌ماند."""
    _default_yaml(); _reset_all()
    os.environ[FLAG] = "1"
    try:
        c = budget_gate._caps()
        r1 = budget_gate.reserve("ZIMAN", _breach_est_usd(c))
        assert r1["allow"] is True, r1                        # همان reserve مجاز است (صفر بلاک)
        assert budget_gate.DRAWDOWN_ADVISORY_LOG.exists(), "breach باید advisory بنویسد"
        lines = budget_gate.DRAWDOWN_ADVISORY_LOG.read_text("utf-8").splitlines()
        assert len(lines) >= 1, lines
        import json
        rec = json.loads(lines[0])
        assert rec["kind"] == "drawdown-advisory" and rec["enforced"] is False, rec
        assert rec["severity"] == "advisory", rec
        d = budget_gate._roll(budget_gate._load())
        assert d["halted"] is False, ("shadow نباید halt کند", d)   # صفر اثرِ پولی
        # reserveِ بعدی هم مجاز (زیرِ سقفِ روزانه) — گارد چیزی را بلاک نکرده
        r2 = budget_gate.reserve("ZIMAN", 0.01)
        assert r2["allow"] is True, r2
    finally:
        os.environ.pop(FLAG, None)


def t_flag_on_no_breach_no_advisory():
    """flag ON ولی reserveِ کوچک (زیرِ threshold) → هیچ advisory."""
    _default_yaml(); _reset_all()
    os.environ[FLAG] = "1"
    try:
        c = budget_gate._caps()
        tiny = (c["day_aud"] * 0.05) / c["aud"]              # ۵٪ سقف، خیلی زیرِ ۲۵٪
        r = budget_gate.reserve("ZIMAN", tiny)
        assert r["allow"] is True, r
        assert not budget_gate.DRAWDOWN_ADVISORY_LOG.exists(), "بدونِ breach نباید advisory باشد"
    finally:
        os.environ.pop(FLAG, None)


def t_caps_surfaces_raw_spike_pct():
    """budget_gate._caps() مقدارِ خامِ spike_pct را از SoT سطح می‌دهد (تک‌منبع)."""
    _default_yaml()
    assert budget_gate._caps()["spike_pct"] == 25.0, budget_gate._caps()
    budget_gate.BUDGETS_YAML.write_text(
        "global:\n  cap_monthly: 30\n  spike_pct: 12\nprojects: {}\n", "utf-8")
    assert budget_gate._caps()["spike_pct"] == 12.0, budget_gate._caps()
    # غیابِ کلید → None (تا drawdown_guard از placeholder استفاده کند)
    budget_gate.BUDGETS_YAML.write_text("global:\n  cap_monthly: 30\nprojects: {}\n", "utf-8")
    assert budget_gate._caps()["spike_pct"] is None, budget_gate._caps()


if __name__ == "__main__":
    failed = harness.run([
        ("MODULE: breach → advisory، صفر تماسِ پولی", t_breach_produces_advisory_zero_money),
        ("MODULE: بدونِ breach → هیچ alert", t_no_breach_no_alert),
        ("MODULE: threshold از تک‌منبعِ owner-tunable + placeholderِ مستند",
         t_threshold_single_owner_tunable_source),
        ("MODULE: deterministic", t_deterministic),
        ("MODULE: structural — صفر network/effector/money-move import",
         t_structural_zero_money_network_imports),
        ("INTEGRATION: flag OFF → byte-identical، هیچ advisory", t_flag_off_byte_identical_no_advisory),
        ("INTEGRATION: flag ON + breach → advisory ولی صفر halt/بلاک",
         t_flag_on_breach_advisory_but_zero_money_effect),
        ("INTEGRATION: flag ON + no breach → هیچ advisory", t_flag_on_no_breach_no_advisory),
        ("INTEGRATION: _caps() مقدارِ خامِ spike_pct را سطح می‌دهد", t_caps_surfaces_raw_spike_pct),
    ])
    sys.exit(1 if failed else 0)
