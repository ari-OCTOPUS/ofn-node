"""Declared anatomy and timing, not inferred deployment or neural control."""
import math
from shadow_homeostasis.canonical import finite_number


def analyze_topology(graph):
    graph = graph or {"organs": [], "links": [], "required_organs": []}
    organs, links = graph.get("organs", []), graph.get("links", [])
    required = graph.get("required_organs", [])
    if not isinstance(required, list) or not isinstance(organs, list) or not isinstance(links, list) or len(organs) > 64 or len(links) > 256:
        raise ValueError("topology budget")
    if not all(isinstance(o, dict) and isinstance(o.get("id"), str) for o in organs):
        raise ValueError("organ identity required")
    ids = {o["id"] for o in organs}
    if len(ids) != len(organs) or not all(isinstance(i, str) for i in required):
        raise ValueError("duplicate/invalid organ identity")
    reports, connected = [], set()
    for link in links:
        source, target = link["from"], link["to"]
        latency, deadline = link.get("latency_ms"), link.get("deadline_ms")
        for value in (latency, deadline):
            if value is not None and (not finite_number(value) or value < 0):
                raise ValueError("timing must be nonnegative finite number")
        partitioned = link.get("partitioned", False)
        if type(partitioned) is not bool:
            raise ValueError("partition flag")
        missing = source not in ids or target not in ids
        state = ("MISSING_ENDPOINT" if missing else "PARTITIONED" if partitioned else
                 "UNKNOWN_TIMING" if latency is None or deadline is None else
                 "OVERDUE" if latency > deadline else "WITHIN_DEADLINE")
        if not missing and not partitioned:
            connected.update((source, target))
        reports.append({"from": source, "to": target, "state": state,
                        "latency_ms": latency, "deadline_ms": deadline,
                        "relationship": "DECLARED_UNVERIFIED", "executable": False})
    missing = sorted(set(required) - ids)
    isolated = sorted(ids - connected)
    return {"organs": sorted(organs, key=lambda o: o["id"]), "links": reports,
            "missing_required": missing, "isolated": isolated,
            "degraded": bool(not organs or missing or isolated or any(l["state"] != "WITHIN_DEADLINE" for l in reports)),
            "anatomy_state": "UNKNOWN" if not organs else "DECLARED",
            "deployment_status": "UNVERIFIED", "executable": False}
