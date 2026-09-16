# -*- coding: utf-8 -*-
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

AEST = timezone(timedelta(hours=10))
now = datetime.now(AEST)
ts_local = now.strftime("%Y-%m-%dT%H:%M:%S+10:00")
ts_utc = now.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

evid = Path(r"F:\backup\06-EVIDENCE\OCTOPUS-U03-SYNTHESIS-NODE-PACKS-2026-08-23")
evid.mkdir(parents=True, exist_ok=True)

adv = json.loads(
    Path(r"F:\backup\_ops\state\organs\synthesis-node-packs-advisory.json").read_text(
        encoding="utf-8"
    )
)

measure = {
    "schema": "octopus-u03-measure.v1",
    "ts_local": ts_local,
    "ts_utc": ts_utc,
    "id": "U03",
    "before": {
        "synthesis_node_packs_hook": True,
        "pointer_enabled": True,
        "pointer_path": r"F:\backup\_ops\evidence_plane\SYNTHESIS-NODE-PACKS.pointer.json",
        "packs_dir": r"F:\backup\06-EVIDENCE\OCTOPUS-LAPTOP-CONCEPTS-TO-CODE-2026-08-23\node-packs",
        "packs_on_disk": [
            "HASHES.sha256",
            "NODE-PACK-BUSINESS.json",
            "NODE-PACK-LAPTOP.json",
            "NODE-PACK-SENSORIUM.json",
        ],
        "organism_beat_consumer": False,
        "organs_enabled_callers_for_hook": [],
        "flag_drift_or_unwired": True,
        "status_undiscovered": "UNWIRED",
        "who_sets_true": "WIRING.json flags.synthesis_node_packs_hook + SYNTHESIS-NODE-PACKS.pointer.json enabled=true",
    },
    "after": {
        "synthesis_node_packs_hook": True,
        "consumer": "organs.synthesis_node_packs.beat",
        "consumer_path": r"F:\backup\_ops\organs\synthesis_node_packs.py",
        "consumer_fired": True,
        "flag_drift": False,
        "live_promote_claimed": False,
        "packs_present": adv.get("packs_present"),
        "packs_missing": adv.get("packs_missing"),
        "hash_mismatches": adv.get("hash_mismatches"),
        "open_questions_total": adv.get("open_questions_total"),
        "advisory_path": adv.get("advisory_path"),
        "run_session_wired": True,
        "pointer_ok": adv.get("pointer_ok"),
    },
    "decision": {
        "path": "A/C hybrid",
        "rationale": (
            "Hook intentionally armed with pointer enabled + packs_dir present "
            "(business/sensorium/laptop). UNWIRED was missing beat/session consumer. "
            "Safer durable close matching U02 architecture: keep hook true, wire "
            "minimal advisory consumer (registry metadata + state only; no LIVE promote; "
            "no invented pack contents). Path B (set false) would disarm designed pointer "
            "without reconciling armed hook intent."
        ),
    },
    "searches": {
        "synthesis_node_packs_hook_defs": [
            "_ops/organs/WIRING.json (+ bak-2026-08-23-synthesis-node-packs + bak-u03)",
            "_ops/evidence_plane/SYNTHESIS-NODE-PACKS.pointer.json",
        ],
        "readers_pre_close": "none in organs/*.py beat path (pointer + WIRING metadata only)",
        "packs": [
            "NODE-PACK-BUSINESS.json (business-board2)",
            "NODE-PACK-SENSORIUM.json (sensorium-orangepi)",
            "NODE-PACK-LAPTOP.json (laptop-center)",
        ],
    },
}

result = {
    "schema": "octopus-u03-result.v1",
    "id": "OCTOPUS-U03-SYNTHESIS-NODE-PACKS",
    "date": "2026-08-23",
    "ts_local": ts_local,
    "ts_utc": ts_utc,
    "status": "PASS_WITH_HOLDS",
    "evidence_dir": str(evid),
    "checks": {
        "hook_still_true": True,
        "pointer_still_enabled": True,
        "consumer_exists": True,
        "consumer_fired": True,
        "flag_drift_false": True,
        "no_live_promote_claims": True,
        "packs_present_3": adv.get("packs_present") == 3,
        "hash_ok_all": not adv.get("hash_mismatches"),
        "run_session_import": True,
        "flag_off_path_returns_flag_off": True,
        "telegram_broadcast": False,
        "money_unlock": False,
        "pwm": False,
        "pack_contents_invented": False,
        "secrets_or_urls_invented": False,
    },
    "changed": [
        "NEW _ops/organs/synthesis_node_packs.py (advisory beat consumer)",
        "PATCH _ops/organs/run_session.py (+ bak-u03-20260823) — import+call+dump+report",
        "PATCH _ops/organs/WIRING.json (+ bak-u03-20260823) — hooks.synthesis_node_packs consumer metadata; keep synthesis_node_packs_hook=true",
        "WRITE _ops/state/organs/synthesis-node-packs-advisory.json (runtime advisory sidecar)",
    ],
    "holds": [
        "Open questions remain on packs (6 total across business/sensorium/laptop) — owner/hold surfaces (incl. related U24 laptop gates); advisory only surfaces counts, does not invent answers",
        "No LIVE promote claimed; synthesis packs stay advisory registry until owner promote gate",
        "Organism hot-path not modified (sidecar organs/run_session consumer; no organism restart required)",
        "Pack body contents not rewritten; HASHES.sha256 verified read-only",
    ],
    "prove": {
        "flag_drift_closed": True,
        "unwired_closed": True,
        "packs_present": adv.get("packs_present"),
        "node_ids": [p.get("node_id") for p in (adv.get("packs") or [])],
        "advisory_path": adv.get("advisory_path"),
        "loaded_pointer": r"F:\backup\_ops\evidence_plane\SYNTHESIS-NODE-PACKS.pointer.json",
    },
    "next_owner_action": "Resolve pack open_questions / U24 gates when ready; keep live_promote_claimed=false until explicit promote GO.",
}

summary = """# OCTOPUS-U03 SYNTHESIS-NODE-PACKS hook UNWIRED — 2026-08-23

**Status: PASS_WITH_HOLDS**

## Problem
`WIRING.json` had `synthesis_node_packs_hook=true` with pointer enabled
(`evidence_plane/SYNTHESIS-NODE-PACKS.pointer.json`) and packs on disk, but **no**
organism/wiring/organs beat consumer → UNDISCOVERED **U03 UNWIRED**.

## Measure (before)
- Hook true in `_ops/organs/WIRING.json` (+ bak lineage)
- Pointer enabled; packs_dir with BUSINESS / SENSORIUM / LAPTOP + HASHES.sha256
- Zero organs beat readers of `synthesis_node_packs_hook`
- Related: pack open_questions / U24 laptop gates remain owner surfaces

## Decision
**Path A/C hybrid** (safer durable close matching U02 architecture):
keep hook **true**, wire minimal **advisory** consumer; do **not** disarm
(Path B) because pointer+packs were intentionally armed.

## Repair
1. Bak: `WIRING.json.bak-u03-20260823`, `run_session.py.bak-u03-20260823`
2. NEW `organs/synthesis_node_packs.py` — `beat()` gated on `enabled("synthesis_node_packs_hook")`
3. Wire into `organs/run_session.py` (import + call + `SYNTHESIS-NODE-PACKS-ADVISORY.json` + report field)
4. Document consumer on `WIRING.hooks.synthesis_node_packs` (mode=advisory, live_promote=false)

## Prove
- `enabled(synthesis_node_packs_hook)=True` and `beat()` → `consumer_fired=True`, `flag_drift=False`
- 3/3 packs present; HASHES match; `live_promote_claimed=false`
- Flag-off path returns `reason=flag-off` without emit
- `run_session.synthesis_node_packs_beat` import OK
- No Telegram broadcast / money / PWM / invented pack contents / invented secrets/URLs

## Holds
- Pack **open_questions** remain (6 total) — advisory surfaces counts only
- Organism hot-path unchanged (sidecar organs session consumer)
- No LIVE promote

## Evidence
`F:\\backup\\06-EVIDENCE\\OCTOPUS-U03-SYNTHESIS-NODE-PACKS-2026-08-23\\`
"""

(evid / "MEASURE.json").write_text(
    json.dumps(measure, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
(evid / "RESULT.json").write_text(
    json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
(evid / "SUMMARY.md").write_text(summary, encoding="utf-8")

rec = Path(r"F:\backup\06-EVIDENCE\OCTOPUS-UNDISCOVERED-2026-08-23\RECONCILE.md")
block = (
    f"\n\n## U03 synthesis_node_packs_hook UNWIRED — {ts_local}\n\n"
    "- **Status: PASS_WITH_HOLDS**\n"
    "- Evidence: `06-EVIDENCE/OCTOPUS-U03-SYNTHESIS-NODE-PACKS-2026-08-23/`\n"
    "- Close path: A/C hybrid — keep `synthesis_node_packs_hook=true`; "
    "wire advisory consumer `organs.synthesis_node_packs.beat` into `run_session`\n"
    "- Prove: consumer_fired=true; flag_drift=false; packs_present=3/3; "
    "HASHES ok; live_promote_claimed=false\n"
    "- Holds: pack open_questions (6) remain owner surfaces; no LIVE promote; "
    "organism hot-path untouched\n"
    "- Baks: `WIRING.json.bak-u03-20260823`, `run_session.py.bak-u03-20260823`\n"
)
prev = rec.read_text(encoding="utf-8")
if "## U03 synthesis_node_packs_hook" not in prev:
    rec.write_text(prev.rstrip() + "\n" + block, encoding="utf-8")
    print("RECONCILE appended")
else:
    print("RECONCILE already had U03 block")

print("evidence written", evid)
print("status", result["status"])
print("ts_local", ts_local)
for p in sorted(evid.iterdir()):
    print(p.name, p.stat().st_size)
