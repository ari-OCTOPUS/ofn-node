#!/usr/bin/env python3
"""live/server.py — اتاقِ کنترلِ زنده (127.0.0.1:8773) — «محیطِ تعاملیِ آنلاین با همهٔ قسمت‌ها».

یک صفحهٔ RTL که هر ۴ ثانیه /api/live را poll می‌کند: بدن، قلب، پمپِ کار، مغزِ مرکزی،
سه مغز، نیازها، ایمنی — همه از state-fileها و پورت‌های زنده (فقط‌خواندنی). به‌علاوه:
چتِ زنده با مغز (router سه‌مغزی) و دو اقدامِ مالک: restartِ بدن (مکانیزمِ sanctioned:
STOP + RESTART-REQUESTED؛ بعدش RUN-ORGANISM را هم می‌زند که ضدِ دوبل است) و
راه‌اندازی/توقفِ مغز. بعداً نسخهٔ بهینه به تلگرام می‌رود (خواستِ مالک).

دکترین: جدا از organism/cortex (هیچ importی از حلقه‌هایشان) · bind فقط 127.0.0.1 ·
$0 (چت فقط از routerی که خودش paid را دوقفله می‌کند) · خروجی از پاسِ redaction.
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

_HERE = Path(__file__).resolve().parent           # _ops/live
_OPS = _HERE.parent
sys.path.insert(0, str(_OPS / "budget"))
sys.path.insert(0, str(_OPS / "cortex"))
import opslib  # noqa: E402

PORT = int(os.environ.get("LIVE_PORT", "8773"))
STATE = opslib.STATE_DIR
PORTS = {"organism": 8771, "cortex": 8772, "ollama": 11434, "dashboard": 8770}


def _read_json(p: Path):
    try:
        return json.loads(p.read_text("utf-8")) if p.exists() else None
    except (OSError, ValueError):
        return None


def _tail_jsonl(p: Path, n: int) -> list:
    try:
        if not p.exists():
            return []
        return [json.loads(x) for x in p.read_text("utf-8").splitlines()[-n:]
                if x.strip()]
    except (OSError, ValueError):
        return []


def _port_alive(port: int, probe=None) -> bool:
    if probe is not None:
        return bool(probe(port))
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.6):
            return True
    except OSError:
        return False


def _age_min(p: Path):
    try:
        return round((time.time() - p.stat().st_mtime) / 60.0, 1) if p.exists() else None
    except OSError:
        return None


def _redact(text: str) -> str:
    try:
        import cockpit_readmodel as crm
        return crm.redact(text)
    except Exception:  # noqa: BLE001
        return text


def aggregate(probe=None) -> dict:
    """کلِ تصویرِ زنده در یک JSON — همه read-only، همه fail-soft."""
    ops = opslib.OPS                      # از env (تست‌پذیر/ایزوله) — نه مسیرِ ثابت
    org = _read_json(STATE / "ORGANISM-STATE.json") or {}
    wiring = org.get("wiring") or {}
    pulse_shadow = _read_json(STATE / "pulse" / "heart-shadow-latest.json") or {}
    signals = _read_json(STATE / "pulse" / "heart-signals-latest.json") or {}
    setpoint = _read_json(STATE / "pulse" / "heart-setpoint-latest.json") or {}
    cortex_st = _read_json(STATE / "cortex" / "cortex-state.json") or {}
    tel = _read_json(STATE / "telemetry-latest.json") or {}
    rep = _read_json(STATE / "replication-latest.json") or {}
    needs = None
    try:
        import needs_digest
        needs = needs_digest.compute()
    except Exception:  # noqa: BLE001
        needs = {"items": [], "n": 0}
    alerts_today = 0
    try:
        a = opslib.ALERTS_MD
        if a.exists():
            alerts_today = a.read_text("utf-8")[-8000:].count(f"## {opslib.today()}")
    except OSError:
        pass
    new_code_live = "heart" in org or bool(pulse_shadow)
    return {
        "ts": opslib.now_iso(),
        "processes": {k: _port_alive(v, probe) for k, v in PORTS.items()},
        "flags_file": (ops / "OCTOPUS-flags.cmd").exists(),
        "new_code_live": new_code_live,
        "body": {
            "state_age_min": _age_min(STATE / "ORGANISM-STATE.json"),
            "month_aud": (org.get("month") or {}).get("aud"),
            "today_usd": (org.get("today") or {}).get("usd"),
            "suspects": org.get("suspect_zero_total"),
            "beat": (org.get("chrono") or {}).get("beat"),
            "legs": (org.get("chrono") or {}).get("legs"),
            "protective": bool(org.get("protective_skip")),
            "germline_lag_h": org.get("germline_lag_h"),
            "halted": org.get("halted"), "frozen": org.get("frozen"),
            "wiring_on": sorted(k for k, v in wiring.items()
                                if v is True and k.startswith("wire_")),
            "profile": wiring.get("profile"),
        },
        "heart": {
            "present": bool(pulse_shadow),
            "period_shadow_s": pulse_shadow.get("period_s"),
            "wire_open": (pulse_shadow.get("production_wire") or {}).get("open"),
            "wire_reasons": (pulse_shadow.get("production_wire") or {}).get("reasons"),
            "gate0": pulse_shadow.get("gate0_live_producer"),
            "velocity": (signals.get("velocity") or {}).get("velocity_per_hr"),
            "cpi": (signals.get("cpi") or {}).get("cpi_0_1"),
            "delta": (signals.get("delta_self") or {}).get("delta_self_live"),
            "band": ([setpoint.get("viable_band_lo"), setpoint.get("viable_band_hi")]
                     if setpoint else None),
        },
        "pump": {
            "plan": (_read_json(STATE / "pulse" / "work-plan.json") or {}).get("templates"),
            "state": _read_json(STATE / "pulse" / "work-state.json"),
            "log_tail": _tail_jsonl(STATE / "pulse" / "work-log.jsonl", 6),
        },
        "cortex": {
            "present": bool(cortex_st),
            "age_min": _age_min(STATE / "cortex" / "cortex-state.json"),
            "coherence": cortex_st.get("coherence"),
            "stale": cortex_st.get("stale_members"),
            "rhythm": cortex_st.get("rhythm"),
            "thought": cortex_st.get("thought"),
            "alignment": cortex_st.get("alignment"),
            "journal_tail": _tail_jsonl(STATE / "cortex" / "journal.jsonl", 6),
            "brains": cortex_st.get("brains"),
        },
        "money": {"month": tel.get("month"), "suspects": tel.get("suspect_zero_total")},
        "sigma": (rep.get("sigma") or {}),
        "needs": needs,
        "alerts_today": alerts_today,
        "stops": {"organism": opslib.STOP_ORGANISM.exists(),
                  "cortex": (ops / "STOP-CORTEX").exists(),
                  "architect": opslib.halted() or "—",
                  "freeze": opslib.frozen()},
    }


def do_action(kind: str) -> dict:
    """اقدام‌های مالک (صفحهٔ محلی = کلیکِ مالک). همه برگشت‌پذیر و sanctioned.
    مسیرها از opslib.OPS (env) — در تست، mini-vault؛ در prod، _ops واقعی."""
    ops = opslib.OPS
    if kind == "restart-organism":
        # مکانیزمِ رسمیِ داشبورد: STOP + RESTART-REQUESTED؛ بعد relaunchِ ضدِ دوبل.
        (ops / "STOP-ORGANISM").write_text("restart via live cockpit", "utf-8")
        (ops / "RESTART-REQUESTED").write_text("live", "utf-8")

        def _relauncher():
            for _ in range(80):                      # تا ~۷ دقیقه صبر برای خروجِ تمیز
                time.sleep(5)
                if not _port_alive(PORTS["organism"]):
                    break
            time.sleep(3)
            bat = ops / "RUN-ORGANISM.bat"
            if not _port_alive(PORTS["organism"]) and bat.exists():
                subprocess.Popen(["cmd", "/c", str(bat)],
                                 creationflags=0x08000010)  # DETACHED+NEW_GROUP
        threading.Thread(target=_relauncher, daemon=True).start()
        return {"ok": True, "note": "درخواستِ restart ثبت شد — تا یک tick (≤۵ دقیقه) بدن با کدِ نو برمی‌گردد"}
    if kind == "start-cortex":
        if _port_alive(PORTS["cortex"]):
            return {"ok": True, "note": "مغز از قبل زنده است"}
        stop = ops / "STOP-CORTEX"
        if stop.exists():
            stop.unlink()
        bat = ops / "RUN-CORTEX.bat"
        if not bat.exists():
            return {"ok": False, "note": "RUN-CORTEX.bat یافت نشد"}
        subprocess.Popen(["cmd", "/c", str(bat)], creationflags=0x08000010)
        return {"ok": True, "note": "مغز در حالِ بالاآمدن روی 8772"}
    if kind == "stop-cortex":
        (ops / "STOP-CORTEX").write_text("via live cockpit", "utf-8")
        return {"ok": True, "note": "مغز تا پایانِ چرخه می‌خوابد"}
    return {"ok": False, "note": "اقدامِ ناشناخته"}


def do_ask(task: str, prompt: str) -> dict:
    """چت: اول proxy به مغزِ جدا (8772)؛ نبود → مستقیم router (همان انضباط)."""
    body = json.dumps({"task": task, "prompt": prompt},
                      ensure_ascii=False).encode("utf-8")
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{PORTS['cortex']}/ask",
                                     data=body,
                                     headers={"Content-Type": "application/json"},
                                     method="POST")
        with urllib.request.urlopen(req, timeout=100) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:  # noqa: BLE001 — مغزِ جدا خاموش → مسیرِ مستقیم
        try:
            import model_router
            return model_router.ask(task, prompt)
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "reason": f"router: {type(e).__name__}"}


PAGE = """<!doctype html><html dir="rtl" lang="fa"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>🐙 اتاق کنترل زنده</title>
<style>
body{font-family:Tahoma,sans-serif;background:#111;color:#ddd;margin:0;padding:14px}
h1{font-size:18px;margin:0 0 10px} h2{font-size:14px;margin:0 0 8px;color:#8fd}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:10px}
.card{background:#1b1b1f;border:1px solid #333;border-radius:10px;padding:10px 12px}
.kv{margin:2px 0;font-size:13px} .kv b{color:#fff}
.ok{color:#6f6}.bad{color:#f66}.warn{color:#fc6}.dim{color:#888;font-size:12px}
button{background:#264;color:#fff;border:0;border-radius:8px;padding:8px 12px;margin:3px;cursor:pointer;font-family:inherit}
button.red{background:#622} textarea{width:100%;background:#222;color:#eee;border:1px solid #444;border-radius:8px;padding:8px;font-family:inherit}
pre{white-space:pre-wrap;font-size:12px;background:#222;border-radius:8px;padding:8px;direction:rtl}
.small{font-size:12px}
</style><body>
<h1>🐙 اتاق کنترل زنده <span id="ts" class="dim"></span></h1>
<div class="grid" id="grid">در حال بارگذاری…</div>
<div class="card" style="margin-top:10px"><h2>💬 گفت‌وگو با مغز (محلی $0 — بعداً fugu/glm)</h2>
<textarea id="q" rows="2" placeholder="از مجموعه بپرس… (مثلاً: الان مهم‌ترین کار چیه؟)"></textarea>
<button onclick="ask()">بپرس</button> <span id="askst" class="dim"></span>
<pre id="ans" style="display:none"></pre></div>
<script>
function esc(s){return String(s??"—").replace(/&/g,"&amp;").replace(/</g,"&lt;")}
function pill(b){return b?'<span class="ok">🟢</span>':'<span class="bad">🔴</span>'}
async function act(k,msg){ if(msg&&!confirm(msg))return;
 const r=await fetch('/api/action',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({kind:k})});
 alert((await r.json()).note); }
async function ask(){ const q=document.getElementById('q').value.trim(); if(!q)return;
 document.getElementById('askst').textContent='در حال فکر…';
 const r=await fetch('/api/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({task:'daily',prompt:q})});
 const j=await r.json(); const a=document.getElementById('ans'); a.style.display='block';
 a.textContent=j.ok?('['+(j.tier||'?')+'] '+j.text):('❌ '+(j.reason||'نشد'));
 document.getElementById('askst').textContent=j.ok?('⏱ '+(j.ms||'')+'ms'):''; }
async function tick(){ try{
 const d=await (await fetch('/api/live')).json();
 document.getElementById('ts').textContent='· '+d.ts;
 const p=d.processes, b=d.body, h=d.heart, c=d.cortex, br=(c.brains||{});
 let cards='';
 cards+=`<div class="card"><h2>⚙️ فرایندها</h2>
 <div class="kv">بدن (8771): ${pill(p.organism)} ${d.new_code_live?'<span class=ok>کدِ نو</span>':'<span class=warn>کدِ قدیم — restart لازم</span>'}</div>
 <div class="kv">مغز (8772): ${pill(p.cortex)} · ollama: ${pill(p.ollama)}</div>
 <div class="kv">flags: ${d.flags_file?'🟢 مستقر':'🔴 غایب'} · STOPها: بدن ${d.stops.organism?'🔴':'—'} مغز ${d.stops.cortex?'🔴':'—'} · freeze ${d.stops.freeze?'🔴':'—'}</div>
 <button onclick="act('restart-organism','بدن یک tick می‌خوابد و با کدِ نو (قلب/پمپ/نوتیف) برمی‌گردد. ادامه؟')">🔄 restart بدن با کدِ نو</button>
 ${p.cortex?'<button class=red onclick="act(\\'stop-cortex\\')">⏸ توقف مغز</button>':'<button onclick="act(\\'start-cortex\\')">🧠 راه‌اندازی مغز</button>'}</div>`;
 cards+=`<div class="card"><h2>🐙 بدن</h2>
 <div class="kv">state: <b>${esc(b.state_age_min)}</b> دقیقه پیش · beat: <b>${esc(b.beat)}</b> · پروفایل: ${esc(b.profile)}</div>
 <div class="kv">ماه: AU$${esc(b.month_aud)} · suspect: ${esc(b.suspects)} · germline: ${esc(b.germline_lag_h)}h</div>
 <div class="kv">پاها: ${esc(JSON.stringify(b.legs))} · protective: ${b.protective?'🔴':'—'}</div>
 <div class="dim small">${(b.wiring_on||[]).length} سیمِ روشن</div></div>`;
 cards+=`<div class="card"><h2>🫀 قلب</h2>${h.present?`
 <div class="kv">period سایه: <b>${esc(h.period_shadow_s)}s</b> · velocity: <b>${esc(h.velocity)}</b>/hr · باند: ${esc(JSON.stringify(h.band))}</div>
 <div class="kv">CPI: ${esc(h.cpi)} · Δ: ${esc(h.delta)} · Gate-0: ${h.gate0?'🟢':'⏳'}</div>
 <div class="kv">سیمِ زنده: ${h.wire_open?'🟢 باز':'🔴 بسته ('+((h.wire_reasons||[]).length)+' شرط)'}</div>`
 :'<div class="kv warn">هنوز نتپیده — بعد از restart بدن شروع می‌شود</div>'}</div>`;
 cards+=`<div class="card"><h2>🛠 پمپ کار</h2>${d.pump.plan?`
 <div class="kv">${d.pump.plan.map(t=>esc(t.kind)+(t.paid?'💰':'')).join(' · ')}</div>
 <pre>${esc((d.pump.log_tail||[]).map(l=>l.ts+' '+(l.kind||'')+' '+(l.skipped||l.idle||(l.ok?'✓':''))).join('\\n')||'هنوز کاری ثبت نشده')}</pre>`
 :'<div class="kv warn">نقشهٔ کار بعد از restart ساخته می‌شود</div>'}</div>`;
 cards+=`<div class="card"><h2>🧠 مغز مرکزی</h2>${c.present?`
 <div class="kv">coherence: <b>${esc(c.coherence)}</b> · کهنه‌ها: ${esc((c.stale||[]).join('، ')||'هیچ')}</div>
 <div class="kv">ریتم: هر ${esc((c.rhythm||{}).period_s)}s (${esc((c.rhythm||{}).source)})</div>
 <div class="kv">مرتب‌سازی: ${esc(((c.alignment||{}).changed?((c.alignment||{}).diff||[]).join('،'):(c.alignment||{}).reason))}</div>
 <div class="kv small">💭 ${esc(c.thought)}</div>
 <div class="kv small">مغزها: local <b>${esc((br.brains||br).local_model||(br.local_model))}</b> · fugu ${((br.keys||{}).fugu)?'🔑':'⚪'} · glm ${((br.keys||{}).glm)?'🔑':'⚪'}</div>`
 :'<div class="kv warn">مغز روشن نیست — دکمهٔ راه‌اندازی بالا</div>'}</div>`;
 cards+=`<div class="card"><h2>📌 نیازها + ایمنی</h2>
 <div class="kv">${(d.needs.items||[]).map((x,i)=>(i+1)+'. '+esc(x)).join('<br>')||'<span class=ok>هیچ‌چیز منتظرت نیست ✅</span>'}</div>
 <div class="kv">σ: ${esc(d.sigma.sigma_effective)} (${esc(d.sigma.zone)}) · هشدارِ امروز: ${d.alerts_today}</div></div>`;
 document.getElementById('grid').innerHTML=cards;
 }catch(e){} }
tick(); setInterval(tick, 4000);
</script></body></html>"""


class _Srv(ThreadingHTTPServer):
    allow_reuse_address = False

    def server_bind(self):
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


class _Handler(BaseHTTPRequestHandler):
    def _send(self, code, body: bytes, ctype="application/json; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802
        if self.path == "/api/live":
            out = _redact(json.dumps(aggregate(), ensure_ascii=False))
            self._send(200, out.encode("utf-8"))
            return
        if self.path == "/":
            self._send(200, PAGE.encode("utf-8"), "text/html; charset=utf-8")
            return
        self._send(404, b"{}")

    def do_POST(self):  # noqa: N802
        try:
            n = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(n).decode("utf-8")) if n else {}
            if self.path == "/api/action":
                self._send(200, json.dumps(do_action(str(body.get("kind", ""))),
                                           ensure_ascii=False).encode("utf-8"))
                return
            if self.path == "/api/ask":
                out = do_ask(str(body.get("task", "daily"))[:40],
                             str(body.get("prompt", ""))[:4000])
                self._send(200, _redact(json.dumps(out, ensure_ascii=False))
                           .encode("utf-8"))
                return
            self._send(404, b"{}")
        except Exception as e:  # noqa: BLE001
            self._send(500, json.dumps({"ok": False, "reason": str(e)},
                                       ensure_ascii=False).encode("utf-8"))

    def log_message(self, *a):
        pass


def main() -> int:
    try:
        import env_loader
        env_loader.load_env()
    except Exception:  # noqa: BLE001
        pass
    try:
        srv = _Srv(("127.0.0.1", PORT), _Handler)
    except OSError:
        print(f"live: نمونهٔ دیگری روی {PORT} زنده است — خروجِ تمیز.")
        return 0
    print(f"live: اتاقِ کنترل روی http://127.0.0.1:{PORT}")
    opslib.heartbeat(f"live-cockpit=START port={PORT}")
    srv.serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
