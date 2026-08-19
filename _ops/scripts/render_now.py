#!/usr/bin/env python3
# render_now.py — deterministic docs/NOW.md renderer from _ops/state/labels.json
# Sole-truth rule: labels.json is machine truth; NOW.md is its human rendering.
# Usage:  py -X utf8 _ops/scripts/render_now.py [--check]
# --check: compare rendered output with docs/NOW.md on disk; exit 1 on drift.
import json, sys, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LABELS = ROOT / "_ops/state/labels.json"
NOW = ROOT / "docs/NOW.md"

SECTIONS = [
    ("SYSTEM", ["OCTOPUS_MODE","AUTONOMY","DAEMON_4D","DAEMON_PID","TCB","SH","BOARDS","SCHEDULER","EXTERNAL_ACTION"]),
    ("MEMORY", ["MEMORY_ADMISSION_GATE","CONTRADICTION_RADAR","PREDICTION_LEDGER","METADATA_ELIGIBILITY","MEMORY_LEARNING","LEARNING_PRIMARY_METRIC","VALID_PAIRS","LIVE4_PILOT_VALID_PAIRS","LIVE4_PRIMARY_VALID_PAIRS","LEARNING_THRESHOLD","CALIBRATION_GROUP_B"]),
    ("PROVIDER/BUDGET", ["FREEZE","PAID_SMOKE","COST_OBSERVABILITY","FX_PIN","PROVIDER_ROUTE","PROVIDER_CAPACITY","LIVE4_RESERVATION","EXPERIMENT_DAILY_CAP_AUD","EXPERIMENT_HARD_STOP_AUD","PER_CALL_CAP_AUD","PAID_CALLS","RECEIPT_BUDGET_ACCOUNTING"]),
    ("LIVE-4", ["LIVE4_STATE","LIVE4_PROTOCOL_VERSION","LIVE4_PROTOCOL","LIVE4_TARGET","LIVE4_PRIMARY_SAMPLE","LIVE4_BATCHES","LIVE4_BATCH_WIN_MINIMUM","LIVE4_TOTAL_WIN_MINIMUM","LIVE4_JUDGE","LIVE4_VOID_POLICY","LIVE4_SCORING"]),
    ("INCIDENTS/DEBT", ["INC_CL1_001","INC_2_TIER_MAP","FREEZE_ERRNO22","F3_METADATA_ENTRY","D3_GIT_HISTORY_RISK","CARD_A","D_A_BASELINE_ARM","D_B_JUDGE_CONTRACT"]),
]

def render() -> str:
    data = json.loads(LABELS.read_text(encoding="utf-8"))
    labels = data["labels"]
    mapped = [lid for _, ids in SECTIONS for lid in ids]
    unmapped = [k for k in labels if k not in mapped]
    L = []
    L.append(f"# NOW — OCTOPUS current truth (generated {data['generated_at_utc']} from _ops/state/labels.json)")
    vp = labels.get("VALID_PAIRS", {})
    pv = labels.get("LIVE4_PRIMARY_VALID_PAIRS", {})
    l4s = labels.get("LIVE4_SCORING", {})
    fx = labels.get("FX_PIN", {})
    L.append("## Headline")
    L.append(f"- **VALID_PAIRS = {vp.get('value')}** ({vp.get('status')}) — primary metric; PRIMARY_VALID_PAIRS = {pv.get('value')}; threshold 20_WINS_OF_30_VALID_PAIRS")
    L.append(f"- LIVE4: {labels.get('LIVE4_STATE',{}).get('value')} · SCORING: {l4s.get('value')} ({l4s.get('status')})")
    L.append(f"- D-A: {labels.get('D_A_BASELINE_ARM',{}).get('value')} · D-B: {labels.get('D_B_JUDGE_CONTRACT',{}).get('value')}")
    L.append(f"- {labels.get('MEMORY_LEARNING',{}).get('value')} · FX: {fx.get('value')} (expires {fx.get('expires_at_utc')})")
    L.append("")
    for title, ids in SECTIONS:
        L.append(f"## {title}")
        L.append("| label | value | status | evidence |")
        L.append("|---|---|---|---|")
        for lid in ids:
            v = labels.get(lid)
            if not v:
                continue
            ev = v.get("evidence_path") or ""
            if v.get("expires_at_utc"):
                ev += f" · expires {v['expires_at_utc']}"
            L.append(f"| {lid} | {v.get('value')} | {v.get('status')} | `{ev}` |")
        L.append("")
    if unmapped:
        L.append("## UNMAPPED (renderer gap — add to SECTIONS)")
        L.append("| label | value | status |")
        L.append("|---|---|---|")
        for lid in unmapped:
            v = labels[lid]
            L.append(f"| {lid} | {v.get('value')} | {v.get('status')} |")
        L.append("")
    L.append("_Rules: statuses are OBSERVED|VERIFIED|CLAIMED|BLOCKED|VOID|UNKNOWN; two agents agreeing never makes VERIFIED; expired evidence auto-downgrades; history append-only in _ops/state/label-history.jsonl. Renderer: _ops/scripts/render_now.py._")
    L.append("")
    return "\n".join(L)

def main():
    out = render()
    if "--check" in sys.argv:
        cur = NOW.read_text(encoding="utf-8") if NOW.exists() else ""
        if cur == out:
            print("NOW.md OK (in sync)")
            return 0
        print("NOW.md DRIFT detected — regenerate")
        return 1
    NOW.parent.mkdir(parents=True, exist_ok=True)
    NOW.write_text(out, encoding="utf-8")
    print(f"rendered {NOW} ({len(out)} bytes) at {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
