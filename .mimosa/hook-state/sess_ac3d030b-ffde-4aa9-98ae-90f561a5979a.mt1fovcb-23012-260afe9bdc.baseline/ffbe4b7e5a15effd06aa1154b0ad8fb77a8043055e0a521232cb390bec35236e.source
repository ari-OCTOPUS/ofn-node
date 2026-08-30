"""داشبورد وبِ کوچک و فقط-خواندنی — بدون وابستگی سنگین (کتابخانهٔ استاندارد پایتون).
فقط وضعیت را نشان می‌دهد؛ کنترل (روشن/خاموش) از تلگرام انجام می‌شود.

G10: افزون بر وضعیتِ پروژه‌ها، پنل‌های فقط-خواندنیِ حاکمیت را نشان می‌دهد —
proposalهای در انتظار، تصمیم‌های اخیر، صحتِ دفترِ evt.v1، حالتِ shadow، و خلاصهٔ
کاتالوگ. همهٔ متنِ پویا با html.escape امن می‌شود (جلوگیری از تزریقِ HTML/XSS).
"""
import html
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from core.models import State

_BADGE = {
    State.RUNNING: ("روشن", "#16a34a"),
    State.STOPPED: ("خاموش", "#6b7280"),
    State.UNKNOWN: ("ناشناخته", "#d97706"),
}
_RISK_COLOR = {"GREEN": "#16a34a", "YELLOW": "#ca8a04",
               "ORANGE": "#ea580c", "RED": "#dc2626"}


def _esc(v) -> str:
    """هر مقدارِ پویا قبل از تزریق در HTML امن می‌شود."""
    return html.escape("" if v is None else str(v), quote=True)


def _find_catalog(start=None):
    here = Path(start).resolve() if start else Path(__file__).resolve()
    for base in [here, *here.parents]:
        cand = base / "03-Offering" / "ziman-catalog.json"
        if cand.exists():
            return cand
    return None


def _catalog_counts(path):
    """شمارشِ خانواده‌ها از فایلِ کاتالوگ (فقط-خواندنی؛ بدونِ import بین-بسته‌ای)."""
    if not path:
        return None
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except Exception:  # noqa: BLE001
        return None
    counts = {}
    for rec in raw.get("products", []) or []:
        fam = str(rec.get("family", "OTHER")).split("_")[0]
        counts[fam] = counts.get(fam, 0) + 1
    return {"total": sum(counts.values()), "by_family": counts}


def _projects_rows(manager) -> str:
    rows = ""
    for s in manager.status_all():
        label, color = _BADGE.get(s.state, (str(s.state), "#6b7280"))
        health = "—" if s.healthy is None else ("✅" if s.healthy else "⚠️")
        en = "بله" if s.enabled else "خیر"
        rows += (
            f"<tr><td>{_esc(s.name)}</td>"
            f"<td><span style='background:{color}'>{_esc(label)}</span></td>"
            f"<td>{health}</td><td>{en}</td><td>{_esc(s.pid or '—')}</td></tr>"
        )
    return rows


def _governance_section(store) -> str:
    if store is None:
        return ""
    try:
        pending = store.list_proposals(status="pending")
        integrity = store.verify_ledger()
        shadow_on = store.get_flag("ziman_shadow", "on") != "off"
        tail = store.ledger_tail(8)
    except Exception:  # noqa: BLE001 — داشبورد نباید به‌خاطرِ دیتابیس بشکند
        return ""

    shadow_badge = ("🕶️ SHADOW — فقط پیشنهاد (propose-only)" if shadow_on
                    else "🔓 shadow خاموش")
    integ_badge = ("✅ دفتر سالم" if integrity.get("ok")
                   else f"⛔ شکستِ زنجیره در seq={_esc(integrity.get('broken_at'))}")

    prows = ""
    for p in pending:
        rc = _RISK_COLOR.get(str(p.get("risk")), "#6b7280")
        prows += (
            f"<tr><td><code>{_esc(p.get('ref') or p.get('proposal_id'))}</code></td>"
            f"<td><span style='background:{rc}'>{_esc(p.get('risk'))}</span></td>"
            f"<td>{_esc(p.get('kind'))}</td>"
            f"<td>{_esc((p.get('detail') or '')[:80])}</td>"
            f"<td>{_esc(p.get('proposed_by'))}</td></tr>"
        )
    if not prows:
        prows = "<tr><td colspan='5' class='muted'>هیچ proposalِ در انتظار.</td></tr>"

    drows = ""
    for e in tail:
        # فقط تصمیم‌های واقعی (decide:approve|reject|defer) — نه decide_denied
        if not str(e.get("kind", "")).startswith("decide:"):
            continue
        drows += (
            f"<tr><td><code>{_esc(e.get('decision_id') or '—')}</code></td>"
            f"<td>{_esc(e.get('kind'))}</td>"
            f"<td>{_esc((e.get('detail') or '')[:80])}</td>"
            f"<td>{_esc(e.get('actor'))}</td></tr>"
        )
    if not drows:
        drows = "<tr><td colspan='4' class='muted'>هنوز تصمیمی ثبت نشده.</td></tr>"

    return f"""
<h2>⚖️ حاکمیت</h2>
<div class="chips"><span class="chip">{_esc(shadow_badge)}</span>
<span class="chip">{_esc(integ_badge)}</span>
<span class="chip">در انتظار: {len(pending)}</span></div>
<h3>Proposalهای در انتظار</h3>
<table><tr><th>شناسه</th><th>ریسک</th><th>نوع</th><th>شرح</th><th>پیشنهاددهنده</th></tr>{prows}</table>
<h3>تصمیم‌های اخیر</h3>
<table><tr><th>ZIM-DEC</th><th>نوع</th><th>شرح</th><th>تصمیم‌گیرنده</th></tr>{drows}</table>"""


def _catalog_section(catalog_path) -> str:
    counts = _catalog_counts(catalog_path)
    if not counts:
        return ""
    fam = counts["by_family"]
    chips = "".join(
        f"<span class='chip'>{_esc(k)}: {_esc(v)}</span>"
        for k, v in sorted(fam.items()))
    return f"""
<h2>🎁 کاتالوگ</h2>
<div class="chips"><span class="chip">کل: {_esc(counts['total'])}</span>{chips}
<span class="chip">قیمت‌گذاری‌شده: 0 (propose-only تا ZIM-V5)</span></div>"""


def _render(manager, safety, store=None, catalog_path=None) -> str:
    rows = _projects_rows(manager)
    banner = ""
    if safety.is_halted():
        banner = "<div class='halt'>⛔ قفل ایمنی روشن است — هیچ پروژه‌ای روشن نمی‌شود.</div>"
    gov = _governance_section(store)
    cat = _catalog_section(catalog_path)
    return f"""<!doctype html><html lang="fa" dir="rtl"><head>
<meta charset="utf-8"><meta http-equiv="refresh" content="5">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>مغز کنترل — وضعیت</title>
<style>
 body{{font-family:Tahoma,system-ui,sans-serif;background:#0f172a;color:#e2e8f0;margin:0;padding:24px}}
 h1{{font-size:20px}} h2{{font-size:17px;margin-top:26px}} h3{{font-size:14px;color:#94a3b8}}
 table{{width:100%;border-collapse:collapse;margin-top:10px;background:#1e293b;border-radius:12px;overflow:hidden}}
 th,td{{padding:10px 12px;text-align:right;border-bottom:1px solid #334155;font-size:13px}}
 th{{background:#334155;font-size:12px}}
 span.chip,td span{{color:#fff;padding:3px 10px;border-radius:999px;font-size:12px}}
 .chips{{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}}
 .chip{{background:#334155}}
 code{{background:#0b1220;color:#93c5fd;padding:1px 6px;border-radius:6px;font-size:12px}}
 .muted{{color:#64748b}} .halt{{background:#7f1d1d;color:#fff;padding:12px;border-radius:10px;margin-top:12px}}
 .foot{{color:#64748b;font-size:12px;margin-top:18px}}
</style></head><body>
<h1>🧠 مغز کنترل — نمای وضعیت</h1>{banner}
<table><tr><th>پروژه</th><th>وضعیت</th><th>سلامت</th><th>فعال؟</th><th>شناسه</th></tr>{rows}</table>
{cat}{gov}
<div class="foot">این صفحه فقط تماشاست؛ روشن/خاموش‌کردن و تأیید از تلگرام. هر ۵ ثانیه تازه می‌شود.</div>
</body></html>"""


def make_handler(manager, safety, store=None, catalog_path=None):
    if catalog_path is None:
        catalog_path = _find_catalog()

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
                if store is not None:
                    try:
                        payload["shadow_on"] = store.get_flag("ziman_shadow", "on") != "off"
                        payload["pending_proposals"] = len(store.list_proposals(status="pending"))
                        payload["ledger_ok"] = store.verify_ledger().get("ok")
                    except Exception:  # noqa: BLE001
                        pass
                self._send(200, json.dumps(payload, ensure_ascii=False).encode(), "application/json; charset=utf-8")
            elif self.path in ("/", "/index.html"):
                body = _render(manager, safety, store, catalog_path).encode()
                self._send(200, body, "text/html; charset=utf-8")
            else:
                self._send(404, b"not found", "text/plain")
    return H


def start_dashboard(manager, safety, store=None, host="127.0.0.1", port=8770,
                    catalog_path=None):
    server = ThreadingHTTPServer(
        (host, port), make_handler(manager, safety, store, catalog_path))
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server
