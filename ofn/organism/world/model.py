from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from ofn.organism.persistence.db import DB_LOCK


DEFAULT_LAN_STATE = Path("/opt/octopus/lab/state/LAN-WATCH.json")


def load_lan_state(path: Path = DEFAULT_LAN_STATE) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def hosts_from_lan(lan: dict[str, Any]) -> list[dict[str, Any]]:
    hosts = []
    for item in lan.get("hosts") or []:
        hosts.append(
            {
                "id": item.get("id"),
                "ip": item.get("ip"),
                "label": item.get("label"),
                "status": item.get("status"),
                "fail_streak": item.get("fail_streak"),
                "recover_streak": item.get("recover_streak"),
                "last_probe": item.get("last_probe") or {},
            }
        )
    return hosts


def persist_hosts(con, hosts: list[dict[str, Any]]) -> list[str]:
    changes = []
    now = time.time()
    with DB_LOCK:
        for host in hosts:
            host_id = str(host.get("id") or "")
            if not host_id:
                continue
            previous = con.execute(
                "SELECT status FROM world_hosts WHERE host_id=?",
                (host_id,),
            ).fetchone()
            status = str(host.get("status") or "unknown")
            up = 1 if status == "up" else 0
            if previous is None:
                con.execute(
                    """
                    INSERT INTO world_hosts(
                        host_id, ip, label, status, last_change_at,
                        observations, up_observations, updated_at, last_probe_json
                    ) VALUES (?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        host_id,
                        str(host.get("ip") or ""),
                        str(host.get("label") or host_id),
                        status,
                        now,
                        1,
                        up,
                        now,
                        json.dumps(host.get("last_probe") or {}, sort_keys=True),
                    ),
                )
                changes.append(f"{host_id}:discovered:{status}")
            else:
                changed = previous[0] != status
                con.execute(
                    """
                    UPDATE world_hosts
                    SET ip=?, label=?, status=?,
                        last_change_at=CASE WHEN ? THEN ? ELSE last_change_at END,
                        observations=observations+1,
                        up_observations=up_observations+?,
                        updated_at=?,
                        last_probe_json=?
                    WHERE host_id=?
                    """,
                    (
                        str(host.get("ip") or ""),
                        str(host.get("label") or host_id),
                        status,
                        changed,
                        now,
                        up,
                        now,
                        json.dumps(host.get("last_probe") or {}, sort_keys=True),
                        host_id,
                    ),
                )
                if changed:
                    changes.append(f"{host_id}:{previous[0]}->{status}")
    return changes


def known_hosts(con) -> list[dict[str, Any]]:
    with DB_LOCK:
        rows = con.execute(
            """
            SELECT host_id, ip, label, status, observations, up_observations
            FROM world_hosts
            ORDER BY host_id
            """
        ).fetchall()
    result = []
    for row in rows:
        observations = max(1, int(row[4]))
        result.append(
            {
                "id": row[0],
                "ip": row[1],
                "label": row[2],
                "status": row[3],
                "observations": observations,
                "up_ratio": round(int(row[5]) / observations, 3),
            }
        )
    return result
