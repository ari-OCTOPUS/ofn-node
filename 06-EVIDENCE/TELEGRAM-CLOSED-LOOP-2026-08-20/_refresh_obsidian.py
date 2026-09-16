# -*- coding: utf-8 -*-
"""Refresh Obsidian-facing labels + NOW.md + CURRENT-TRUTH auto block from A19."""
from __future__ import annotations

import datetime
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(r"F:/backup")
OPS = ROOT / "_ops"
sys.path.insert(0, str(OPS / "scripts"))
sys.path.insert(0, str(OPS))

from label_history import append  # noqa: E402
from intel_spine.obsidian_sync import safe_update_note  # noqa: E402
import render_now  # noqa: E402

NOW = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")
EV = "06-EVIDENCE/TELEGRAM-CLOSED-LOOP-2026-08-20/A19-HANDOFF.json"
EV_PATH = ROOT / EV
EV_HASH = hashlib.sha256(EV_PATH.read_bytes()).hexdigest()[:16]

UPDATES = {
    "DAEMON_PID": {
        "value": "organism=zive · center=8828 · brain.daemon=25680(old code)",
        "status": "OBSERVED",
        "evidence_path": "_ops/state/telegram/process-identity.json",
        "evidence_hash": hashlib.sha256(
            (OPS / "state/telegram/process-identity.json").read_bytes()).hexdigest()[:16],
    },
    "WRITER_LEASE": {
        "value": "RELEASED after A19 · archive octopus-writer.lock.released.1787222380",
        "status": "VERIFIED",
        "evidence_path": "_ops/state/locks/octopus-writer.lock.released.1787222380",
        "evidence_hash": "",
    },
    "LIVE_GATES": {
        "value": "A=PASS · B=BLOCKED(telegram A13-A17 PASS; Full Loop not started) · C=PASS · D/E=BLOCKED",
        "status": "MEASURED",
        "evidence_path": EV,
        "evidence_hash": EV_HASH,
    },
    "AGENT_ROLES": {
        "value": "A/B=telegram A13-A19 done, lease released · C=organs, knowledge_hook_activation_allowed",
        "status": "VERIFIED",
        "evidence_path": EV,
        "evidence_hash": EV_HASH,
    },
    "TELEGRAM_CANARY": {
        "value": "A13 PASS (0 cost @20:18) · A14 READ_BACK_USED · A15+A5 receipt · A16 window 0 rx · A17 HC_WM_CAUSAL · A18 BLOCKED",
        "status": "MEASURED",
        "evidence_path": EV,
        "evidence_hash": EV_HASH,
    },
    "ORGAN_LANE": {
        "value": "A19 issued · hook activation allowed on organism line · telegram lane released",
        "status": "VERIFIED",
        "evidence_path": EV,
        "evidence_hash": EV_HASH,
    },
}


def main() -> None:
    labels_path = OPS / "state" / "labels.json"
    data = json.loads(labels_path.read_text(encoding="utf-8"))
    data["generated_at_utc"] = NOW
    for lid, patch in UPDATES.items():
        old = data["labels"].get(lid, {})
        rec = dict(old)
        rec.update({
            "label_id": lid,
            "value": patch["value"],
            "status": patch["status"],
            "evidence_path": patch["evidence_path"],
            "evidence_hash": patch["evidence_hash"],
            "updated_at_utc": NOW,
        })
        data["labels"][lid] = rec
        append({
            "ts_utc": NOW,
            "label_id": lid,
            "event": "UPDATE",
            "value": patch["value"],
            "status": patch["status"],
            "supersedes": old.get("value"),
            "evidence_path": patch["evidence_path"],
        })
    labels_path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    # Map TELEGRAM/LANE into NOW.md
    if ("LANE", ["WRITER_LEASE", "LIVE_GATES", "AGENT_ROLES", "TELEGRAM_CANARY", "ORGAN_LANE"]) not in render_now.SECTIONS:
        render_now.SECTIONS.append(
            ("LANE", ["WRITER_LEASE", "LIVE_GATES", "AGENT_ROLES", "TELEGRAM_CANARY", "ORGAN_LANE"])
        )
    render_now.NOW.write_text(render_now.render(), encoding="utf-8")

    org = json.loads((OPS / "state" / "ORGANISM-STATE.json").read_text(encoding="utf-8"))
    ident = json.loads((OPS / "state" / "telegram" / "process-identity.json").read_text(encoding="utf-8"))
    content = (
        "## Current Truth\n\n"
        f"- **beat:** {org.get('beat')} (ORGANISM-STATE)\n"
        f"- **organism_pid:** zive · center={ident.get('process_id')} · daemon=25680(old)\n"
        f"- **halted:** {bool(org.get('halted'))}\n"
        f"- **frozen:** {bool(org.get('frozen'))}\n"
        f"- **HEAD:** 2dd9b26 (loaded center still 3abc16b)\n"
        "- **LIVE_gates:** A=PASS · B=BLOCKED(telegram A13–A17 PASS; Full Loop not started) · C=PASS · D/E=BLOCKED\n"
        "- **telegram_canary:** A13 PASS · A14 READ_BACK_USED · A15 receipt · A16 window 0 · A17 HC_WM_CAUSAL · A18 BLOCKED\n"
        "- **organ_lane_C:** A19 issued · knowledge_hook_activation_allowed=true · telegram lane released\n"
        "- **writer_lease:** RELEASED\n"
        "- **D6:** CLOSED_NEGATIVE (pair-dependent) · flip_rate gate official\n"
        "- **executable:** false (allowlisted protective only)\n"
        "- **paid_cognition:** PAUSED (telegram canary zero new receipts)\n"
    )
    wrote = safe_update_note(ROOT / "OCTOPUS" / "CURRENT-TRUTH.md", content, section_name="current-truth")

    state = ROOT / "00-INDEX" / "OCTOPUS-CURRENT-STATE.md"
    state.write_text(
        f"# OCTOPUS CURRENT STATE (generated {NOW})\n"
        "> منبع یگانه: `_ops/state/labels.json` — این صفحه محصول است، نه منبع.\n"
        "## در یک نگاه\n"
        f"- beat: {org.get('beat')} · center PID **8828** · build `3abc16b/typed-v1`\n"
        "- telegram canary: A13–A17 PASS · A18 BLOCKED · A19 handoff issued\n"
        "- lease: RELEASED · knowledge hook activation allowed for C\n"
        "- LIVE-B / Full Loop: BLOCKED\n"
        "- یافته‌ها: MISSING_ACK_FOR_/remember · CORRECT_ACCEPTED_INVALID_TURN_ID · STALE_GATE_LABEL_IN_REPLY\n"
        "لینک کامل: [[../docs/NOW.md]] · حقیقت: [[../OCTOPUS/CURRENT-TRUTH.md]] · گزارش: [[../06-EVIDENCE/TELEGRAM-CLOSED-LOOP-2026-08-20/REPORT]]\n",
        encoding="utf-8",
    )
    print(json.dumps({"labels": list(UPDATES), "truth": wrote, "now": str(render_now.NOW)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
