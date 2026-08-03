#!/usr/bin/env python3
from __future__ import annotations
import json, sys, tempfile
from pathlib import Path
OPS = Path(__file__).resolve().parents[2]
if str(OPS) not in sys.path: sys.path.insert(0, str(OPS))
from owner_console import catalog


def valid(cid="future_cap"):
    return {"schema":"octopus.capability-manifest.v1","capability_id":cid,"title":"Future",
      "version":"1","owner_phrases":["future"],"read_handler":"x:y",
      "action_contract":{"schema":None,"default_decision":"READ_ONLY"},
      "risk_class":"read","owner_gate":False,"surface":"owner_outer_dm",
      "runtime_status_probe":"IMPLEMENTED_NOT_WIRED","tests":[],
      "registration_is_authorization":False}

def t_future_manifest_is_discovered_without_central_menu_edit():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td); p=root/"future"/"capability-manifest.json"; p.parent.mkdir()
        p.write_text(json.dumps(valid()),"utf-8")
        rs=catalog.discover(root)
        assert [r["capability_id"] for r in rs]==["future_cap"]
        assert rs[0]["status"]=="IMPLEMENTED_NOT_WIRED"

def t_invalid_manifest_stays_visible_but_not_live():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td); p=root/"bad"/"capability-manifest.json"; p.parent.mkdir()
        d=valid("bad_cap"); d["owner_gate"]="no"; d["action_contract"]="text"
        p.write_text(json.dumps(d),"utf-8")
        r=catalog.discover(root)[0]
        assert r["status"]=="MANIFEST_INVALID"
        assert r["owner_gate"] is True
        assert "bad-owner-gate" in r["errors"]

def t_not_live_is_never_parsed_as_live():
    assert catalog._parse_status("RATIFIED+WIRED, NOT_LIVE") == "NOT_LIVE"


def t_registration_can_never_authorize():
    d=valid(); d["registration_is_authorization"]=True
    assert "registration-must-not-authorize" in catalog.validate(d)

def t_duplicate_ids_are_visible_as_error():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        for n in ("a","b"):
            p=root/n/"capability-manifest.json"; p.parent.mkdir()
            p.write_text(json.dumps(valid("same")),"utf-8")
        rs=catalog.discover(root)
        assert len(rs)==2 and any("duplicate-capability-id" in r["errors"] for r in rs)

if __name__=="__main__":
    ts=[v for k,v in sorted(globals().items()) if k.startswith("t_")]
    [f() for f in ts]; print(f"OK {len(ts)}")
