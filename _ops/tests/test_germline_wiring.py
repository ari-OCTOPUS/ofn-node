#!/usr/bin/env python3
"""تستِ رفتاریِ فاز۱a: اتصالِ germline به organism tick.

گپ: germline.py ساخته+تست‌شده بود ولی organism.py inline آن را duplicate می‌کرد
(organism.py:205-212) و enrich_state_with_germline هرگز صدا نمی‌زد. حالا tick از
طریقِ قراردادِ wiring.enrich_state_with_germline می‌رود که germline.py را وصل می‌کند.

اثبات:
  (الف) enrich_state_with_germline فیلدهای germline_lag_h/germline_alert را در state می‌گذارد.
  (ب) CRIT-tier alert: ERROR/CRIT → opslib.alert صدا زده می‌شود (نه بی‌صدا).
  (ج) organism.py دیگر inline-duplicate ندارد (structural: enrich_state_with_germline صدا می‌زند).
  (د) fail-soft: اگر germline.py import نشد → fallback به opslib.germline_lag_hours.
$0 آفلاین.
"""
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
ENV = harness.setup("germline-wiring")

_OPS = (harness.REAL_VAULT / r"_ops")
for _p in [str(_OPS), str(_OPS / "budget")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import wiring  # noqa: E402
import germline  # noqa: E402

ORGANISM_SRC = (_OPS / "organism.py").read_text("utf-8")


# ════════════════════════════════════════════════════════════════════════════════
# (الف) enrich فیلدها را می‌گذارد
# ════════════════════════════════════════════════════════════════════════════════

def t_enrich_sets_germline_fields():
    """enrich_state_with_germline باید germline_lag_h و germline_alert را در state بگذارد."""
    state = {}
    wiring.enrich_state_with_germline(state)
    assert "germline_lag_h" in state, "germline_lag_h باید در state باشد"
    assert "germline_alert" in state, "germline_alert باید در state باشد"


def t_enrich_uses_germline_module():
    """اگر germline.lag_alarm یک آلارم برگرداند، enrich باید آن منعکس کند."""
    state = {}
    with patch.object(germline, "lag_alarm",
                      return_value={"germline_lag_h": 3.5, "germline_alert": "warn",
                                    "last_hourly": "x", "last_bundle": "y"}):
        wiring.enrich_state_with_germline(state)
    assert state["germline_lag_h"] == 3.5
    assert state["germline_alert"] == "warn"


# ════════════════════════════════════════════════════════════════════════════════
# (ب) CRIT-tier alert
# ════════════════════════════════════════════════════════════════════════════════

def t_crit_alert_fires():
    """ERROR/CRIT germline → opslib.alert صدا زده می‌شود (نه بی‌صدا)."""
    import opslib
    calls = []
    with patch.object(germline, "lag_alarm",
                      return_value={"germline_lag_h": 30.0, "germline_alert": "ERROR"}), \
         patch.object(opslib, "alert", side_effect=lambda m: calls.append(m)):
        state = {}
        wiring.enrich_state_with_germline(state)
    assert state["germline_alert"] == "ERROR"
    assert len(calls) >= 1, "CRIT-tier germline باید alert شود"
    assert "germline" in calls[0][0]


def t_ok_no_alert():
    """ok/warn germline → نباید alert شود (فقط CRIT-tier)."""
    import opslib
    calls = []
    with patch.object(germline, "lag_alarm",
                      return_value={"germline_lag_h": 1.0, "germline_alert": "ok"}), \
         patch.object(opslib, "alert", side_effect=lambda m: calls.append(m)):
        state = {}
        wiring.enrich_state_with_germline(state)
    # فقط در CRIT/ERROR alert می‌زند؛ ok نباید
    germ_alerts = [c for c in calls if any("germline_lag" in str(m) for m in c)]
    assert len(germ_alerts) == 0, "ok نباید CRIT-tier alert داشته باشد"


# ════════════════════════════════════════════════════════════════════════════════
# (ج) organism از قرارداد استفاده می‌کند (نه inline-duplicate)
# ════════════════════════════════════════════════════════════════════════════════

def t_organism_calls_enrich_state():
    """organism.py باید enrich_state_with_germline را صدا بزند (نه inline-duplicate)."""
    assert "enrich_state_with_germline" in ORGANISM_SRC, \
        "organism باید enrich_state_with_germline را صدا بزند"


def t_organism_no_inline_duplicate():
    """بلاکِ inlineِ germline_lag_hours نباید به‌تنهایی در tick باشد (duplicate حذف شد)."""
    # نباید الگوی inline کامل باشد: lag = opslib.germline_lag_hours() + if/elif germ
    # (قراردادِ enrich جایگزینش کرد)
    assert "lag = opslib.germline_lag_hours()" not in ORGANISM_SRC, \
        "بلاکِ inlineِ germline باید حذف شود — enrich_state_with_germline جایگزین"


# ════════════════════════════════════════════════════════════════════════════════
# (د) fail-soft fallback
# ════════════════════════════════════════════════════════════════════════════════

def t_fallback_when_germline_fails():
    """اگر germline.lag_alarm استثنا بیندازد → fallback به opslib."""
    import opslib
    with patch.object(germline, "lag_alarm", side_effect=RuntimeError("boom")), \
         patch.object(opslib, "germline_lag_hours", return_value=1.0):
        state = {}
        wiring.enrich_state_with_germline(state)
    # fallback باید مقدار بدهد
    assert "germline_lag_h" in state
    assert state["germline_lag_h"] == 1.0


if __name__ == "__main__":
    failed = harness.run([
        ("enrich فیلدها را می‌گذارد", t_enrich_sets_germline_fields),
        ("enrich از ماژولِ germline استفاده می‌کند", t_enrich_uses_germline_module),
        ("CRIT-tier alert", t_crit_alert_fires),
        ("ok → no alert", t_ok_no_alert),
        ("organism enrich_state_with_germline", t_organism_calls_enrich_state),
        ("organism inline-duplicate حذف شد", t_organism_no_inline_duplicate),
        ("fallback وقتی germline fail", t_fallback_when_germline_fails),
    ])
    sys.exit(1 if failed else 0)
