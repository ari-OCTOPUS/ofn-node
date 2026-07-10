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
    upgrades = _read_json(STATE / "cortex" / "upgrades-digest.json") or {}
    research_st = _read_json(STATE / "pulse" / "research-latest.json") or {}
    selfmodel_st = _read_json(STATE / "cortex" / "self-model.json") or {}
    synth_st = _read_json(STATE / "cortex" / "synthesis-latest.json") or {}
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
            "members": cortex_st.get("members"),
            "stale": cortex_st.get("stale_members"),
            "rhythm": cortex_st.get("rhythm"),
            "thought": cortex_st.get("thought"),
            "alignment": cortex_st.get("alignment"),
            "journal_tail": _tail_jsonl(STATE / "cortex" / "journal.jsonl", 6),
            "brains": cortex_st.get("brains"),
        },
        "upgrades": {
            "maturity_pct": upgrades.get("maturity_pct"),
            "n": upgrades.get("n_proposals"),
            "categories": {k: len(v) for k, v in (upgrades.get("by_category") or {}).items()},
            "top": [{"title": t.get("title"), "priority": t.get("priority"),
                     "action": t.get("suggested_action"), "level": t.get("change_level")}
                    for t in (upgrades.get("top") or [])[:5]],
            "auto_enabled": upgrades.get("auto_enabled"),
            "brain_note": upgrades.get("brain_note"),
        },
        # جلسه ۴۶ — لایهٔ فراشناختی: تحقیقِ وبِ $0 + نقشهٔ خود + سنتزِ مغز
        "research": {
            "present": bool(research_st),
            "age_min": _age_min(STATE / "pulse" / "research-latest.json"),
            "n_topics": research_st.get("n_topics"),
            "topics": [{"topic": f.get("topic"), "n": f.get("n"),
                        "sample": ((f.get("hits") or [{}])[0].get("title") or "")[:70]}
                       for f in (research_st.get("findings") or [])[:4]],
        },
        "self_model": {
            "present": bool(selfmodel_st),
            "n_modules": selfmodel_st.get("n_modules"),
            "total_lines": selfmodel_st.get("total_lines"),
            "awareness_pct": selfmodel_st.get("self_awareness_pct"),
            "n_wire_flags": selfmodel_st.get("n_wire_flags"),
        },
        "synthesis": {
            "present": bool(synth_st),
            "age_min": _age_min(STATE / "cortex" / "synthesis-latest.json"),
            "tier": synth_st.get("tier"),
            "cost_usd": synth_st.get("cost_usd"),
            "proposals": [{"title": p.get("title"), "step": p.get("first_step")}
                          for p in (synth_st.get("proposals") or [])[:3]],
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


def ops_state() -> dict:
    """state داشبوردِ اتوماسیونِ مینیمال — رویدادها + شمارِ تصمیم‌های منتظر."""
    try:
        sys.path.insert(0, str(_OPS))
        import events
        pending = 0
        try:
            needs = _read_json(STATE / "needs-nudge.json") or {}
            pending = int(needs.get("last_n", 0) or 0)
        except Exception:  # noqa: BLE001
            pending = 0
        st = events.dashboard_state(pending_count=pending)
        try:
            import part_loops
            st["parts"] = part_loops.summary().get("parts", [])
        except Exception:  # noqa: BLE001
            st["parts"] = []
        return st
    except Exception as e:  # noqa: BLE001
        return {"overall": "—", "error": f"{type(e).__name__}", "log": [], "parts": []}


# ── داشبوردِ اتوماسیونِ مینیمال (رأی مالک): وضعیت + Now/آخرین/گیرکرده + خلاصهٔ ۵min + لاگ ──
OPS_PAGE = """<!doctype html><html dir="rtl" lang="fa"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>اختاپوس — کنترل</title>
<style>
*{box-sizing:border-box;margin:0}body{background:#0d1117;color:#c9d1d9;font:13px/1.5 -apple-system,Segoe UI,Roboto,sans-serif;padding:10px;max-width:640px;margin:0 auto}
.bar{display:flex;justify-content:space-between;align-items:center;background:#161b22;border:1px solid #30363d;border-radius:10px;padding:10px 12px;position:sticky;top:0}
.bar b{font-size:16px}.upd{color:#6e7681;font-size:11px}
.btn{background:#21262d;border:1px solid #30363d;color:#c9d1d9;border-radius:7px;padding:6px 12px;cursor:pointer;font:inherit}
.btn:active{background:#30363d}
.cards{display:grid;grid-template-columns:1fr;gap:8px;margin:10px 0}
.card{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:10px 12px}
.card .lbl{color:#6e7681;font-size:11px;margin-bottom:2px}.card .val{font-size:14px}
.att{border-color:#9e6a03}.att .lbl{color:#e3b341}
.kpis{display:flex;gap:6px;flex-wrap:wrap;margin:8px 0}
.kpi{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:6px 10px;flex:1;text-align:center;min-width:70px}
.kpi b{display:block;font-size:18px}.kpi span{font-size:10px;color:#6e7681}
.log{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:8px;max-height:46vh;overflow:auto}
.ev{display:flex;gap:8px;padding:4px 2px;border-bottom:1px solid #21262d;font-size:12px}
.ev .tm{color:#6e7681;font-variant-numeric:tabular-nums}.ev .nm{font-size:10px;padding:1px 5px;border-radius:5px;background:#21262d}
.ok{color:#3fb950}.fail{color:#f85149}.blk{color:#e3b341}
</style><body>
<div class="bar"><div><b id="ov">…</b><div class="upd" id="upd">—</div></div>
 <button class="btn" id="act" onclick="act()">🔄</button></div>
<div class="cards">
 <div class="card"><div class="lbl">الان چیکار می‌کند</div><div class="val" id="now">…</div></div>
 <div class="card"><div class="lbl">آخرین نتیجه</div><div class="val" id="last">…</div></div>
 <div class="card att" id="attc" style="display:none"><div class="lbl">⚠ منتظرِ تو / گیرکرده</div><div class="val" id="att"></div></div>
</div>
<div class="card" style="margin-bottom:10px"><div class="lbl">بخش‌ها (هرکدام لوپِ خودش را دارد)</div><div id="parts" style="display:flex;flex-wrap:wrap;gap:6px;margin-top:4px"></div></div>
<div class="kpis">
 <div class="kpi"><b id="k_c">0</b><span>تمام‌شده</span></div>
 <div class="kpi"><b id="k_w">0</b><span>منتظر</span></div>
 <div class="kpi"><b id="k_f">0</b><span>خطا</span></div>
 <div class="kpi"><b id="k_e">0</b><span>رویداد (۵m)</span></div>
</div>
<div class="log" id="log"></div>
<script>
function esc(s){return String(s==null?'':s).replace(/[<>&]/g,c=>({'<':'&lt;','>':'&gt;','&':'&amp;'}[c]))}
async function act(){if(!confirm('ری‌استارتِ بدن؟ یک لحظه می‌خوابد و تازه برمی‌گردد.'))return;
 const r=await fetch('/api/action',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({kind:'restart-organism'})});
 try{alert((await r.json()).note)}catch(e){}}
const NM={'task.started':'▶ شروع','task.completed':'✓ تمام','task.failed':'✗ خطا','task.blocked':'⏸ گیر','system.heartbeat':'💓 ضربان','approval.required':'🙋 تأیید','handoff.created':'🤝 تحویل'};
async function tick(){try{
 const d=await(await fetch('/api/ops')).json();
 document.getElementById('ov').textContent=d.overall||'—';
 document.getElementById('upd').textContent='آخرین به‌روزرسانی: '+new Date().toLocaleTimeString('fa-IR');
 document.getElementById('now').textContent=d.now||'—';
 document.getElementById('last').textContent=(d.last_outcome||'—')+(d.last_status==='failed'?' ✗':'');
 const att=d.attention||''; const ac=document.getElementById('attc');
 ac.style.display=att?'block':'none';
 document.getElementById('att').textContent=att+(d.attention_next?(' — '+d.attention_next):'');
 document.getElementById('parts').innerHTML=(d.parts||[]).map(p=>
  '<span style="background:#161b22;border:1px solid #30363d;border-radius:7px;padding:4px 8px;font-size:11px">'
  +esc(p.status)+' '+esc(p.name)+' <span style=color:#6e7681>'+esc(p.detail||'')+'</span></span>').join('')
  ||'<span style=color:#6e7681;font-size:11px>لوپ‌ها هنوز نچرخیده‌اند</span>';
 const s=d.summary_5m||{};
 document.getElementById('k_c').textContent=s.completed||0;
 document.getElementById('k_w').textContent=(s.waiting||d.pending||0);
 document.getElementById('k_f').textContent=s.failed||0;
 document.getElementById('k_e').textContent=s.events||0;
 const lg=document.getElementById('log');
 lg.innerHTML=(d.log||[]).map(e=>{const cl=e.status==='failed'?'fail':(e.event_name==='task.blocked'?'blk':'ok');
  return '<div class=ev><span class=tm>'+esc(e.t)+'</span><span class=nm>'+esc(NM[e.name]||e.name)+'</span><span class="'+cl+'">'+esc(e.summary||e.agent)+'</span></div>'}).join('')
  ||'<div style=color:#6e7681;padding:8px>هنوز رویدادی نیست — به‌زودی.</div>';
}catch(e){document.getElementById('ov').textContent='قطع'}}
tick(); setInterval(tick, 5000);
</script></body></html>"""


PAGE = """<!doctype html><html dir="rtl" lang="fa"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>🐙 هولوگرامِ اختاپوس</title>
<style>
:root{--beat:2.4s;--glow:#4de8ff;--warm:#ffb84d;--bad:#ff5d5d}
body{font-family:Tahoma,sans-serif;background:radial-gradient(ellipse at 50% 42%,#0c1622 0%,#070a10 62%,#04060a 100%);color:#cfe8f5;margin:0;min-height:100vh;overflow-x:hidden}
#chips{display:flex;gap:10px;justify-content:center;padding:14px 8px 0;flex-wrap:wrap}
.chip{background:rgba(20,40,60,.55);border:1px solid rgba(77,232,255,.35);border-radius:999px;padding:7px 16px;font-size:14px;backdrop-filter:blur(4px);cursor:default}
.chip b{color:#fff;font-size:16px}
#stage{display:block;margin:0 auto;max-width:720px;width:100%}
.orbit{fill:none;stroke:rgba(77,232,255,.14);stroke-width:1;stroke-dasharray:3 7}
.spin{transform-origin:350px 250px;animation:spin 70s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
#heartG{transform-origin:350px 250px;animation:pulse var(--beat) ease-in-out infinite}
@keyframes pulse{0%,100%{transform:scale(1)}18%{transform:scale(1.14)}30%{transform:scale(1.02)}42%{transform:scale(1.1)}}
.ray{stroke-width:1.2}
.node{cursor:pointer}
.node circle{stroke-width:1.4}
.nl{font-size:12px;fill:#bfe6f2;text-anchor:middle}
.ok{fill:rgba(45,120,110,.75);stroke:#39e6c0;filter:drop-shadow(0 0 7px rgba(57,230,192,.8))}
.warn{fill:rgba(120,90,30,.75);stroke:var(--warm);filter:drop-shadow(0 0 7px rgba(255,184,77,.8))}
.bad{fill:rgba(110,35,35,.78);stroke:var(--bad);filter:drop-shadow(0 0 8px rgba(255,93,93,.85))}
.off{fill:rgba(60,70,80,.4);stroke:#5a6a75;stroke-dasharray:3 3}
#thought{max-width:640px;margin:2px auto;text-align:center;font-size:13px;color:#9fd8ea;min-height:20px;padding:0 12px}
#panel{position:fixed;inset:auto 12px 96px 12px;max-width:420px;margin:0 auto;background:rgba(10,22,32,.94);border:1px solid rgba(77,232,255,.4);border-radius:14px;padding:12px 14px;font-size:13px;display:none;backdrop-filter:blur(6px);box-shadow:0 0 24px rgba(77,232,255,.25)}
#bar{position:fixed;bottom:0;left:0;right:0;display:flex;gap:8px;padding:10px;background:rgba(6,10,16,.9);backdrop-filter:blur(8px);border-top:1px solid rgba(77,232,255,.25)}
#q{flex:1;background:rgba(20,36,50,.8);color:#eaf7ff;border:1px solid rgba(77,232,255,.35);border-radius:10px;padding:10px;font-family:inherit;font-size:14px}
button{background:linear-gradient(180deg,#155a66,#0d3a44);color:#dffaff;border:1px solid rgba(77,232,255,.4);border-radius:10px;padding:9px 14px;cursor:pointer;font-family:inherit;font-size:13px}
.dim{color:#6f93a3;font-size:11px;text-align:center;padding:4px 0 84px}
</style><body>
<div id="chips">
 <span class="chip">💗 <b id="cPeriod">—</b><span style="font-size:11px"> ضربان</span></span>
 <span class="chip">🧠 هم‌آهنگی <b id="cCoh">—</b></span>
 <span class="chip" id="cNeedsChip" style="cursor:pointer" onclick="showNeeds()">📌 <b id="cNeeds">—</b> نیاز</span>
 <span class="chip" style="cursor:pointer" onclick="showUpgrades()">🧬 بلوغ <b id="cMat">—</b></span>
 <span class="chip" style="cursor:pointer" onclick="showResearch()">🌐 تحقیق <b id="cRes">—</b></span>
 <span class="chip" style="cursor:pointer" onclick="showMind()">🪞 خود <b id="cSelf">—</b></span>
</div>
<svg id="stage" viewBox="0 0 700 500" xmlns="http://www.w3.org/2000/svg">
 <circle class="orbit" cx="350" cy="250" r="120"/>
 <circle class="orbit spin" cx="350" cy="250" r="168"/>
 <circle class="orbit" cx="350" cy="250" r="210"/>
 <g id="rays"></g>
 <circle id="cohRing" cx="350" cy="250" r="74" fill="none" stroke="#39e6c0" stroke-width="3"
   stroke-linecap="round" stroke-dasharray="465" stroke-dashoffset="465"
   transform="rotate(-90 350 250)" style="filter:drop-shadow(0 0 8px rgba(57,230,192,.7));transition:stroke-dashoffset 1.2s"/>
 <g id="heartG">
   <circle cx="350" cy="250" r="56" fill="rgba(210,50,90,.28)" stroke="#ff5d8f" stroke-width="2"
     style="filter:drop-shadow(0 0 18px rgba(255,93,143,.85))"/>
   <text x="350" y="243" text-anchor="middle" style="font-size:30px">🫀</text>
   <text id="heartTxt" x="350" y="272" class="nl" style="font-size:13px;fill:#ffd7e4">—</text>
 </g>
 <g id="nodes"></g>
</svg>
<div id="thought">…</div>
<div class="dim" id="mode">—</div>
<div id="panel" onclick="this.style.display='none'"></div>
<div id="bar">
 <input id="q" placeholder="از مغز بپرس…" onkeydown="if(event.key==='Enter')ask()">
 <button onclick="ask()">💬</button>
 <button id="actBtn" onclick="mainAct()">⚡</button>
</div>
<script>
const LABELS={organism:'بدن',heart:'قلب',producers:'سنجه‌ها',work_pump:'پمپ کار',
 doctor_setpoint:'دکتر',governor:'گاورنر',sigma:'ایمنی',fitness:'برازندگی',
 school:'مدرسه',reconcile:'پول'};
const IDS=Object.keys(LABELS); let LIVE=null;
function esc(s){return String(s??'—').replace(/&/g,'&amp;').replace(/</g,'&lt;')}
function nodePos(i){const a=-Math.PI/2+i*(2*Math.PI/IDS.length);
 return [350+168*Math.cos(a),250+168*Math.sin(a)]}
function build(){let n='',r='';IDS.forEach((id,i)=>{const[x,y]=nodePos(i);
 r+=`<line class="ray" id="ray-${id}" x1="350" y1="250" x2="${x}" y2="${y}" stroke="rgba(77,232,255,.15)"/>`;
 n+=`<g class="node" id="nd-${id}" onclick="info('${id}')">
     <circle cx="${x}" cy="${y}" r="24" class="off"/>
     <text x="${x}" y="${y+4}" class="nl" style="font-size:15px">·</text>
     <text x="${x}" y="${y+42}" class="nl">${LABELS[id]}</text></g>`});
 document.getElementById('rays').innerHTML=r;
 document.getElementById('nodes').innerHTML=n}
function cls(a,present){if(!present)return'off';if(a>=0.7)return'ok';if(a>=0.35)return'warn';return'bad'}
function icon(c){return c==='ok'?'●':c==='warn'?'◐':c==='bad'?'▲':'·'}
function info(id){const m=((LIVE?.cortex?.members)||[]).find(x=>x.id===id)||{};
 const p=document.getElementById('panel');
 p.innerHTML=`<b>${LABELS[id]}</b><br>${esc(m.note||'مغز هنوز جارو نکرده')}`+
  (m.age_s!=null?`<br><span style="color:#7fb">تازگی: ${Math.round(m.age_s/60)} دقیقه پیش</span>`:'')+
  extra(id); p.style.display='block'}
function extra(id){const d=LIVE||{};const h=d.heart||{};
 if(id==='heart')return h.present?`<br>ضربان سایه: ${h.period_shadow_s}s · شتاب‌سنج Δ: ${h.delta??'—'}<br>سیمِ زنده: ${h.wire_open?'باز 🟢':'بسته 🔴 ('+((h.wire_reasons||[]).length)+' شرط)'}`:'<br>هنوز نتپیده';
 if(id==='work_pump'){const l=((d.pump||{}).log_tail||[]).slice(-2).map(x=>(x.kind||'')+' '+(x.ok?'✓':(x.skipped?'⏭':'·'))).join(' · ');return l?'<br>'+esc(l):''}
 if(id==='sigma')return `<br>σ=${esc((d.sigma||{}).sigma_effective)} (${esc((d.sigma||{}).zone)})`;
 if(id==='reconcile')return (d.needs?.items||[]).some(x=>x.includes('CSV'))?'<br>منتظرِ CSV بانکی 💵':'';
 return ''}
function showNeeds(){const p=document.getElementById('panel');
 const items=(LIVE?.needs?.items)||[];
 p.innerHTML='<b>📌 الان</b><br>'+(items.length?items.map((x,i)=>(i+1)+'. '+esc(x)).join('<br>'):'هیچ‌چیز منتظرت نیست ✅');
 p.style.display='block'}
function showUpgrades(){const p=document.getElementById('panel');const u=LIVE?.upgrades||{};
 if(u.n==null){p.innerHTML='<b>🧬 خودارتقا</b><br>حلقه هنوز نچرخیده (هر ۱۰ چرخهٔ مغز).';p.style.display='block';return}
 const cats=Object.entries(u.categories||{}).map(([k,v])=>esc(k)+':'+v).join(' · ');
 const tops=(u.top||[]).map(t=>'• <b>'+esc(t.priority)+'</b> '+esc(t.title)+' <span style=color:#6f93a3>['+esc(t.level)+']</span><br><span style=color:#9fd8ea;font-size:12px>↳ '+esc(t.action)+'</span>').join('<br>');
 p.innerHTML='<b>🧬 خودارتقا — بلوغ '+esc(u.maturity_pct)+'%</b><br>'+esc(u.n)+' پیشنهاد · auto '+(u.auto_enabled?'🟢':'⚪ خاموش')+'<br><span style=color:#6f93a3>'+cats+'</span><br><br>'+tops+(u.brain_note?'<br><br>💭 '+esc(u.brain_note):'')+'<br><br><span style=color:#6f93a3>propose-only · هر تغییرِ جدی از تو می‌پرسد</span>';
 p.style.display='block'}
function showResearch(){const p=document.getElementById('panel');const r=LIVE?.research||{};
 if(!r.present){p.innerHTML='<b>🌐 تحقیقِ وب</b><br>هنوز نچرخیده — پمپِ کار هر ~۱۲h روی گپِ مدرسه سرچِ رایگان ($0) می‌زند.';p.style.display='block';return}
 const rows=(r.topics||[]).map(t=>'• <b>'+esc(t.topic)+'</b> ('+esc(t.n)+')'+(t.sample?'<br><span style=color:#9fd8ea;font-size:12px>↳ '+esc(t.sample)+'</span>':'')).join('<br>');
 p.innerHTML='<b>🌐 تحقیقِ وبِ رایگان — '+esc(r.n_topics)+' موضوع</b> <span style=color:#6f93a3>('+esc(r.age_min==null?'—':Math.round(r.age_min)+' دقیقه پیش')+' · $0 · DDG+Wiki+arXiv)</span><br><br>'+rows;
 p.style.display='block'}
function showMind(){const p=document.getElementById('panel');const m=LIVE?.self_model||{};const s=LIVE?.synthesis||{};
 let html='<b>🪞 خودمدلی</b><br>';
 html+=m.present?('بدن: <b>'+esc(m.n_modules)+'</b> ماژول · <b>'+esc(m.total_lines)+'</b> خط · خودآگاهیِ سند <b>'+esc(m.awareness_pct)+'%</b> · '+esc(m.n_wire_flags)+' پرچم<br>'):'نقشهٔ خود هنوز ساخته نشده.<br>';
 if(s.present){html+='<br><b>🔮 سنتزِ مغز</b> <span style=color:#6f93a3>['+esc(s.tier||'—')+' · $'+esc(s.cost_usd??0)+']</span><br>';
  html+=(s.proposals||[]).map(x=>'• '+esc(x.title)+(x.step?'<br><span style=color:#9fd8ea;font-size:12px>↳ '+esc(x.step)+'</span>':'')).join('<br>')||'<span style=color:#6f93a3>(پیشنهادی پارس نشد)</span>'}
 else{html+='<br><span style=color:#6f93a3>🔮 سنتزِ مغز هنوز نچرخیده (لِینِ llm_learn پمپ).</span>'}
 p.innerHTML=html;p.style.display='block'}
async function mainAct(){const c=LIVE?.processes?.cortex;
 const k=c?'restart-organism':'start-cortex';
 const msg=c?'بدن یک tick می‌خوابد و تازه برمی‌گردد. ادامه؟':null;
 if(msg&&!confirm(msg))return;
 const r=await fetch('/api/action',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({kind:k})});
 alert((await r.json()).note)}
async function ask(){const q=document.getElementById('q');const t=q.value.trim();if(!t)return;
 q.value='';const p=document.getElementById('panel');p.innerHTML='💭 در حال فکر…';p.style.display='block';
 const r=await fetch('/api/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({task:'daily',prompt:t})});
 const j=await r.json();
 p.innerHTML=j.ok?('<b>['+(j.tier||'مغز')+']</b><br>'+esc(j.text)):('❌ '+esc(j.reason))}
async function tick(){try{
 const d=await (await fetch('/api/live')).json(); LIVE=d;
 const h=d.heart||{}, c=d.cortex||{};
 const per=h.period_shadow_s;
 document.getElementById('cPeriod').textContent=per?Math.round(per)+'s':'—';
 document.getElementById('heartTxt').textContent=per?Math.round(per)+'s':'خواب';
 document.documentElement.style.setProperty('--beat',(per?Math.max(1,Math.min(6,per/60)):3)+'s');
 const coh=c.coherence; document.getElementById('cCoh').textContent=coh!=null?Math.round(coh*100)+'%':'—';
 document.getElementById('cohRing').style.strokeDashoffset=coh!=null?String(465*(1-coh)):'465';
 document.getElementById('cNeeds').textContent=(d.needs||{}).n??'—';
 document.getElementById('cMat').textContent=(d.upgrades?.maturity_pct!=null)?(d.upgrades.maturity_pct+'%'):'—';
 document.getElementById('cRes').textContent=(d.research?.n_topics!=null)?d.research.n_topics:'—';
 document.getElementById('cSelf').textContent=(d.self_model?.n_modules!=null)?d.self_model.n_modules:'—';
 const th=c.thought||''; document.getElementById('thought').textContent=th?('💭 '+th.slice(0,160)):'';
 document.getElementById('mode').textContent=(d.new_code_live?'کدِ نو':'کدِ قدیم')+
  ' · بدن '+(d.processes.organism?'🟢':'🔴')+' · مغز '+(d.processes.cortex?'🟢':'🔴')+
  ' · ollama '+(d.processes.ollama?'🟢':'🔴')+(h.wire_open?' · سیمِ زنده باز':'');
 document.getElementById('actBtn').textContent=d.processes.cortex?'🔄':'🧠';
 const members={}; (c.members||[]).forEach(m=>members[m.id]=m);
 IDS.forEach(id=>{const m=members[id];const cl=cls(m?m.awareness:0,!!(m&&m.present));
  const g=document.getElementById('nd-'+id); if(!g)return;
  const circ=g.querySelector('circle'); circ.setAttribute('class',cl);
  g.querySelectorAll('text')[0].textContent=icon(cl);
  const ray=document.getElementById('ray-'+id);
  ray.setAttribute('stroke',`rgba(77,232,255,${m?Math.max(0.08,m.awareness*0.55):0.06})`)});
}catch(e){}}
build(); tick(); setInterval(tick, 4000);
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
        if self.path == "/api/ops":
            self._send(200, _redact(json.dumps(ops_state(), ensure_ascii=False)).encode("utf-8"))
            return
        if self.path in ("/ops", "/ops/"):
            self._send(200, OPS_PAGE.encode("utf-8"), "text/html; charset=utf-8")
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
