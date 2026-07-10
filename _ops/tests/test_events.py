"""test_events.py — ستون‌فقراتِ رویدادِ ساختاریافته + داشبوردِ اتوماسیونِ مینیمال (جلسه ۴۶).

اسکیمای رویداد (طبقِ اسپکِ مالک)، aggregate ۵-دقیقه‌ای، Now/آخرین/گیرکرده، و ops_state سرور.
"""
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness
ENV = harness.setup("events")

import events as ev   # noqa: E402


def t_a_emit_schema_complete():
    """هر رویداد دقیقاً فیلدهای اسپک را دارد؛ approval_state صریح، نه null."""
    e = ev.emit("task.completed", "pump/web_research", summary="تحقیق انجام شد",
                duration_ms=1200, next_action="", trace_id="pump-5")
    for k in ("timestamp", "trace_id", "agent_id", "event_name", "status",
              "summary", "duration_ms", "next_action", "approval_state"):
        assert k in e, f"فیلدِ گمشده: {k}"
    assert e["approval_state"] == "unknown"      # پیش‌فرضِ صریح
    assert e["event_name"] == "task.completed" and e["duration_ms"] == 1200
    # نامِ نامعتبر → به task.completed نرمال می‌شود
    assert ev.emit("bogus.name", "x")["event_name"] == "task.completed"
    assert ev.emit("task.failed", "x", approval_state="weird")["approval_state"] == "unknown"


def t_b_summary_window_counts():
    ev.emit("task.started", "a", summary="s")
    ev.emit("task.completed", "a", summary="done")
    ev.emit("task.failed", "b", summary="oops", status="failed")
    ev.emit("task.blocked", "c", summary="stuck")
    ev.emit("approval.required", "d", approval_state="required")
    s = ev.summary_window(5)
    assert s["completed"] >= 1 and s["failed"] >= 1 and s["blocked"] >= 1
    assert s["waiting"] >= 1 and s["events"] >= 5


def t_c_now_last_attention():
    # کارِ در جریان (started بدونِ completed) → now
    ev.emit("task.started", "pump/x", summary="کارِ جاری", trace_id="tr-now")
    assert "کارِ جاری" in ev.now_line()
    # وقتی completed رسید، دیگر now نیست
    ev.emit("task.completed", "pump/x", summary="کارِ جاری تمام", trace_id="tr-now")
    lo = ev.last_outcome()
    assert lo and "تمام" in lo["summary"]
    # attention: blocked یا approval.required
    ev.emit("task.blocked", "leg/z", summary="عضو z افتاد", status="failed")
    att = ev.attention()
    assert att and ("z" in att["summary"] or att["event_name"] == "task.blocked")


def t_d_dashboard_state_shape():
    st = ev.dashboard_state(pending_count=2)
    assert st["schema"] == "dashboard-state.v1"
    for k in ("overall", "now", "last_outcome", "attention", "summary_5m", "log"):
        assert k in st
    assert isinstance(st["log"], list)
    # با pending>0 و بدونِ خطا/گیر → منتظرِ تو (اگر attention نباشد)
    assert st["overall"] in ("🟢 روان", "🟡 منتظرِ تو", "🔴 گیر")


def t_e_ops_state_server_reads_events():
    sys.path.insert(0, str(_HERE.parent / "live"))
    import server
    ev.emit("task.completed", "pump/health", summary="سلامت اوکی")
    st = server.ops_state()
    assert "overall" in st and isinstance(st.get("log"), list)


def t_f_ops_page_has_no_charts_and_is_compact():
    sys.path.insert(0, str(_HERE.parent / "live"))
    import server
    page = server.OPS_PAGE
    assert "/api/ops" in page and "setInterval(tick, 5000)" in page   # poll ۵s
    assert "الان چیکار می‌کند" in page and "آخرین نتیجه" in page
    for chart in ("<canvas", "chart.js", "svg viewBox"):    # داشبوردِ متنی، نه نمودار
        assert chart not in page.lower()


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_events: {len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
