#!/usr/bin/env python3
"""تست T1: تلمتری واحد micro-USD + تله‌های «or 0» و واحد ارزی + FREEZE/شرط مرگ (I3)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("telemetry")
import json  # noqa: E402

import opslib     # noqa: E402
import telemetry  # noqa: E402


def _ledger():
    return opslib.genome_ledger()


def t_zero_source_gap_no_death():
    # رگرسیونِ 2026-07-23: منبعِ تلمتریِ تهی (core.dbِ یخ‌زده) نباید مرگِ متابولیسم بسازد.
    # billed>کف ولی همهٔ منابع صفر → observability-gap (نرم)، نه divergence (مرگ).
    Path(ENV["BUDGET_STATE"]).write_text(json.dumps(
        {"date": opslib.today(), "month": opslib.month(),
         "spent_today_usd": 0.02, "spent_month_aud": 0.06, "halted": False}), "utf-8")
    s = telemetry.snapshot()
    assert s["month"]["aud"] == 0.0, s["month"]          # همهٔ منابع هنوز تهی‌اند
    probs = telemetry.reconcile(s)
    assert any("observability-gap" in p for p in probs), probs
    assert not any("divergence" in p for p in probs), probs
    assert not opslib.STOP_METABOLIC.exists(), "شکافِ رصد نباید STOP-METABOLIC بسازد"
    assert not opslib.frozen(), "شکافِ رصد نباید FREEZE بسازد"
    Path(ENV["BUDGET_STATE"]).unlink()                   # پاک‌سازی برای تست‌های بعدی


def t_genome_metric_and_or0():
    lg = _ledger()
    lg.append("METRIC", {"llm_cost_usd": 0.5, "model": "m", "task": "t"}, actor="router")
    lg.append("METRIC", {"llm_cost_usd": 0, "model": "m", "task": "t"}, actor="router")   # تلهٔ or 0
    lg.append("NOTE", {"cost_usd": 9.9}, actor="research")   # نباید شمرده شود (دوباره‌شماری)
    g = telemetry.read_genome()
    assert g["events"] == 2, f"events={g['events']}"
    assert g["cost_musd"] == opslib.micro(0.5), f"musd={g['cost_musd']}"
    assert g["suspect_zero"] == 1, f"suspect={g['suspect_zero']}"


def t_brain_usage_unmapped_or0():
    # «unmappedbiz» نامِ عمداً-نگاشت‌نشده است: painting/accounting از 2026-07-18
    # (verdict budgets-proposed-diff §۵) به ORGAN_MAP اضافه شدند، پس دیگر UNMAPPED
    # نیستند — این تست باید یک business واقعاً بیرونِ نگاشت بگیرد تا مسیرِ UNMAPPED را بسنجد.
    harness.add_usage(ENV["brain"], [
        (opslib.today(), "deepseek", "ziman", 1000, 500, 0.01),
        (opslib.today(), "deepseek", "unmappedbiz", 100, 50, 0.0),    # or-0 با توکن > 0
        (opslib.today(), "deepseek", "unmappedbiz", 100, 50, None),   # NULL هم همان تله
    ])
    b = telemetry.read_brain()
    assert b["rows"] == 3
    assert b["cost_musd"] == opslib.micro(0.01)
    assert b["suspect_zero"] == 2, f"suspect={b['suspect_zero']}"
    assert b["by_organ"].get("ZIMAN") == opslib.micro(0.01)
    assert any(k.startswith("UNMAPPED:unmappedbiz") for k in b["unmapped"]), b["unmapped"]


def t_snapshot_units():
    s = telemetry.snapshot()
    # 0.5 (ژنوم) + 0.01 (مغز) = 0.51 USD این ماه؛ AUD با نرخ پین 1.5
    assert s["month"]["usd"] == 0.51, s["month"]
    assert abs(s["month"]["aud"] - 0.765) < 1e-9, s["month"]
    assert s["suspect_zero_total"] == 3
    assert (opslib.STATE_DIR / "telemetry-latest.json").exists()


def t_reconcile_healthy():
    s = telemetry.snapshot()
    probs = telemetry.reconcile(s)
    assert probs == [], probs
    assert not opslib.frozen()


def t_reconcile_cap_breach_freezes():
    harness.add_usage(ENV["brain"], [(opslib.today(), "fugu", "ziman", 9, 9, 100.0)])
    s = telemetry.snapshot()
    probs = telemetry.reconcile(s)
    assert probs and "cap_monthly" in probs[0], probs
    assert opslib.frozen(), "FREEZE.flag باید ساخته می‌شد (I3)"
    q = (Path(ENV["ORG_ROOT"]) / "00 - Inbox" / "AGENT_QUESTIONS.md").read_text("utf-8")
    assert "CONFLICT-METABOLIC" in q, "سوال [CONFLICT] باید به صف انسان می‌رفت"
    opslib.FREEZE_FLAG.unlink()


def t_divergence_death():
    # billed (budget-state) = 10 AUD ولی تلمتری ~150+ AUD → واگرایی > 20٪ → شرط مرگ
    Path(ENV["BUDGET_STATE"]).write_text(json.dumps(
        {"date": opslib.today(), "month": opslib.month(),
         "spent_today_usd": 1.0, "spent_month_aud": 10.0, "halted": False}), "utf-8")
    s = telemetry.snapshot()
    probs = telemetry.reconcile(s)
    assert any("divergence" in p for p in probs), probs
    assert opslib.STOP_METABOLIC.exists(), "شرط مرگ: STOP-METABOLIC باید ساخته می‌شد"


def t_germline_lag_vital():
    # verdict 2026-07-07 #4: کهنگی germline — غایب=None (ERROR بالادست)، >26h=ERROR، تازه=سالم
    import os as _os
    import tempfile
    import time as _t
    ob = Path(tempfile.mkdtemp(prefix="offbox-"))
    assert opslib.germline_lag_hours(ob) is None
    m = ob / "last_backup_manifest.json"
    m.write_text("{}", "utf-8")
    old = _t.time() - 30 * 3600
    _os.utime(m, (old, old))
    lag = opslib.germline_lag_hours(ob)
    assert lag is not None and lag > opslib.GERMLINE_ERR_H, lag
    (ob / "hourly-latest.bundle").write_text("x", "utf-8")
    lag2 = opslib.germline_lag_hours(ob)
    assert lag2 is not None and lag2 < 0.1, lag2   # تازه‌ترین مصنوع می‌بَرد


if __name__ == "__main__":
    failed = harness.run([
        ("شکافِ رصد (منبعِ تهی) → soft، نه مرگ", t_zero_source_gap_no_death),
        ("ژنوم: METRIC + تله or0", t_genome_metric_and_or0),
        ("مغز: usage + UNMAPPED + NULL", t_brain_usage_unmapped_or0),
        ("واحدها: micro-USD و نرخ پین AUD", t_snapshot_units),
        ("تطبیق سالم", t_reconcile_healthy),
        ("عبور از سقف → FREEZE + CONFLICT", t_reconcile_cap_breach_freezes),
        ("واگرایی billed↔telemetry → STOP-METABOLIC", t_divergence_death),
        ("germline_lag: غایب=None · کهنه>26h=ERROR · تازه=سالم", t_germline_lag_vital),
    ])
    sys.exit(1 if failed else 0)
