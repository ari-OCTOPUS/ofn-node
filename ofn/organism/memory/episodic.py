
import json, time, hashlib

def remember(con, source_event_id, event_type, body, salience=0.5, outcome=None):
    if not source_event_id:
        raise ValueError("summary_without_provenance")
    eid = hashlib.sha256(f"{source_event_id}:{event_type}:{time.time_ns()}".encode()).hexdigest()[:32]
    con.execute(
        "INSERT INTO episodes(episode_id,source_event_id,event_type,salience,outcome,body_json,created_at) VALUES (?,?,?,?,?,?,?)",
        (eid, source_event_id, event_type, salience, outcome, json.dumps(body, sort_keys=True), time.time()),
    )
    return eid

def recall(con, event_type=None, limit=20):
    if event_type:
        rows = con.execute("SELECT episode_id,source_event_id,event_type,salience,outcome,body_json,created_at FROM episodes WHERE event_type=? ORDER BY created_at DESC LIMIT ?", (event_type, limit)).fetchall()
    else:
        rows = con.execute("SELECT episode_id,source_event_id,event_type,salience,outcome,body_json,created_at FROM episodes ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    return [{"episode_id": r[0], "source_event_id": r[1], "event_type": r[2], "salience": r[3], "outcome": r[4], "body": json.loads(r[5]), "created_at": r[6]} for r in rows]
