#!/usr/bin/env python3
"""
dashboard.py — فاز ۲: داشبورد شفافیت و هزینه.

از روی logs/audit.jsonl یک صفحه‌ی HTML می‌سازد که نشان می‌دهد:
  - هر ایجنت چقدر هزینه کرده و چند بار فراخوانی شده (cost-accounting بصری)
  - خط‌زمانیِ کامل کارها (چه کسی، کِی، چه کرد)
  - وضعیت هر اجرا (نهایی شد / متوقف شد) و دلیل توقف
  - صحت زنجیره‌ی audit (دستکاری‌نشده؟)

اجرا:  python dashboard.py        → فایل dashboard.html ساخته و در مرورگر باز می‌شود.
بدون هیچ وابستگی/اینترنت کار می‌کند.
"""
from __future__ import annotations
import json, os, html, webbrowser, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "logs", "audit.jsonl")
OUT = os.path.join(HERE, "dashboard.html")

AGENT_COLOR = {
    "researcher": "#4f8cff", "analyst": "#22c55e", "supervisor": "#f59e0b",
    "orchestrator": "#a855f7", "human-gate": "#ec4899",
}


def load_records(path: str) -> list[dict]:
    recs = []
    if not os.path.exists(path):
        return recs
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                recs.append(json.loads(line))
    return recs


def verify_chain(recs: list[dict]) -> bool:
    prev = "GENESIS"
    for rec in recs:
        r = {k: rec[k] for k in rec if k != "hash"}
        if r.get("prev") != prev:
            return False
        payload = json.dumps(r, ensure_ascii=False, sort_keys=True)
        if hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16] != rec["hash"]:
            return False
        prev = rec["hash"]
    return True


def aggregate(recs: list[dict]):
    agents: dict[str, dict] = {}
    runs = []
    cur = None
    for rec in recs:
        ev, actor, data = rec["event"], rec["actor"], rec.get("data", {})
        a = agents.setdefault(actor, {"calls": 0, "cost": 0.0, "events": 0})
        a["events"] += 1
        if ev == "agent_call":
            a["calls"] += 1
            a["cost"] += float(data.get("cost_usd", 0) or 0)
        if ev == "run_start":
            cur = {"topic": data.get("topic", "?"), "mode": data.get("mode", "?"),
                   "ts": rec["ts"], "status": "در حال اجرا", "reason": "", "events": 0}
        if cur is not None:
            cur["events"] += 1
        if ev == "run_done":
            cur["status"] = "✅ نهایی شد"; runs.append(cur); cur = None
        if ev == "run_halted":
            cur["status"] = "🛑 متوقف شد"; cur["reason"] = data.get("reason", "")
            runs.append(cur); cur = None
    if cur is not None:
        runs.append(cur)
    return agents, runs


def esc(s) -> str:
    return html.escape(str(s))


def build_html(recs, agents, runs, integrity) -> str:
    total_cost = sum(a["cost"] for a in agents.values())
    total_calls = sum(a["calls"] for a in agents.values())
    max_cost = max((a["cost"] for a in agents.values()), default=0) or 1

    # کارت‌های هر ایجنت + نوار نسبت هزینه
    bars = ""
    for name, a in sorted(agents.items(), key=lambda x: -x[1]["cost"]):
        if a["calls"] == 0 and a["cost"] == 0:
            continue
        color = AGENT_COLOR.get(name, "#888")
        pct = int(a["cost"] / max_cost * 100)
        bars += f"""
        <div class="row">
          <div class="lbl"><span class="dot" style="background:{color}"></span>{esc(name)}</div>
          <div class="track"><div class="fill" style="width:{pct}%;background:{color}"></div></div>
          <div class="val">${a['cost']:.4f} · {a['calls']} فراخوانی</div>
        </div>"""

    # جدول اجراها
    run_rows = ""
    for r in runs:
        run_rows += f"""
        <tr><td>{esc(r['ts'])}</td><td>{esc(r['topic'])}</td>
        <td>{esc(r['status'])}</td><td class="muted">{esc(r['reason'])}</td></tr>"""

    # خط‌زمانی رویدادها
    timeline = ""
    for rec in recs:
        color = AGENT_COLOR.get(rec["actor"], "#888")
        d = json.dumps(rec.get("data", {}), ensure_ascii=False)
        d = d if len(d) <= 120 else d[:117] + "…"
        timeline += f"""
        <div class="tl">
          <span class="time">{esc(rec['ts'][11:])}</span>
          <span class="badge" style="background:{color}22;color:{color}">{esc(rec['actor'])}</span>
          <span class="ev">{esc(rec['event'])}</span>
          <span class="data">{esc(d)}</span>
        </div>"""

    integ = ('<span class="ok">🔐 سالم (دستکاری‌نشده)</span>' if integrity
             else '<span class="bad">⚠️ دستکاری‌شده!</span>')

    return f"""<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>داشبورد فیوژن MVP</title>
<style>
  body{{font-family:'Segoe UI',Tahoma,sans-serif;background:#0f1117;color:#e6e8ee;margin:0;padding:24px}}
  h1{{font-size:22px;margin:0 0 4px}} .sub{{color:#8b90a0;margin-bottom:20px}}
  .grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:22px}}
  .card{{background:#171a23;border:1px solid #232733;border-radius:14px;padding:16px}}
  .card .n{{font-size:26px;font-weight:700}} .card .t{{color:#8b90a0;font-size:13px}}
  .panel{{background:#171a23;border:1px solid #232733;border-radius:14px;padding:18px;margin-bottom:18px}}
  .panel h2{{font-size:15px;margin:0 0 14px;color:#c7ccda}}
  .row{{display:flex;align-items:center;gap:12px;margin:9px 0}}
  .lbl{{width:120px;font-size:14px}} .dot{{display:inline-block;width:9px;height:9px;border-radius:50%;margin-left:7px}}
  .track{{flex:1;background:#0f1117;border-radius:8px;height:14px;overflow:hidden}}
  .fill{{height:100%;border-radius:8px}} .val{{width:170px;text-align:left;font-size:13px;color:#aab}}
  table{{width:100%;border-collapse:collapse;font-size:13px}}
  td,th{{text-align:right;padding:8px 6px;border-bottom:1px solid #232733}} th{{color:#8b90a0}}
  .muted{{color:#8b90a0}}
  .tl{{display:flex;gap:10px;align-items:center;font-size:12.5px;padding:5px 0;border-bottom:1px solid #1c2029}}
  .time{{color:#6b7080;width:64px;font-variant-numeric:tabular-nums}}
  .badge{{padding:2px 8px;border-radius:6px;font-weight:600;min-width:78px;text-align:center}}
  .ev{{color:#c7ccda;width:135px}} .data{{color:#777e90;flex:1}}
  .ok{{color:#22c55e;font-weight:600}} .bad{{color:#ef4444;font-weight:600}}
</style></head><body>
  <h1>داشبورد فیوژن MVP — شفافیت و هزینه</h1>
  <div class="sub">ساخته‌شده از روی logs/audit.jsonl · صحت ممیزی: {integ}</div>

  <div class="grid">
    <div class="card"><div class="n">${total_cost:.4f}</div><div class="t">هزینه کل</div></div>
    <div class="card"><div class="n">{total_calls}</div><div class="t">کل فراخوانی مدل</div></div>
    <div class="card"><div class="n">{len(runs)}</div><div class="t">تعداد اجرا</div></div>
    <div class="card"><div class="n">{len(recs)}</div><div class="t">کل رویدادهای ثبت‌شده</div></div>
  </div>

  <div class="panel"><h2>هزینه به تفکیک ایجنت</h2>{bars or '<div class="muted">داده‌ای نیست</div>'}</div>

  <div class="panel"><h2>اجراها</h2>
    <table><tr><th>زمان</th><th>موضوع</th><th>نتیجه</th><th>دلیل توقف</th></tr>{run_rows}</table>
  </div>

  <div class="panel"><h2>خط‌زمانیِ کارها (چه کسی، کِی، چه کرد)</h2>{timeline}</div>
</body></html>"""


def main():
    recs = load_records(LOG)
    if not recs:
        print("⚠️  هیچ لاگی پیدا نشد. اول run.py را اجرا کن تا logs/audit.jsonl ساخته شود.")
        return
    integrity = verify_chain(recs)
    agents, runs = aggregate(recs)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(build_html(recs, agents, runs, integrity))
    print(f"✅ داشبورد ساخته شد: {OUT}")
    print(f"   {len(recs)} رویداد · {len(runs)} اجرا · صحت زنجیره: {'سالم' if integrity else 'دستکاری‌شده!'}")
    try:
        webbrowser.open("file://" + OUT.replace(os.sep, "/"))
    except Exception:
        pass


if __name__ == "__main__":
    main()
