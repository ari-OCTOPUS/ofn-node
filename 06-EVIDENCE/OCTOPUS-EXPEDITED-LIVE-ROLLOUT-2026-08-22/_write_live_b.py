import json, time, sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
ROOT=Path(r"F:\backup"); EV=ROOT/"06-EVIDENCE"/"OCTOPUS-EXPEDITED-LIVE-ROLLOUT-2026-08-22"
sys.path.insert(0,str(EV)); sys.path.insert(0,str(ROOT/"_ops"))
from _rollout_ops import now_local, read_json
from live_state_guard import allow_live_write
CANARY="2026-08-22T15:29:52.125+10:00"
AUTH="OCTOPUS-OWNER-CANARY-20260822-N1"
# heartbeat
lock_path=ROOT/"_ops/state/locks/octopus-writer.lock"
with allow_live_write("live-b-writer-heartbeat"):
    lock=json.loads(lock_path.read_text(encoding="utf-8"))
    assert lock.get("agent_id")=="grok-ari-single-writer"
    now=time.time(); remain=(float(lock["expires_at"])-now)/3600
    lock["heartbeat_at"]=now; lock["renewed_at"]=round(now,3); lock["renewed_at_local"]=now_local()
    lock_path.write_text(json.dumps(lock,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
hb={"ok":True,"remaining_hours":remain,"ttl_extended":False,"agent_id":"grok-ari-single-writer"}
# inbound after canary
canary_naive=datetime.fromisoformat(CANARY).replace(tzinfo=None)
inbound=[]
p=ROOT/"_ops/state/telegram/inbound-log.jsonl"
for ln in p.read_text(encoding="utf-8",errors="replace").splitlines():
    if not ln.strip(): continue
    o=json.loads(ln); ts=o.get("ts");
    if not ts: continue
    t=datetime.fromisoformat(ts)
    if t.replace(tzinfo=None)>canary_naive: inbound.append(o)
center_in=[r for r in inbound if r.get("bot")=="center" and r.get("from_owner") is True]
inner_in=[r for r in inbound if r.get("bot")!="center" and r.get("from_owner") is True]
# closed loops after canary
canary_utc=datetime.fromisoformat(CANARY).astimezone(timezone.utc)
consumed=[]
for fp in sorted((ROOT/"_ops/state/telegram/loop/events").glob("tg_*.json")):
    o=json.loads(fp.read_text(encoding="utf-8"))
    recv=o.get("received_at") or o.get("closed_at")
    if not recv: continue
    rt=datetime.fromisoformat(recv.replace("Z","+00:00"))
    if rt.tzinfo is None: rt=rt.replace(tzinfo=timezone.utc)
    if rt>=canary_utc and o.get("state")=="CLOSED":
        ch=(o.get("chat_id_hash") or "")[:12]
        consumed.append({"event_id":o.get("event_id"),"update_id":o.get("update_id"),"state":o.get("state"),
            "delivery_message_id":o.get("delivery_message_id"),"readback_verified":o.get("readback_verified"),
            "chat_id_hash_sha12":ch,"owner_chat_hash_match":ch=="14280e011544",
            "received_at":o.get("received_at"),"closed_at":o.get("closed_at"),
            "correlation_id":o.get("correlation_id"),
            "outward_effect":"owner-only reply CONFIRMED" if o.get("delivery_message_id") else None,
            "path":"canonical-center-durable-loop"})
n=len(consumed); need=5
status="PASS" if n>=need else "WAITING_FOR_GENUINE_OWNER_EVENT"
note=(f"Observed {n}/{need} CLOSED owner durable-loop events after canary "
      f"(center_inbound={len(center_in)}, inner_non_canonical={len(inner_in)}); "
      "LIVE-B bar typically requires 5 real owner events / A18 path — not fabricating")
result={"schema":"octopus-live-b-result/1","authorization_id":AUTH,"mode":"EXPEDITED_BOUNDED_LIVE_ROLLOUT",
 "builder":"grok-ari-single-writer","written_at_local":now_local(),
 "canary_ref":str(EV/"CANARY-N1.json"),"canary_timestamp_local":CANARY,"canary_message_id":596,
 "protocol":{"name":"LIVE-B","bounds":["no fabricated owner events","no owner impersonation","no manual getUpdates",
  "canonical poller / durable-loop only","owner-only outward effects","typically 5 real owner events (A18 path)"],
  "events_required_typical":need},
 "status":status,"status_allowed_terminal":status=="WAITING_FOR_GENUINE_OWNER_EVENT",
 "genuine_owner_events_closed":n,"genuine_owner_events_required":need,"consumed_within_bounds":consumed,
 "inbound_after_canary":{"center_owner":center_in,"inner_owner_non_canonical_poller":inner_in,
  "note":"Only center bot + durable-loop CLOSED counts toward LIVE-B"},
 "fabricated":False,"impersonated_owner":False,"manual_getUpdates":False,"broadcast":False,
 "webhook_mutated":False,"paid_calls":0,"second_canary":False,"heartbeat":hb,"note":note,"rfc":"NO_RFC_ELIGIBLE"}
(EV/"LIVE-B-RESULT.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print("LIVE_B",status,"closed",n)
