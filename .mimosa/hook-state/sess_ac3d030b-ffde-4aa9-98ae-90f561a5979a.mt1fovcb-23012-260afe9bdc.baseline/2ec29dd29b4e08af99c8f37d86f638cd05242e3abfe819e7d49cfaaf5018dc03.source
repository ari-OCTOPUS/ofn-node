"""داشبورد وبِ کوچک و فقط-خواندنی — بدون وابستگی سنگین (کتابخانهٔ استاندارد پایتون).
فقط وضعیت را نشان می‌دهد؛ کنترل (روشن/خاموش) از تلگرام انجام می‌شود.
افزودهٔ ژنوم (فاز ۱): /api/genomes + /genomes — view روی رجیستری ژنوم، هستهٔ قدیم دست‌نخورده."""
import json
import threading
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from core.models import State


def _genomes_data():
    """رجیستری ژنوم → list[dict]. lazy + fail-safe تا داشبورد هرگز به‌خاطرش نیفتد."""
    try:
        from adapters.business import genomes
        return [asdict(g) for g in genomes().values()]
    except Exception as e:  # noqa: BLE001
        return [{"error": str(e)}]


_AUTONOMY_COLOR = {"propose_only": "#2563eb", "bounded_auto": "#16a34a", "status_only": "#d97706"}


def _genomes_page() -> str:
    """صفحهٔ کارت هر ژنوم — مدرن، RTL، تک‌فایل؛ داده را از /api/genomes می‌گیرد."""
    return """<!doctype html><html lang="fa" dir="rtl"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>ژنوم‌ها — مغز دوم</title><style>
 :root{--bg:#0b1220;--card:#141e33;--line:#243049;--txt:#e6edf7;--dim:#8598b6;--accent:#7c93ff}
 *{box-sizing:border-box}
 body{font-family:Tahoma,system-ui,sans-serif;background:var(--bg);color:var(--txt);margin:0;padding:28px}
 h1{font-size:22px;margin:0 0 4px}.sub{color:var(--dim);font-size:13px;margin-bottom:22px}
 .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:16px}
 .card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:18px;position:relative}
 .card h2{font-size:17px;margin:0 0 6px;display:flex;align-items:center;gap:8px}
 .persona{color:var(--dim);font-size:13px;line-height:1.7;min-height:44px}
 .badges{display:flex;flex-wrap:wrap;gap:6px;margin:12px 0}
 .b{font-size:11px;padding:3px 9px;border-radius:999px;color:#fff}
 .b.priv{background:#7f1d1d}.b.evo{background:#3730a3}
 .bar{height:8px;background:#0b1220;border-radius:999px;overflow:hidden;margin:10px 0 4px}
 .bar>i{display:block;height:100%;background:var(--accent)}
 .row{display:flex;justify-content:space-between;font-size:12px;color:var(--dim);margin-top:8px}
 .kpi{font-size:12px;color:var(--txt);margin-top:8px}.kpi b{color:var(--dim);font-weight:400}
 a{color:var(--accent)}.foot{color:var(--dim);font-size:12px;margin-top:20px}
</style></head><body>
<h1>🧬 ژنوم‌ها</h1><div class="sub">ژنوم شخصی هر بخش، کنار ژنوم اصلیِ مشترک · view روی رجیستری (هستهٔ قدیم دست‌نخورده) · <a href="/">← وضعیت</a></div>
<div class="grid" id="g">در حال بارگذاری…</div>
<div class="foot">autonomy: آبی=propose · سبز=bounded · نارنجی=status-only. 🔒=sensitive (هرگز Fugu).</div>
<script>
fetch('/api/genomes').then(r=>r.json()).then(gs=>{
 const C={propose_only:'#2563eb',bounded_auto:'#16a34a',status_only:'#d97706'};
 document.getElementById('g').innerHTML = gs.map(g=>{
  if(g.error) return '<div class=card>خطا: '+g.error+'</div>';
  const pr = g.privacy_class==='sensitive' ? '<span class="b priv">🔒 sensitive</span>':'';
  const ev = g.evolution_optin ? '<span class="b evo">🧬 evolve</span>':'';
  const pct = Math.round((g.budget_share||0)*100);
  const kp = (g.kpis||[]).join('، ')||'—';
  const ch = (g.channels||[]).join(' · ')||'—';
  return `<div class="card">
    <h2>${g.name}</h2>
    <div class="persona">${g.persona||''}</div>
    <div class="badges"><span class="b" style="background:${C[g.autonomy]||'#555'}">${g.autonomy}</span>${pr}${ev}</div>
    <div class="bar"><i style="width:${pct}%"></i></div>
    <div class="row"><span>سهم بودجه</span><span>${pct}%</span></div>
    <div class="row"><span>کانال‌ها</span><span>${ch}</span></div>
    <div class="kpi"><b>KPI:</b> ${kp}</div>
  </div>`;
 }).join('');
}).catch(e=>{document.getElementById('g').innerHTML='خطا در دریافت: '+e});
</script></body></html>"""

_BADGE = {
    State.RUNNING: ("روشن", "#16a34a"),
    State.STOPPED: ("خاموش", "#6b7280"),
    State.UNKNOWN: ("ناشناخته", "#d97706"),
}


def _render(manager, safety) -> str:
    rows = ""
    for s in manager.status_all():
        label, color = _BADGE.get(s.state, (str(s.state), "#6b7280"))
        health = "—" if s.healthy is None else ("✅" if s.healthy else "⚠️")
        en = "بله" if s.enabled else "خیر"
        rows += (
            f"<tr><td>{s.name}</td>"
            f"<td><span style='background:{color}'>{label}</span></td>"
            f"<td>{health}</td><td>{en}</td><td>{s.pid or '—'}</td></tr>"
        )
    banner = ""
    if safety.is_halted():
        banner = "<div class='halt'>⛔ قفل ایمنی روشن است — هیچ پروژه‌ای روشن نمی‌شود.</div>"
    return f"""<!doctype html><html lang="fa" dir="rtl"><head>
<meta charset="utf-8"><meta http-equiv="refresh" content="5">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>مغز کنترل — وضعیت</title>
<style>
 body{{font-family:Tahoma,system-ui,sans-serif;background:#0f172a;color:#e2e8f0;margin:0;padding:24px}}
 h1{{font-size:20px}}
 table{{width:100%;border-collapse:collapse;margin-top:16px;background:#1e293b;border-radius:12px;overflow:hidden}}
 th,td{{padding:12px 14px;text-align:right;border-bottom:1px solid #334155}}
 th{{background:#334155;font-size:13px}}
 span{{color:#fff;padding:3px 10px;border-radius:999px;font-size:12px}}
 .halt{{background:#7f1d1d;color:#fff;padding:12px;border-radius:10px;margin-top:12px}}
 .foot{{color:#64748b;font-size:12px;margin-top:14px}}
</style></head><body>
<h1>🧠 مغز کنترل — نمای وضعیت</h1>{banner}
<table><tr><th>پروژه</th><th>وضعیت</th><th>سلامت</th><th>فعال؟</th><th>شناسه</th></tr>{rows}</table>
<div class="foot">این صفحه فقط تماشاست؛ روشن/خاموش‌کردن از تلگرام. هر ۵ ثانیه تازه می‌شود. &nbsp;·&nbsp; <a href="/genomes" style="color:#7c93ff">🧬 نمای ژنوم‌ها</a></div>
</body></html>"""


def make_handler(manager, safety):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):  # ساکت
            pass

        def _send(self, code, body, ctype):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path.startswith("/api/status"):
                data = [
                    {"id": s.id, "name": s.name, "state": s.state, "enabled": s.enabled,
                     "healthy": s.healthy, "pid": s.pid}
                    for s in manager.status_all()
                ]
                payload = {"halted": safety.is_halted(), "projects": data}
                self._send(200, json.dumps(payload, ensure_ascii=False).encode(), "application/json; charset=utf-8")
            elif self.path.startswith("/api/genomes"):
                self._send(200, json.dumps(_genomes_data(), ensure_ascii=False).encode(),
                           "application/json; charset=utf-8")
            elif self.path.startswith("/genomes"):
                self._send(200, _genomes_page().encode(), "text/html; charset=utf-8")
            elif self.path in ("/", "/index.html"):
                self._send(200, _render(manager, safety).encode(), "text/html; charset=utf-8")
            else:
                self._send(404, b"not found", "text/plain")
    return H


def start_dashboard(manager, safety, host="127.0.0.1", port=8770):
    server = ThreadingHTTPServer((host, port), make_handler(manager, safety))
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server
