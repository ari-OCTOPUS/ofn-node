#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
OPS=Path(__file__).resolve().parents[2]
if str(OPS) not in sys.path: sys.path.insert(0,str(OPS))
from owner_console import telegram_adapter

OK={"allow":True,"mode":"core_conversation","reason":"outer-dm-owner"}

def t_authorized_outer_dm_is_handled():
    r=telegram_adapter.handle_message("خانه",surface_decision=OK)
    assert r["handled"] and r["reply"]["kind"]=="home"

def t_group_or_inner_is_never_handled():
    for d in ({"allow":True,"mode":"leg_scoped"},{"allow":True,"mode":"status_approval"},
              {"allow":False,"mode":"deny"},{}):
        assert not telegram_adapter.handle_message("خانه",surface_decision=d)["handled"]

def t_only_own_callbacks_are_claimed():
    assert telegram_adapter.handle_callback("oc:home",surface_decision=OK)["handled"]
    assert not telegram_adapter.handle_callback("tr:x",surface_decision=OK)["handled"]

def t_adapter_does_not_reinfer_owner():
    # No owner_id/chat_id/token args exist; upstream decision is the single authority.
    import inspect
    assert set(inspect.signature(telegram_adapter.handle_message).parameters)=={"text","surface_decision"}

if __name__=="__main__":
    ts=[v for k,v in sorted(globals().items()) if k.startswith("t_")]
    [f() for f in ts]; print(f"OK {len(ts)}")
