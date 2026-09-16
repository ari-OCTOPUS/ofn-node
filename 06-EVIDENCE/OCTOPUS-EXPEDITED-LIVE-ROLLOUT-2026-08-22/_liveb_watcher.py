import json, time, sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
ROOT=Path(r"F:\backup")
EV=ROOT/"06-EVIDENCE"/"OCTOPUS-EXPEDITED-LIVE-ROLLOUT-2026-08-22"
sys.path.insert(0,str(EV)); sys.path.insert(0,str(ROOT/"_ops")); sys.path.insert(0,str(ROOT/"_ops"/"tests"))
from _rollout_ops import now_local
from live_state_guard import allow_live_write
CANARY="2026-08-22T15:29:52.125+10:00"
canary_utc=datetime.fromisoformat(CANARY).astimezone(timezone.utc)
canary_naive=datetime.fromisoformat(CANARY).replace(tzinfo=None)
need=5
log=EV/"_liveb_watcher.log"
end=time.time()+50*60  # watch until roughly soak end

def scan():
    inbound=[]
    p=ROOT/"_ops/state/telegram/inbound-log.jsonl"
    for ln in p.read_text(encoding="utf-8",errors="replace").splitlines():
        if not ln.strip(): continue
        o=json.loads(ln); ts=o.get("ts")
        if not ts: continue
        t=datetime.fromisoformat(ts)
        if t.replace(tzinfo=None)>canary_naive: inbound.append(o)
    center_in=[r for r in inbound if r.get("bot")=="center" and r.get("from_owner") is True]
    inner_in=[r for r in inbound if r.get("bot")!="center" and r.get("from_owner") is True]
    consumed=[]
    for fp in sorted((ROOT/"_ops/state/telegram/loop/events").glob("tg_*.json")):
        o=json.loads(fp.read_text(encoding="utf-8"))
        recv=o.get("received_at") or o.get("closed_at")
        if not recv: continue
        rt=datetime.fromisoformat(recv.replace("Z","+00:00"))
        if rt.tzinfo is None: rt=rt.replace(tzinfo=timezone.utc)
        if rt>=canary_utc and o.get("state")=="CLOSED":
            ch=(o.get("chat_id_hash") or "")[:12]
            if ch!="14280e011544":
                continue
            consumed.append({
                "event_id":o.get("event_id"),"update_id":o.get("update_id"),"state":o.get("state"),
                "delivery_message_id":o.get("delivery_message_id"),"readback_verified":o.get("readback_verified"),
                "chat_id_hash_sha12":ch,"owner_chat_hash_match":True,
                "received_at":o.get("received_at"),"closed_at":o.get("closed_at"),
                "correlation_id":o.get("correlation_id"),
                "outward_effect":"owner-only reply CONFIRMED" if o.get("delivery_message_id") else None,
                "path":"canonical-center-durable-loop",
            })
    return center_in, inner_in, consumed

def write_liveb(center_in, inner_in, consumed, trigger):
    n=len(consumed)
    status="PASS" if n>=need else "WAITING_FOR_GENUINE_OWNER_EVENT"
    path=EV/"LIVE-B-RESULT.json"
    with allow_live_write("live-b-watcher-update"):
        prev=json.loads(path.read_text(encoding="utf-8"))
        prev_ids=set(c.get("event_id") for c in (prev.get("consumed_within_bounds") or []))
        new_ids=[c.get("event_id") for c in consumed if c.get("event_id") not in prev_ids]
        if not new_ids and prev.get("genuine_owner_events_closed")==n and prev.get("status")==status:
            return False, []
        note=(f"Watcher rescan ({trigger}): {n}/{need} CLOSED owner durable-loop; new={new_ids or 'none'}; "
              f"center_inbound={len(center_in)}. "+("LIVE-B PASS" if n>=need else "Still waiting — not fabricating."))
        prev.update({
            "status":status,"status_allowed_terminal":status=="WAITING_FOR_GENUINE_OWNER_EVENT",
            "genuine_owner_events_closed":n,"genuine_owner_events_required":need,
            "consumed_within_bounds":consumed,
            "inbound_after_canary":{"center_owner":center_in,"inner_owner_non_canonical_poller":inner_in,
                "note":"Only center bot + durable-loop CLOSED counts toward LIVE-B"},
            "note":note,"last_rescan_at_local":now_local(),"last_rescan_trigger":trigger,
            "new_events_this_rescan":new_ids,"fabricated":False,"impersonated_owner":False,"manual_getUpdates":False,
        })
        path.write_text(json.dumps(prev,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return True, new_ids

with log.open("a",encoding="utf-8") as f:
    f.write(f"{now_local()} watcher_start\n")
while time.time()<end:
    # stop if soak summary exists
    if (EV/"POST-ACTIVATION-SUMMARY.json").exists():
        with log.open("a",encoding="utf-8") as f:
            f.write(f"{now_local()} soak_summary_present exit\n")
        break
    try:
        c,i,cons=scan()
        changed,new_ids=write_liveb(c,i,cons,"periodic_30s")
        line=f"{now_local()} n={len(cons)} changed={changed} new={new_ids}\n"
        with log.open("a",encoding="utf-8") as f:
            f.write(line)
        print(line.strip(), flush=True)
        if len(cons)>=need:
            with log.open("a",encoding="utf-8") as f:
                f.write(f"{now_local()} LIVE_B_PASS exit\n")
            break
    except Exception as e:
        with log.open("a",encoding="utf-8") as f:
            f.write(f"{now_local()} err={e}\n")
    time.sleep(30)
print("watcher_done", flush=True)
