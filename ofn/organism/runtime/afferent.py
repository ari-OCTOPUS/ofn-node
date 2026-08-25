from __future__ import annotations

import datetime as dt
import json
import signal
import time
from pathlib import Path
from typing import Any

from ofn.organism.runtime.lan_watch import (
    DEFAULT_ALLOWLIST,
    DEFAULT_STATE,
    allowed_targets,
    atomic_json,
    load_allowlist,
    next_status,
    probe_target,
)
from ofn.organism.runtime.telegram_letter import (
    append_local_letter,
    send_telegram,
    telegram_ready,
)


PUBLIC_PATH = Path("/opt/octopus/lab/state/ORGANISM-PUBLIC.json")
SOAK_PATH = Path("/opt/octopus/lab/evidence/SOAK-RESULTS.json")
RECEIPT_PATH = Path("/opt/octopus/lab/evidence/AFFERENT-LIVE.json")


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def format_letter(kind: str, detail: str, extra: dict[str, Any]) -> str:
    lines = [
        "board-life-001",
        f"kind={kind}",
        f"detail={detail}",
        f"health={extra.get('health_state')}",
        f"autonomy={extra.get('autonomy_state')}",
        f"identity_valid={extra.get('identity_chain_valid')}",
        f"utc={utc_now()}",
    ]
    return "\n".join(str(item) for item in lines)


def emit_letter(kind: str, detail: str, extra: dict[str, Any]) -> dict[str, Any]:
    text = format_letter(kind, detail, extra)
    record = {
        "utc": utc_now(),
        "kind": kind,
        "detail": detail,
        "telegram": telegram_ready(),
        "text": text,
    }
    append_local_letter(record)
    if kind in {"LAN_DOWN", "LAN_UP", "HEALTH_DANGER", "HEALTH_RECOVERY", "SOAK_ABORT"}:
        telegram = send_telegram(text)
    else:
        telegram = {"sent": False, "status": "NOT_A_DANGER_OR_RECOVERY_LETTER"}
    record["telegram_result"] = telegram.get("status")
    return record


def material_public(public: dict[str, Any]) -> dict[str, Any]:
    return {
        "health_state": public.get("health_state"),
        "autonomy_state": public.get("autonomy_state"),
        "identity_chain_valid": public.get("identity_chain_valid"),
        "alert": public.get("alert"),
        "letter": public.get("letter"),
        "llama_health": public.get("llama_health"),
        "soak_running": (public.get("soak") or {}).get("running"),
        "unknowns": public.get("unknowns") or [],
    }


def run_once(state: dict[str, Any]) -> dict[str, Any]:
    allowlist = load_allowlist()
    targets = allowed_targets(allowlist)
    public = read_json(PUBLIC_PATH)
    soak = read_json(SOAK_PATH)
    extra = {
        "health_state": public.get("health_state"),
        "autonomy_state": public.get("autonomy_state"),
        "identity_chain_valid": public.get("identity_chain_valid"),
    }
    letters = []
    host_state = state.setdefault("hosts", {})
    observations = []
    for target in targets:
        probe = probe_target(
            target,
            int(allowlist.get("icmp_timeout_s", 1)),
            float(allowlist.get("tcp_timeout_s", 1)),
        )
        previous = host_state.get(target["id"]) or {
            "status": "unknown",
            "fail_streak": 0,
            "recover_streak": 0,
        }
        status, fail_streak, recover_streak = next_status(
            previous.get("status", "unknown"),
            bool(probe["reachable"]),
            int(previous.get("fail_streak", 0)),
            int(previous.get("recover_streak", 0)),
            int(allowlist.get("fail_threshold", 3)),
            int(allowlist.get("recover_threshold", 2)),
        )
        changed = status != previous.get("status") and status in {"up", "down"}
        host_state[target["id"]] = {
            "id": target["id"],
            "ip": target["ip"],
            "label": target["label"],
            "status": status,
            "fail_streak": fail_streak,
            "recover_streak": recover_streak,
            "last_probe": probe,
            "updated_utc": utc_now(),
        }
        if changed and status == "down":
            letters.append(emit_letter("LAN_DOWN", f"{target['id']} unreachable", extra))
        elif changed and status == "up" and previous.get("status") in {"down", "down_candidate"}:
            letters.append(emit_letter("LAN_UP", f"{target['id']} recovered", extra))
        observations.append(host_state[target["id"]])

    previous_public = state.get("public_material") or {}
    current_public = material_public(public)
    previous_health = previous_public.get("health_state")
    current_health = current_public.get("health_state")
    if current_health in {"DEGRADED", "SAFE_HALT"} and previous_health not in {
        "DEGRADED",
        "SAFE_HALT",
        None,
    }:
        letters.append(emit_letter("HEALTH_DANGER", str(current_health), extra))
    if previous_health in {"DEGRADED", "SAFE_HALT"} and current_health in {
        "OBSERVING",
        "STABLE",
        "RECOVERING",
    }:
        letters.append(emit_letter("HEALTH_RECOVERY", str(current_health), extra))
    if current_public.get("identity_chain_valid") is False and previous_public.get(
        "identity_chain_valid"
    ) is not False:
        letters.append(emit_letter("HEALTH_DANGER", "identity_chain_invalid", extra))
    state["public_material"] = current_public

    previous_abort = state.get("soak_abort")
    current_abort = soak.get("abort")
    if current_abort and current_abort != previous_abort:
        letters.append(emit_letter("SOAK_ABORT", str(current_abort), extra))
    state["soak_abort"] = current_abort

    snapshot = {
        "claim_level": "OBSERVED",
        "updated_utc": utc_now(),
        "telegram": telegram_ready(),
        "allowlist_targets": [item["id"] for item in targets],
        "candidates_not_probed": allowlist.get("candidates_not_probed") or [],
        "hosts": observations,
        "public_material": current_public,
        "soak_abort": current_abort,
        "letters_this_tick": [item["kind"] for item in letters],
    }
    atomic_json(DEFAULT_STATE, snapshot)
    atomic_json(
        RECEIPT_PATH,
        {
            "updated_utc": utc_now(),
            "telegram": snapshot["telegram"],
            "hosts": {item["id"]: item["status"] for item in observations},
            "letters_this_tick": snapshot["letters_this_tick"],
        },
    )
    state["updated_utc"] = utc_now()
    return snapshot


def main() -> int:
    allowlist = load_allowlist(DEFAULT_ALLOWLIST)
    interval = max(10, int(allowlist.get("probe_interval_s", 30)))
    stop = False

    def request_stop(_signum, _frame):
        nonlocal stop
        stop = True

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)
    state: dict[str, Any] = {}
    while not stop:
        run_once(state)
        for _ in range(interval):
            if stop:
                break
            time.sleep(1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
