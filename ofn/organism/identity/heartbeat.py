
import json, time, os

def beat(con, extra=None):
    body = {
        "organism_id": "board-life-001",
        "boot_id": extra.get("boot_id") if extra else None,
        "age_seconds": extra.get("age_seconds", 0) if extra else 0,
        "health_state": extra.get("health_state", "OBSERVING") if extra else "OBSERVING",
        "autonomy_state": "PROPOSE_ONLY",
        "last_event_sequence": extra.get("last_event_sequence", 0) if extra else 0,
        "identity_chain_valid": True,
        "local_cortex": extra.get("local_cortex", "STARTING") if extra else "STARTING",
        "external_api": "DISABLED",
        "memory_status": "AVAILABLE",
        "unknowns": extra.get("unknowns", []) if extra else [],
        "current_experiment": "board-life-001",
    }
    con.execute("INSERT INTO identity_heartbeat(ts, body_json) VALUES (?,?)", (time.time(), json.dumps(body, sort_keys=True)))
    return body
