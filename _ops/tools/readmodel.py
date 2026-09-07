#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, time
from pathlib import Path
STATE = Path(__file__).resolve().parents[1] / "state"

def _read(p, d=None):
    try: return json.loads(p.read_text("utf-8"))
    except Exception: return d

def _fresh(mtime, fresh_s=300.0):
    age = time.time() - mtime
    return "fresh" if age < fresh_s else "stale" if age < fresh_s*6 else "very_stale"

def _card(name, value, path, fresh_s=300.0):
    p = STATE / path; e = p.exists(); m = p.stat().st_mtime if e else 0
    return {"name":name,"value":value if e else None,
            "as_of":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime(m)) if e else None,
            "source":f"state/{path}","freshness":_fresh(m,fresh_s) if e else "unavailable"}

def build():
    org = _read(STATE/"ORGANISM-STATE.json",{})
    tel = _read(STATE/"telemetry-latest.json",{})
    st = _read(STATE/"cortex/stress-latest.json",{})
    cal = _read(STATE/"cortex/calibration-latest.json",{})
    money = (tel.get("month") or {}).get("aud") or 0
    return {"readmodel_version":"1.0",
            "built_at":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
            "cards":{"beat":_card("beat",org.get("beat"),"ORGANISM-STATE.json",900),
                     "stress":_card("stress",st.get("level"),"cortex/stress-latest.json",600),
                     "quality":_card("quality",st.get("data_quality"),"cortex/stress-latest.json",600),
                     "calib_n":_card("calib_n",cal.get("n"),"cortex/calibration-latest.json",7200),
                     "budget":_card("budget",money,"telemetry-latest.json",3600),
                     "halted":_card("halted",org.get("halted"),"ORGANISM-STATE.json",900)},
            "summary":{"alive":bool(org.get("beat")),"halted":bool(org.get("halted")),
                       "stress":st.get("level","unknown"),"data_quality":st.get("data_quality","unknown"),
                       "budget_pct":round(money/45*100,1) if money else 0,"budget_cap":45}}

if __name__ == "__main__":
    print(json.dumps(build(), ensure_ascii=False, indent=1))
