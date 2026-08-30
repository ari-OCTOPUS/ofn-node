"""
brain/workspace.py — دینامیکِ «فضای کاری جهانی» (Global Workspace) از روی traceها.

پیاده‌سازیِ عملیِ لایه‌ی «دینامیکِ آگاهی» از دستورکار: به‌جای ادعای آگاهی، متغیرهای
قابل‌اندازه‌گیریِ سبکِ GNWT را از جریانِ رویداد محاسبه می‌کنیم:

  • ignition        — چند ماژول/ایجنت با یک trace فعال شدند (ورود به workspace)
  • broadcast_width — در پنجره‌ی اخیر چند نوع ایجنت فعال بودند (پهنای انتشار)
  • coherence       — کسرِ رویدادهای موفق (انسجامِ رفتاری)
  • ignition_rate   — نرخِ رویدادهای «پرشعله» (چند-ماژولی)

این‌ها فرضیه‌های دستورکار را آزمون‌پذیر می‌کنند (مثلاً همبستگیِ ignition با کشف).
"""
from __future__ import annotations

from brain import events


def workspace_metrics(window: int = 80) -> dict:
    """متغیرهای دینامیکِ فضای کاری را از رویدادهای اخیر محاسبه می‌کند."""
    rows = events.get_recent(window)
    if not rows:
        return {"mean_ignition": 0.0, "max_ignition": 0, "broadcast_width": 0,
                "coherence": 0.0, "ignition_rate": 0.0, "n": 0}

    # ignition per trace = تعداد ایجنت‌های متمایز که یک trace را «شعله‌ور» کردند
    traces: dict[str, set] = {}
    for r in rows:
        tid = r.get("trace_id") or f"_{r.get('id')}"
        traces.setdefault(tid, set()).add(r.get("agent_id", "?"))
    ignitions = [len(a) for a in traces.values()]
    mean_ign = sum(ignitions) / max(len(ignitions), 1)
    max_ign = max(ignitions) if ignitions else 0
    # «پرشعله» = traceای که ≥۲ ماژول را درگیر کرد (به workspace رسید)
    ignited = sum(1 for x in ignitions if x >= 2)
    ignition_rate = ignited / max(len(ignitions), 1)

    broadcast_width = len({r.get("agent_id") for r in rows})
    ok = sum(1 for r in rows if r.get("status") == "ok")
    coherence = ok / max(len(rows), 1)

    return {
        "mean_ignition": round(mean_ign, 2),
        "max_ignition": max_ign,
        "broadcast_width": broadcast_width,
        "coherence": round(coherence, 2),
        "ignition_rate": round(ignition_rate, 2),
        "n": len(rows),
    }


if __name__ == "__main__":
    print(workspace_metrics())
