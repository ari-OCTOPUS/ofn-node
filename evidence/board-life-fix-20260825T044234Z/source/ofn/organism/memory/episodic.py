
import json, time, hashlib
from ofn.organism.persistence.db import DB_LOCK

def remember(con, source_event_id, event_type, body, salience=0.5, outcome=None):
    if not source_event_id:
        raise ValueError("summary_without_provenance")
    with DB_LOCK:
        source = con.execute(
            "SELECT event_type FROM events WHERE event_id=?",
            (source_event_id,),
        ).fetchone()
        if not source:
            raise ValueError("source_event_not_found")
        if source[0] != event_type:
            raise ValueError("source_event_type_mismatch")
        existing = con.execute(
            """
            SELECT episode_id
            FROM episodes
            WHERE source_event_id=? AND event_type=?
            """,
            (source_event_id, event_type),
        ).fetchone()
        if existing:
            return existing[0]
        eid = hashlib.sha256(
            f"{source_event_id}:{event_type}".encode()
        ).hexdigest()[:32]
        con.execute(
            "INSERT OR IGNORE INTO episodes(episode_id,source_event_id,event_type,salience,outcome,body_json,created_at) VALUES (?,?,?,?,?,?,?)",
            (eid, source_event_id, event_type, salience, outcome, json.dumps(body, sort_keys=True), time.time()),
        )
        row = con.execute(
            """
            SELECT episode_id
            FROM episodes
            WHERE source_event_id=? AND event_type=?
            """,
            (source_event_id, event_type),
        ).fetchone()
        return row[0]

def recall(con, event_type=None, limit=20):
    query = """
        SELECT ep.episode_id, ep.source_event_id, ep.event_type, ep.salience,
               ep.outcome, ep.body_json, ep.created_at, ev.hash,
               CASE
                 WHEN ev.event_id IS NOT NULL AND ev.event_type=ep.event_type
                 THEN 1 ELSE 0
               END
        FROM episodes AS ep
        LEFT JOIN events AS ev ON ev.event_id=ep.source_event_id
    """
    with DB_LOCK:
        if event_type:
            rows = con.execute(
                query
                + " WHERE ep.event_type=? ORDER BY ep.created_at DESC LIMIT ?",
                (event_type, limit),
            ).fetchall()
        else:
            rows = con.execute(
                query + " ORDER BY ep.created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
    return [
        {
            "episode_id": row[0],
            "source_event_id": row[1],
            "event_type": row[2],
            "salience": row[3],
            "outcome": row[4],
            "body": json.loads(row[5]),
            "created_at": row[6],
            "source_event_hash": row[7],
            "provenance_valid": bool(row[8]),
        }
        for row in rows
    ]
