#!/usr/bin/env python3
"""Generate docs and owner-approval bundles. Does not apply live config or NATS changes."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import yaml

from octopus_sensorium.audit import export_checkpoint
from octopus_sensorium.schema_ids import is_runtime_enabled

ROOT = Path("/var/lib/octopus/staging/sensorium-software-v1")
WORK = ROOT / "work"
DOCS = WORK / "docs"
BUNDLES = ROOT / "bundles"
REG = Path("/etc/octopus/config/registry.yaml")
BOARD = Path("/etc/octopus/config/board.yaml")
TS = datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


def catalog_rows(sensors: list[dict]) -> str:
    lines = ["| ID | Name | Family | Status | Enabled | Plugin |", "|---|---|---|---|---|---|"]
    for spec in sensors:
        plugin = (spec.get("plugin") or {}).get("type") or "none"
        lines.append(
            f"| {spec.get('sensor_id')} | {spec.get('name')} | {spec.get('family')} | "
            f"{spec.get('status')} | {spec.get('enabled')} | {plugin} |"
        )
    return "\n".join(lines)


def main() -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    BUNDLES.mkdir(parents=True, exist_ok=True)
    registry = yaml.safe_load(REG.read_text(encoding="utf-8"))
    sensors = registry.get("sensors") or []
    runtime = [s["sensor_id"] for s in sensors if is_runtime_enabled(s)]
    shadow = [s["sensor_id"] for s in sensors if s.get("status") == "SHADOW"]
    active = [s["sensor_id"] for s in sensors if s.get("status") == "ACTIVE"]
    blocked = [s["sensor_id"] for s in sensors if str(s.get("status", "")).startswith("BLOCKED")]
    manifest = [s["sensor_id"] for s in sensors if s.get("status") in {"MANIFEST_ONLY", "PLANNED", "DEFERRED"}]

    write(
        DOCS / "SENSOR_CATALOG_100.md",
        f"# SENSOR_CATALOG_100\n\nLive Registry v5 `{sha(REG)}` at {TS}.\n\n"
        "Status values are live. Plugins exist for 096/097/099/100 in SENSORIUM_SOFTWARE_V1 "
        "but remain MANIFEST_ONLY until a signed Registry v6 is applied.\n\n"
        + catalog_rows(sensors),
    )
    write(
        DOCS / "RUNTIME_SENSOR_INVENTORY.md",
        f"# RUNTIME_SENSOR_INVENTORY\n\nACTIVE: {active}\n\nSHADOW: {shadow}\n\n"
        f"is_runtime_enabled: {runtime}\n\n"
        "096/097/099/100 plugins are in the software release and are not loaded from Registry v5.",
    )
    write(
        DOCS / "SENSORIUM_ARCHITECTURE.md",
        """# SENSORIUM_ARCHITECTURE

Board agent `agent://octopus/sensorium-board/main` on `sensorium-opi5pro-68e44cdf`.

Live code: `/opt/octopus/current` → release directory (atomic symlink).
Config: signed `/etc/octopus/config/{board,registry}.yaml` verified with root-v2.
State: `/var/lib/octopus/state` (snapshots, evidence, sequences).
Audit: `/var/lib/octopus/audit` append-only hash chain.
Bus: NATS Core + JetStream on 192.168.0.182:4222. Agent cannot create streams.

SOFTWARE_PLATFORM_COMPLETE ≠ ARMED ≠ HARDWARE_SAFE ≠ ALL_100_SENSORS_ACTIVE.
READY means WAVE0_OBSERVE_ONLY.
""",
    )
    write(
        DOCS / "UNIVERSAL_ENVELOPE.md",
        """# UNIVERSAL_ENVELOPE

Required fields: event_id, schema_version, sequence_number, sensorium_board_id, sensor_id,
subsensor_id, sensor_agent_id, observation_type, observed_property, subject, result, time,
location, quality, uncertainty, provenance, evidence, security, routing, policy.

Rules:
- provenance, evidence, and policy are mandatory
- time_unverified is explicit
- signature_verified is false unless a real verify set verified_by
- confidence is clamped to [0,1]
- canonical JSON + SHA-256 content hash
- malformed events append to quarantine jsonl; originals are not rewritten
""",
    )
    write(
        DOCS / "NATS_SUBJECTS.md",
        """# NATS_SUBJECTS

Streams (historical, 8): SENSORIUM, OBSERVATION, FEATURE, SENSOR_HEALTH, WORLD, AUDIT, COMMAND, LEG.

Subjects used by the agent:
- octopus.sensor.observation.<id>
- octopus.sensor.feature.<id>
- octopus.sensor.health.<id>
- octopus.sensor.anomaly.OCT-SENSE-092
- octopus.world.contradiction
- octopus.sensorium.{heartbeat,health,birth,alert,capabilities}
- octopus.audit.sensorium
- octopus.command.sensorium (receive only; commands do not execute)

EVIDENCE and ANOMALIES streams are not provisioned. Local evidence jsonl is the store.
A provisioning bundle exists; runtime must not create streams.
""",
    )
    write(
        DOCS / "NATS_PERMISSIONS.md",
        """# NATS_PERMISSIONS

Live users (names only): sensorium, leg01.

sensorium may publish octopus.sensor.>, octopus.sensorium.>, octopus.world.>, octopus.audit.>
and subscribe octopus.command.>, octopus.leg.>.

leg01 currently has publish octopus.leg.01.> while leg_authority=DENIED.
A maintenance bundle is prepared to deny-all/remove leg01. It is not applied without owner approval.
Passwords and bcrypt hashes are not documented here.
""",
    )
    write(
        DOCS / "EVIDENCE_MODEL.md",
        """# EVIDENCE_MODEL

Append-only `/var/lib/octopus/state/evidence/observations.jsonl`.
Indexes: event_id, sequence, timestamp, sensor_id, subject, observed_property.
last_*.json files are latest pointers, not the historical store.
Duplicates are detected by event_id. Hash mismatch fails verify_jsonl.
Retention policy: 14 days for derived indexes; jsonl is not rewritten.
No independent JetStream EVIDENCE stream is live.
""",
    )
    write(
        DOCS / "AUDIT_CHAIN.md",
        """# AUDIT_CHAIN

Fields: previous_hash, payload_hash, record_hash, sequence, head.hash.
verify_chain walks the jsonl. Concurrent delayed forks from a seen parent are accepted.
GAP-002 remains OPEN until an offline-signed checkpoint verifies.
audit_integrity=HASH_CHAIN_ONLY until that happens.
""",
    )
    write(
        DOCS / "REPLAY_MODEL.md",
        """# REPLAY_MODEL

G13 PASS requires hash(full_replay) == hash(snapshot_plus_tail_replay).
diagnose_journal reports missing sequences, duplicates, and corrupt lines on a copy.
apply_event ignores duplicate content_hash. Original journals are never rewritten.
""",
    )
    write(
        DOCS / "META_SENSES.md",
        """# META_SENSES

092 anomaly: Shadow, MAD/CUSUM/rate/missing/invalid-transition/rules. No enforcement.
095 contradiction: Shadow, CON-R001..R014. Cannot overwrite source observations.
096 uncertainty: plugin ready, Registry v5 MANIFEST_ONLY.
097 novelty: plugin ready, novelty≠anomaly, Registry v5 MANIFEST_ONLY.
099 policy/safety: plugin ready, may propose DEGRADED/FAILED_SAFE, cannot act.
100 provenance: plugin ready, grades evidence quality only.

Cycles 092→092, 095→092, self-ingest of 096/097/100 are denied.
""",
    )
    write(
        DOCS / "READINESS_CONTRACT.md",
        """# READINESS_CONTRACT

runtime_state ACTIVE is not readiness READY.
systemd is-active is not READY.
READY/WAVE0_OBSERVE_ONLY requires gates_failed=[], trusted clock, signed config,
observe-only isolation, MQTT closed, leg DENIED, actuator NONE.

Changing readiness_profile requires owner approval.
""",
    )
    write(
        DOCS / "SECURITY_MODEL.md",
        """# SECURITY_MODEL

Trust: root-v2 live, root-v1 revoked, signing OFFLINE_ONLY, no v2 private on board.
DevicePolicy=closed. PWM/GPIO/watchdog denied to user octopus.
Policy gate drops enforcing shadow output and all commands (command_trust_root_not_bound).
MQTT closed. Actuator authority NONE.
""",
    )
    write(
        DOCS / "SIGNING_WORKFLOW.md",
        """# SIGNING_WORKFLOW

Never generate keys on this board. Never copy private/ to the Pi.
Windows packagers sign with the existing root-v2 private key.
Output is SIGNED-BUNDLE only. Apply is a separate owner yes/no.
""",
    )
    write(
        DOCS / "SCHEMA_MIGRATIONS.md",
        """# SCHEMA_MIGRATIONS

upgrade_observation fills location/evidence/policy and forces signature_verified=false.
Legacy records are not deleted. Malformed events go to quarantine jsonl.
""",
    )
    write(
        DOCS / "RECOVERY_RUNBOOK.md",
        f"""# RECOVERY_RUNBOOK

Code rollback: `ln -sfn /opt/octopus/releases/phase2-kernel-v1 /opt/octopus/current && systemctl restart octopus-sensorium`

Do not restore root-v1. Do not rewrite audit or evidence.
Wave 0 freeze `{sha(Path('/var/lib/octopus/state/wave0-baseline/registry.yaml'))}` must stay.
Registry v4 and v5 milestones stay.
If gates_failed is non-empty after restart, keep DEGRADED and do not claim READY.
""",
    )
    write(
        DOCS / "DEPLOYMENT_RUNBOOK.md",
        """# DEPLOYMENT_RUNBOOK

1. Build a read-only release under /opt/octopus/releases/<id>
2. Run pytest inside that tree
3. Verifier to a temp file, not live boot_report
4. Atomic `ln -sfn` of /opt/octopus/current
5. Restart only octopus-sensorium
6. Promote boot_report only if gates_failed=[]
""",
    )
    write(
        DOCS / "LEG_INTEGRATION_DISABLED.md",
        """# LEG_INTEGRATION_DISABLED

leg_authority=DENIED. Stream LEG may remain historical.
A NATS user named leg01 still exists. That is a policy contradiction (CON-R011).
Removal/deny-all requires owner approval. Birth from unknown legs must be rejected.
""",
    )
    write(
        DOCS / "MQTT_DISABLED.md",
        """# MQTT_DISABLED

mqtt_state=DISABLED. Port 1883 must stay closed. Opening MQTT requires owner approval.
""",
    )
    write(
        DOCS / "OPEN_GAPS.md",
        """# OPEN_GAPS

GAP-001 cold_boot_unverified — DEFERRED_BY_OPERATOR. Not PASS.
GAP-002 audit_head_unsigned — DEFERRED_TO_WAVE1. audit_integrity=HASH_CHAIN_ONLY. Not PASS.

A reboot is required to close GAP-001. A Windows-signed checkpoint is required to close GAP-002.
""",
    )
    write(
        DOCS / "SOFTWARE_PLATFORM_COMPLETE.md",
        f"""# SOFTWARE_PLATFORM_COMPLETE

Declared for software kernel, envelope, evidence, audit hash-chain, replay, policy gate,
092/095 shadow, 096/097/099/100 plugins in-tree, tests, docs, and release SENSORIUM_SOFTWARE_V1.

Not declared: ALL_100_SENSORS_ACTIVE, ARMED, ACTUATOR_READY, LEG_CONTROL_READY, HARDWARE_SAFE.

Live runtime remains the six Wave 0 sensors until signed Registry v6 is applied.
Generated {TS}.
""",
    )

    # unsigned registry v6 enabling meta shadows
    pack = Path("/root/OCTOPUS-REGISTRY-V6-META-SHADOW")
    if pack.exists():
        shutil.rmtree(pack)
    pack.mkdir()
    live_reg = yaml.safe_load(REG.read_text(encoding="utf-8"))
    live_reg["config_version"] = 6
    plugin_map = {
        "OCT-SENSE-096": ("uncertainty", "meta.uncertainty"),
        "OCT-SENSE-097": ("novelty", "meta.novelty"),
        "OCT-SENSE-099": ("policy", "meta.policy_safety"),
        "OCT-SENSE-100": ("provenance", "meta.provenance"),
    }
    for spec in live_reg["sensors"]:
        sid = spec.get("sensor_id")
        if sid in plugin_map:
            ptype, prop = plugin_map[sid]
            spec["status"] = "SHADOW"
            spec["enabled"] = True
            spec["mode"] = "shadow"
            spec["version"] = "1.0.0"
            spec["plugin"] = {"type": ptype, "module": f"octopus_sensorium.meta.{ptype if ptype != 'policy' else 'policy_safety'}"}
            spec["publication"] = {
                "raw_enabled": False,
                "observation_enabled": True,
                "feature_enabled": True,
                "shadow_only": True,
                "can_change_readiness": False,
                "can_quarantine": False,
                "can_execute": False,
            }
            spec["schedule"] = {
                "mode": "interval",
                "default_interval_seconds": 5,
                "minimum_interval_seconds": 1,
                "maximum_interval_seconds": 3600,
            }
            spec["block_reason"] = "awaiting signed apply; shadow advisory only"
            spec["source_requirements"] = {"present": True, "reason": "software plugin ready"}
    (pack / "board.yaml").write_bytes(BOARD.read_bytes())
    (pack / "registry.yaml").write_text(yaml.safe_dump(live_reg, sort_keys=False), encoding="utf-8")
    shutil.copy2("/root/OCTOPUS-REGISTRY-100/sign-registry-v2.bat", pack / "sign-registry-v2.bat")
    sign_py = Path("/root/OCTOPUS-REGISTRY-100/sign_registry_v2.py").read_text(encoding="utf-8")
    sign_py = sign_py.replace("REGISTRY_100_CONTENT", "REGISTRY_V6_META_SHADOW")
    (pack / "sign_registry_v2.py").write_text(sign_py, encoding="utf-8")
    write(
        pack / "README.txt",
        "Sign with existing root-v2 only. Do not run make-root-v2.bat.\n"
        "Copy only SIGNED-REGISTRY-BUNDLE back. Do not copy private/.\n"
        "This enables 096/097/099/100 as SHADOW. It does not enable actuators, MQTT, or legs.\n",
    )

    nats_dir = BUNDLES / "nats-leg01-deny"
    nats_dir.mkdir(parents=True, exist_ok=True)
    write(
        nats_dir / "PLAN.md",
        """# NATS leg01 deny-all (NOT APPLIED)

Proposed change: remove or deny-all the `leg01` NATS user. Keep stream LEG historical.
Move `/root/octopus-ca/nats-leg01.env` out of any future active path (already not in /etc/octopus/secrets).
Reload nats-server only after owner yes. Do not put live password hashes in this bundle.

Test after apply: leg01 must not be able to publish Birth; sensorium connection must remain CONNECTED.
""",
    )
    write(nats_dir / "manifest.json", json.dumps({
        "bundle": "NATS_LEG01_DENY",
        "applied": False,
        "needs_owner": True,
        "live_users_named": ["sensorium", "leg01"],
        "active_secret_files": ["nats-sensorium.env"],
        "historical_leg_env": "/root/octopus-ca/nats-leg01.env",
    }, indent=2))

    cons_dir = BUNDLES / "consumer-cleanup"
    cons_dir.mkdir(parents=True, exist_ok=True)
    consumers = {"note": "jsz consumer dump", "applied": False}
    try:
        jsz = json.load(urllib.request.urlopen("http://127.0.0.1:8222/jsz?consumers=1", timeout=3))
        names = []
        for acct in jsz.get("account_details") or []:
            for stream in acct.get("stream_detail") or []:
                for c in stream.get("consumer_detail") or []:
                    names.append({"stream": stream.get("name"), "name": c.get("name"), "num_pending": c.get("num_pending")})
        consumers["consumers"] = names
    except Exception as exc:
        consumers["error"] = type(exc).__name__
    write(cons_dir / "inventory.json", json.dumps(consumers, indent=2))
    write(
        cons_dir / "PLAN.md",
        """# Bootstrap consumer cleanup (NOT APPLIED)

No stream or message deletion. Only durable consumer state may be removed after owner yes,
and only if the runtime agent is not bound to that durable.
""",
    )

    ev_dir = BUNDLES / "stream-evidence-anomalies"
    ev_dir.mkdir(parents=True, exist_ok=True)
    write(
        ev_dir / "PLAN.md",
        """# Optional EVIDENCE/ANOMALIES streams (NOT APPLIED)

Local jsonl evidence store is live. Independent JetStream streams are optional.
Runtime Agent must not create them. Provisioner would need --i-am-the-provisioner and owner yes.
""",
    )

    cp = export_checkpoint()
    cp_dir = BUNDLES / "audit-checkpoint"
    cp_dir.mkdir(parents=True, exist_ok=True)
    write(cp_dir / "checkpoint.unsigned.json", json.dumps(cp, indent=2))
    win = Path("/root/OCTOPUS-AUDIT-CHECKPOINT")
    if win.exists():
        shutil.rmtree(win)
    win.mkdir()
    write(win / "checkpoint.unsigned.json", json.dumps(cp, indent=2))
    write(
        win / "sign-checkpoint.bat",
        """@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %ERRORLEVEL%==0 (set PY=py -3) else (set PY=python)
%PY% -c "import nacl.signing" 2>nul || %PY% -m pip install --user pynacl
%PY% "%~dp0sign_checkpoint.py"
pause
""",
    )
    write(
        win / "sign_checkpoint.py",
        '''#!/usr/bin/env python3
"""Sign audit checkpoint with existing root-v2. Windows only."""
from __future__ import annotations
import hashlib, json, os, sys
from datetime import datetime, timezone
from pathlib import Path
from nacl.signing import SigningKey
HERE = Path(__file__).resolve().parent
SRC = HERE / "checkpoint.unsigned.json"
EXPECTED_V2 = "sha256:a20d836d1f461482c76c4d3ed6c6de301d38b3e8e0ef4707e87d7b45e2223a40"
BUNDLE = HERE / "SIGNED-CHECKPOINT-BUNDLE"

def find_key():
    for path in [
        HERE / "private" / "root-v2.ed25519.private",
        Path.home() / "Desktop" / "OCTOPUS-ROOT-V2" / "private" / "root-v2.ed25519.private",
    ]:
        if path.is_file():
            return path
    print("existing root-v2 private key not found", file=sys.stderr)
    raise SystemExit(2)

def main():
    payload = SRC.read_bytes()
    key = SigningKey(find_key().read_bytes())
    fp = "sha256:" + hashlib.sha256(bytes(key.verify_key)).hexdigest()
    if fp != EXPECTED_V2:
        print("refusing unknown key", file=sys.stderr)
        return 5
    BUNDLE.mkdir(exist_ok=True)
    (BUNDLE / "checkpoint.json").write_bytes(payload)
    (BUNDLE / "checkpoint.json.sig").write_bytes(key.sign(payload).signature)
    (BUNDLE / "root-v2.ed25519.public").write_bytes(bytes(key.verify_key))
    (BUNDLE / "manifest.json").write_text(json.dumps({
        "bundle_type": "AUDIT_CHECKPOINT",
        "public_key_fingerprint": fp,
        "signed_at": datetime.now(timezone.utc).isoformat(),
        "private_key_included": False,
    }, indent=2))
    print("signed checkpoint with root-v2", fp)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
''',
    )
    write(
        win / "README.txt",
        "Sign checkpoint.unsigned.json with existing root-v2. Copy SIGNED bundle back.\n"
        "GAP-002 stays open until the Pi verifies the signature against live head.hash.\n",
    )

    print(json.dumps({"docs": len(list(DOCS.glob('*.md'))), "runtime": runtime, "ts": TS}))


if __name__ == "__main__":
    main()
