"""B-safe laptop library loop. Does not call OCTOPUS-flags.cmd. Forces listed wires to 0."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

OPS = Path(r"F:\backup\_ops")
PY = r"C:\Program Files\Python313\python.exe"
FORCE_OFF = (
    "OCTOPUS_WIRE_VAULT_RAG",
    "OCTOPUS_WIRE_EPISTEMICS",
    "OCTOPUS_WIRE_LEAD_OUTBOUND",
    "OCTOPUS_WIRE_EMAIL",
    "OCTOPUS_WIRE_HARVEST",
    "CORTEX_HYPOTHESIS",
    "OCTOPUS_UNIFIED_CHAT",
    "OFN_KEEP_GATES_OPEN",
    "OCTOPUS_SMTP_USE_GMAIL",
    # paper-full defaults; apply_profile only sets these if absent
    "OCTOPUS_WIRE_DOCTOR",
    "OCTOPUS_WIRE_NEURAL",
    "OCTOPUS_WIRE_UNIFIED",
    "OCTOPUS_WIRE_LEAD",
    "OCTOPUS_WIRE_ZIMAN",
    "OCTOPUS_WIRE_SCHOOL",
    "OCTOPUS_WIRE_CONSOLIDATION",
    "OCTOPUS_WIRE_EVOLUTION",
    "OCTOPUS_WIRE_BOX",
    "OCTOPUS_WIRE_LEAD_TICK",
    "OCTOPUS_WIRE_IDEAS",
    "OCTOPUS_WIRE_CHRONO_RHYTHM",
    "OCTOPUS_WIRE_SPECTRAL",
    "OCTOPUS_WIRE_BCM",
    "OCTOPUS_WIRE_SPARSE",
    "OCTOPUS_WIRE_FISHER",
    "OCTOPUS_WIRE_CARTOGRAPHER",
)


def main() -> int:
    if (OPS / "STOP-ORGANISM").exists():
        print("STOP-ORGANISM present")
        return 2
    env = os.environ.copy()
    for key in FORCE_OFF:
        env[key] = "0"
    env["OCTOPUS_PROFILE"] = "bare"
    env["OCTOPUS_LIBRARY_LOOP"] = "1"
    env.pop("OCTOPUS_STATE_DIR", None)
    org = subprocess.Popen(
        [PY, "-X", "utf8", "organism.py"],
        cwd=str(OPS),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    cor = subprocess.Popen(
        [PY, "-X", "utf8", str(Path("cortex") / "cortex.py")],
        cwd=str(OPS),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print(f"organism_pid={org.pid} cortex_pid={cor.pid}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
