#!/usr/bin/env python3
"""تستِ P4 (dedupِ هشدارِ گاورنر-LLM) + P9 (heartbeatِ مرگِ کاکپیت).

P4: PriceNotLocked/خطای ثابت فقط یک‌بار در هر session هشدار می‌دهد (نه ساعتی)؛ یک
    اجرای موفق re-arm می‌کند. رفتارِ پول/گیت دست‌نخورده.
P9: live/server.py هر خروجِ serve_forever را با live-cockpit=STOP در HEARTBEAT ثبت می‌کند.
$0 · sandbox · صفر شبکه · صفر دست‌زدن به state/پروسهٔ زنده.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("p4-p9-fixes")
_OPS = (harness.REAL_VAULT / r"_ops")
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "live"), str(_OPS / "debate")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402
import governor_epoch as G  # noqa: E402


# ── P4: dedup ────────────────────────────────────────────────────────────────
def t_alert_once_dedups():
    """یک کلید فقط یک‌بار هشدار می‌دهد؛ کلیدِ دیگر جدا هشدار می‌دهد."""
    seen = []
    _orig = opslib.alert
    opslib.alert = lambda msgs: seen.extend(msgs)
    try:
        G._GOV_LLM_ALERTED.clear()
        G._gov_llm_alert_once("gov-llm-dormant", "خفته ۱")
        G._gov_llm_alert_once("gov-llm-dormant", "خفته ۲")   # همان کلید → skip
        G._gov_llm_alert_once("gov-llm-dormant", "خفته ۳")
        assert len(seen) == 1, seen
        G._gov_llm_alert_once("gov-llm-error", "خطای دیگر")   # کلیدِ نو → هشدار
        assert len(seen) == 2, seen
    finally:
        opslib.alert = _orig
        G._GOV_LLM_ALERTED.clear()


def t_success_rearms():
    """پاک‌کردنِ set (اجرای موفق) → همان کلید دوباره یک‌بار هشدار می‌دهد."""
    seen = []
    _orig = opslib.alert
    opslib.alert = lambda msgs: seen.extend(msgs)
    try:
        G._GOV_LLM_ALERTED.clear()
        G._gov_llm_alert_once("gov-llm-dormant", "خفته")
        assert len(seen) == 1
        G._GOV_LLM_ALERTED.clear()   # الگوی «اجرای موفق re-arm می‌کند»
        G._gov_llm_alert_once("gov-llm-dormant", "خفته دوباره")
        assert len(seen) == 2, "بعد از re-arm باید دوباره هشدار دهد"
    finally:
        opslib.alert = _orig
        G._GOV_LLM_ALERTED.clear()


def t_allocate_llm_gate_closed_no_alert():
    """گیتِ بسته (flag نیست) → allocate_llm بی‌صدا None، صفر هشدار (مسیرِ امنِ عادی)."""
    seen = []
    _orig = opslib.alert
    opslib.alert = lambda msgs: seen.extend(msgs)
    try:
        G._GOV_LLM_ALERTED.clear()
        # در sandbox، ACTIVATION-GOVERNOR-LLM.flag وجود ندارد → live_gate_open=False
        out = G.allocate_llm({"month": {}}, {})
        assert out is None
        assert seen == [], f"گیتِ بسته نباید هشدار بدهد: {seen}"
    finally:
        opslib.alert = _orig
        G._GOV_LLM_ALERTED.clear()


def t_p4_source_shape():
    """source-scan: except عام دیگر مستقیم opslib.alert نمی‌زند؛ PriceNotLocked جدا گرفته شده."""
    src = (_OPS / "budget" / "governor_epoch.py").read_text("utf-8")
    assert "except PriceNotLocked as e:" in src, "PriceNotLocked باید جدا گرفته شود"
    assert "_gov_llm_alert_once(" in src and "_GOV_LLM_ALERTED" in src, "dedup غایب"
    # آلرتِ خامِ ساعتیِ قدیمی نباید بماند
    assert 'opslib.alert([f"governor llm epoch failed' not in src, "آلرتِ خامِ قدیمی مانده"


# ── P9: death heartbeat ──────────────────────────────────────────────────────
def t_p9_death_heartbeat_source():
    """live/server.py هر خروجِ serve_forever را با live-cockpit=STOP ثبت می‌کند."""
    src = (_OPS / "live" / "server.py").read_text("utf-8")
    assert "live-cockpit=STOP" in src, "heartbeatِ مرگ غایب"
    assert "srv.serve_forever()" in src
    # STOP باید در قابِ try/except/finally دورِ serve_forever باشد
    i = src.index("srv.serve_forever()")
    tail = src[i:i + 600]
    assert "finally:" in tail and "server_close" in tail, "قابِ try/finally غایب"
    assert "live-cockpit=STOP" in tail, "STOP باید دورِ serve_forever باشد"


def t_p9_server_still_imports():
    """server.py هنوز سالم import می‌شود (خرابِ سینتکسی نشده)."""
    import importlib
    srv = importlib.import_module("server")
    assert hasattr(srv, "main") and callable(srv.main)


if __name__ == "__main__":
    failed = harness.run([
        ("[P4] dedup یک‌بار در session", t_alert_once_dedups),
        ("[P4] اجرای موفق re-arm", t_success_rearms),
        ("[P4] گیتِ بسته → صفر هشدار", t_allocate_llm_gate_closed_no_alert),
        ("[P4] شکلِ source", t_p4_source_shape),
        ("[P9] heartbeatِ مرگ در source", t_p9_death_heartbeat_source),
        ("[P9] server هنوز import می‌شود", t_p9_server_still_imports),
    ])
    sys.exit(1 if failed else 0)
