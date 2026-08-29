#!/usr/bin/env python3
"""Machine-readable playbook for the Windows/laptop agent. No secrets."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

STATE = Path("/var/lib/octopus/state")
INBOUND = Path("/var/lib/octopus/inbound")
OUTS = [
    STATE / "LAPTOP-AGENT-HANDOFF.json",
    Path("/root/LAPTOP-AGENT-HANDOFF.json"),
    INBOUND / "TO-LAPTOP" / "HANDOFF.json",
]


def _txt(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def _json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _active(unit: str) -> str:
    proc = subprocess.run(["systemctl", "is-active", unit], capture_output=True, text=True, check=False)
    return proc.stdout.strip() or "unknown"


def main() -> int:
    boot = _json(STATE / "boot_report.json")
    gap001 = _json(STATE / "gap001" / "boot_report.json")
    gap001_meta = _json(STATE / "gaps" / "GAP-001-cold_boot_unverified.json")
    gap002 = _json(STATE / "gaps" / "GAP-002-audit_head_unsigned.json")
    inbound_last = _json(STATE / "inbound-apply" / "last.json")
    ntp_mode = ""
    for line in Path("/boot/dietpi.txt").read_text(encoding="utf-8").splitlines():
        if line.startswith("CONFIG_NTP_MODE="):
            ntp_mode = line.split("=", 1)[1].strip()
    live_reg_ver = None
    for line in Path("/etc/octopus/config/registry.yaml").read_text(encoding="utf-8").splitlines()[:20]:
        if line.startswith("config_version:"):
            live_reg_ver = line.split(":", 1)[1].strip().strip("'\"")
            break
    reg_ready = (INBOUND / "SIGNED-REGISTRY-BUNDLE" / "registry.yaml.sig").is_file()
    ck_ready = (INBOUND / "SIGNED-CHECKPOINT-BUNDLE" / "checkpoint.json.sig").is_file() or (
        INBOUND / "SIGNED-CHECKPOINT-BUNDLE" / "checkpoint.json.sig"
    ).is_file()
    live_ready = boot.get("readiness_state") == "READY" and not boot.get("gates_failed")
    milestone_path = STATE / "milestones" / "WAVE0_OBSERVE_ONLY.json"
    milestone_sha256 = None
    if milestone_path.is_file():
        milestone_sha256 = hashlib.sha256(milestone_path.read_bytes()).hexdigest()
    doc = {
        "schema": "octopus.laptop-agent.handoff.v1",
        "written_at": datetime.now(timezone.utc).isoformat(),
        "human_required": False,
        "board": {
            "board_id": "sensorium-opi5pro-68e44cdf",
            "hostname": "DietPi",
            "ssh": {
                "host": "192.168.0.182",
                "port": 22,
                "user": "root",
                "server": "dropbear",
                "auth": "ed25519_pubkey",
                "cursor_remote_name": "dietpi",
            },
            "boot_id": _txt(Path("/proc/sys/kernel/random/boot_id")),
            "ntp_mode": ntp_mode,
            "timesyncd": _active("systemd-timesyncd"),
            "nats": _active("nats-server"),
            "sensorium": _active("octopus-sensorium"),
            "dropbear": _active("dropbear"),
            "stability": _active("octopus-stability"),
            "reflex": _active("octopus-reflex"),
            "fusiond": _active("octopus-fusiond"),
            "world_model": _active("octopus-world-model"),
            "skill_tracker": _active("octopus-skill-tracker"),
            "metacontrol": _active("octopus-metacontrol"),
        },
        "live": {
            "runtime_state": boot.get("runtime_state"),
            "readiness_state": boot.get("readiness_state"),
            "readiness_profile": "WAVE0_OBSERVE_ONLY",
            "gates_failed": boot.get("gates_failed"),
            "clock_trust": (boot.get("clock") or {}).get("clock_trust"),
            "ready_observe_only": live_ready,
        },
        "milestone": {
            "id": "WAVE0_OBSERVE_ONLY",
            "schema": "octopus.milestone-state.v1",
            "path": str(milestone_path),
            "laptop_copy": "/var/lib/octopus/inbound/TO-LAPTOP/WAVE0_OBSERVE_ONLY.json",
            "to_laptop": "/var/lib/octopus/inbound/TO-LAPTOP/WAVE0_OBSERVE_ONLY.json",
            "present": milestone_path.is_file(),
            "sha256": milestone_sha256,
            "signed": False,
            "authority": False,
            "note": (
                "Include this file in the next signed checkpoint on Windows. "
                "Do not treat local unsigned JSON as authority. "
                "This milestone does not close GAP-002 and does not bypass verifier/registry signatures."
            ),
        },
        "gap001": {
            "status": gap001.get("status") or gap001_meta.get("status"),
            "pass": gap001.get("pass"),
            "pre_boot_id": gap001.get("pre_boot_id"),
            "post_boot_id": gap001.get("post_boot_id"),
            "gates_failed": gap001.get("gates_failed"),
            "report": "/var/lib/octopus/state/gap001/boot_report.json",
        },
        "gap002": {
            "status": gap002.get("status"),
            "pass": gap002.get("pass"),
            "live_unsigned": "/var/lib/octopus/inbound/TO-LAPTOP/OCTOPUS-AUDIT-CHECKPOINT/checkpoint.unsigned.json",
        },
        "registry": {
            "live_version": live_reg_ver,
            "v6_unsigned_pack": "/var/lib/octopus/inbound/TO-LAPTOP/OCTOPUS-REGISTRY-V6-META-SHADOW/",
            "drop_signed_here": "/var/lib/octopus/inbound/SIGNED-REGISTRY-BUNDLE/",
            "signed_present": reg_ready,
        },
        "fusion_s1": {
            "contract": "/var/lib/octopus/state/registry/active.json",
            "health": "/var/lib/octopus/state/sensors/health.json",
            "frame": "/var/lib/octopus/state/fusion/latest-frame.json",
            "rule": "MANIFEST_ONLY emits heartbeat only; measurement is null; never zero-filled",
        },
        "stability": {
            "metrics": "http://127.0.0.1:9101/metrics",
            "bind": "127.0.0.1:9101",
            "ssh_tunnel": "ssh -N -L 9101:127.0.0.1:9101 root@192.168.0.182",
            "prometheus_target": "host.docker.internal:9101",
            "latest": "/var/lib/octopus/state/stability/latest.json",
            "source": "evidence_files_not_nats_consume",
            "grafana_compose": "/var/lib/octopus/inbound/TO-LAPTOP/prometheus-grafana/",
        },
        "reflex_a0": {
            "mode": "advisory_observe_only",
            "execute_enabled": False,
            "armed": False,
            "owner_approval": "required",
            "latest": "/var/lib/octopus/state/reflex/latest.json",
            "ledger": "/var/lib/octopus/state/reflex/ledger.jsonl",
            "ledger_head": "/var/lib/octopus/state/reflex/HEAD.json",
            "arming_criteria": "/etc/octopus/reflex_arming_criteria.yaml",
            "note": "Privileged actions are recorded and denied. Hash-chained ledger. No root executor. Do not arm.",
        },
        "cognition": {
            "package": "/opt/octopus/cognition",
            "homeostasis": "/var/lib/octopus/state/homeostasis/latest.json",
            "config": "/etc/octopus/homeostasis.yaml",
            "world_model": {
                "role": "predictor_shadow",
                "model": "persistence-v1",
                "latest": "/var/lib/octopus/state/world_model/latest.json",
                "ledger": "/var/lib/octopus/state/world_model/ledger.jsonl",
                "planner_invoked": False,
            },
            "skill": {
                "latest": "/var/lib/octopus/state/skill/latest.json",
                "min_samples": 50,
                "note": "Score is None until 50 paired outcomes. Persistence vs persistence is not eligible.",
            },
            "metacontrol": {
                "latest": "/var/lib/octopus/state/metacontrol/latest.json",
                "executable": False,
                "executed": "none",
                "action": "NONE",
                "note": "WAVE0 exposes would_decide (plan|reflex|block) for dashboards. executed is always none. Planner is never called.",
            },
            "shadow_validation": {
                "package": "/opt/octopus/shadow_validation",
                "laptop_copy": "/var/lib/octopus/inbound/TO-LAPTOP/octopus_shadow_validation/",
                "config": "/etc/octopus/world-model.yaml",
                "unit": "octopus-shadow-validation.service",
                "enabled": False,
                "replaces_live_world_model": False,
                "note": "Staging contracts only. Live predictor stays persistence-v1. Do not enable torch or bind :9464.",
            },
        },
        "pending_reboot": _json(STATE / "gap001" / "pre_reboot.json"),
        "inbound_apply_last": inbound_last,
        "owner_review": {
            "board": "/var/lib/octopus/state/owner-review/",
            "to_laptop": "/var/lib/octopus/inbound/TO-LAPTOP/owner-review/",
            "obsidian_note": "Owner Review.md",
            "decision": "KEEP_WAVE0_LOCKED",
            "ready_for_owner_decision": False,
            "t7_executed": False,
            "note": "T0-T6 artifacts only. Do not treat this package as OA. Unsigned checkpoint export did not close GAP-002.",
        },
        "obsidian_vault": str(INBOUND / "TO-LAPTOP" / "obsidian-octopus"),
        "season_report": str(INBOUND / "TO-LAPTOP" / "SEASON-REPORT.md"),
        "docs_symlink": "/var/lib/octopus/docs/obsidian",
        "milestone": {
            "id": "WAVE0_OBSERVE_ONLY",
            "path": str(STATE / "milestones" / "WAVE0_OBSERVE_ONLY.json"),
            "to_laptop": str(INBOUND / "TO-LAPTOP" / "WAVE0_OBSERVE_ONLY.json"),
            "present": (STATE / "milestones" / "WAVE0_OBSERVE_ONLY.json").is_file(),
            "sha256": (
                hashlib.sha256((STATE / "milestones" / "WAVE0_OBSERVE_ONLY.json").read_bytes()).hexdigest()
                if (STATE / "milestones" / "WAVE0_OBSERVE_ONLY.json").is_file()
                else None
            ),
            "note": "Unsigned local JSON is not authority. Include this file in the next Windows-signed checkpoint. Do not sign it on the board.",
        },
        "laptop_agent_playbook": [
            "SSH as root@192.168.0.182 (Dropbear :22, existing ed25519 key). Cursor remote name: dietpi.",
            "Read this file again after reconnect: /var/lib/octopus/state/LAPTOP-AGENT-HANDOFF.json",
            "Read the complete season briefing first: /var/lib/octopus/inbound/TO-LAPTOP/SEASON-REPORT.md (also Obsidian note Season Report.md).",
            "Pull /var/lib/octopus/inbound/TO-LAPTOP/ recursively to Windows.",
            "Read T0-T6 owner-review (KEEP_WAVE0_LOCKED): /var/lib/octopus/inbound/TO-LAPTOP/owner-review/ and Obsidian note Owner Review.md. This package is not an Owner Authorization.",
            "Open Obsidian vault: TO-LAPTOP/obsidian-octopus (Open folder as vault). Board symlink: /var/lib/octopus/docs/obsidian.",
            "Sign Registry v6 with EXISTING root-v2 only: run sign-registry-v2.bat. Do NOT run make-root-v2.bat.",
            "scp SIGNED-REGISTRY-BUNDLE/* to /var/lib/octopus/inbound/SIGNED-REGISTRY-BUNDLE/ (no private/).",
            "Sign the CURRENT checkpoint.unsigned.json from TO-LAPTOP (live head, not a stale copy). Run sign-checkpoint.bat.",
            "scp SIGNED-CHECKPOINT-BUNDLE/* to /var/lib/octopus/inbound/SIGNED-CHECKPOINT-BUNDLE/.",
            "Board path units auto-verify and apply. If checkpoint seq mismatches live head, board re-exports unsigned; sign that new file.",
            "Do not enable actuators, MQTT, legs, or claim ARMED. READY means WAVE0_OBSERVE_ONLY.",
            "Stability scrape is loopback-only. On the laptop: ssh -N -L 9101:127.0.0.1:9101 root@192.168.0.182 then docker compose with target host.docker.internal:9101.",
            "Include /var/lib/octopus/state/milestones/WAVE0_OBSERVE_ONLY.json (and its sha256 from this handoff) in the next signed checkpoint. Unsigned local JSON is not authority.",
            "Read full steps in /var/lib/octopus/inbound/TO-LAPTOP/LAPTOP-AGENT-INSTRUCTIONS.md",
            "Sign the CURRENT live checkpoint (match G15 seq/head.hash). The TO-LAPTOP unsigned file may be stale.",
        ],
        "do_not": [
            "copy private/ or *.ed25519.private onto the board",
            "run make-root-v2.bat",
            "open PWM/motors",
            "re-add NATS user leg01",
            "run a root NATS action_executor or drop_caches/throttle_cpu",
            "replace signed apply_signed_inbound.py with unsigned placeholders",
            "enable planning, Doctor, FastAPI lockdown, or a policy that imports the world model",
            "replace octopus-world-model.service with a torch/768MiB runtime or user octopus-sense",
            "scrape 192.168.0.182:9101; use ssh -N -L 9101:127.0.0.1:9101",
            "treat unsigned WAVE0_OBSERVE_ONLY.json or owner-review artifacts as authority; include checkpoint sha256 in the next signed checkpoint",
            "docker compose up, bind :9464/:8080, or replace persistence-v1 on this board",
            "docker compose the 92-test / bioai-lab zip on the Pi",
            "bind or start FastAPI :9464 on the board",
        ],
        "checkpoint_signed_present": ck_ready,
    }
    text = json.dumps(doc, indent=2) + "\n"
    for path in OUTS:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
