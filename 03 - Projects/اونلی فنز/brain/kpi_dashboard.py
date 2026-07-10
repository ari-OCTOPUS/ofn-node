#!/usr/bin/env python3
"""kpi_dashboard.py — #3: KPI Dashboard HTML. read-only، صفر PII."""
from __future__ import annotations
import html


class KPIRenderer:
    """داشبوردِ HTML سبک. از config/memory تغذیه. صفر PII."""

    def render(self, config: dict | None = None, acquisition_data: dict | None = None,
               neural_snap: dict | None = None, brain_status: dict | None = None,
               drafts_count: int = 0) -> str:
        cfg = config or {}
        acq = acquisition_data or {}
        snap = neural_snap or {}
        bs = brain_status or {}
        analytics = cfg.get("analytics", {})
        calendar = cfg.get("calendar", {})

        # funnel
        vis = acq.get("visitors", 100); subs = acq.get("subscribers", 5); ppv = acq.get("ppv_buyers", 1)
        sub_pct = subs/max(vis,1)*100; ppv_pct = ppv/max(subs,1)*100

        # tag perf bars
        tag_perf = acq.get("tag_performance", {})
        bars = ""
        for tag, score in sorted(tag_perf.items(), key=lambda x:-x[1])[:5]:
            w = int(score*100)
            bars += f'<div style="margin:4px 0"><span>{html.escape(tag)}</span>'
            bars += f'<div style="background:#e0e0e0;border-radius:4px;height:14px;width:100%">'
            bars += f'<div style="background:#4CAF50;height:14px;width:{w}%;border-radius:4px"></div>'
            bars += f'</div></div>'

        # neural
        rhythm = snap.get("rhythm",{}); pain = snap.get("pain_level",0)
        mode = rhythm.get("mode_focus","STEADY"); color = rhythm.get("mode_color","GREEN")
        pain_color = "#4CAF50" if pain < 0.4 else ("#FF9800" if pain < 0.7 else "#F44336")

        # brain
        agent_count = bs.get("agent_count",10); last_insight = bs.get("last_insight","—")

        return f"""<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8">
<title>Project-F Dashboard</title>
<style>
body{{font-family:Vazirmatn,Tahoma,Arial;background:#f5f3ee;margin:0;padding:20px}}
.card{{max-width:700px;margin:0 auto;background:#fff;border-radius:12px;padding:20px;
box-shadow:0 1px 3px rgba(0,0,0,.1)}}
h1{{font-size:18px}} h2{{font-size:15px;margin-top:20px;border-bottom:2px solid #eee;padding-bottom:5px}}
.metric{{display:inline-block;margin:10px;padding:10px 15px;background:#f0efe9;border-radius:8px;min-width:80px}}
.metric .v{{font-size:22px;font-weight:700}} .metric .l{{font-size:11px;color:#888}}
</style></head><body><div class="card">
<h1>🎬 Project-F — داشبورد</h1>
<p style="color:#888">read-only · صفر PII · paper-mode</p>

<h2>🔵 قیفِ تبدیل</h2>
<div class="metric"><div class="v">{vis}</div><div class="l">بازدید</div></div>
<div class="metric"><div class="v">{subs} ({sub_pct:.1f}%)</div><div class="l">مشترک</div></div>
<div class="metric"><div class="v">{ppv} ({ppv_pct:.1f}%)</div><div class="l">PPV</div></div>

<h2>📊 عملکردِ Tag</h2>
{bars if bars else '<p style="color:#888">هنوز داده‌ای ثبت نشده.</p>'}

<h2>⚡ وضعیتِ عصبی</h2>
<div class="metric"><div class="v" style="color:{'#4CAF50' if color=='GREEN' else '#FF9800' if color=='AMBER' else '#F44336'}">{mode}</div><div class="l">{color}</div></div>
<div class="metric"><div class="v" style="color:{pain_color}">{pain:.2f}</div><div class="l">درد</div></div>

<h2>🧠 مغز</h2>
<div class="metric"><div class="v">{agent_count}</div><div class="l">agent فعال</div></div>
<div class="metric"><div class="v">{drafts_count}</div><div class="l">درفت</div></div>
<p style="font-size:13px;color:#666">آخرین insight: {html.escape(str(last_insight))}</p>

<h2>📅 تقویم</h2>
<p style="font-size:13px">فصل: {html.escape(str(calendar.get('season','?')))}</p>

</div></body></html>"""
