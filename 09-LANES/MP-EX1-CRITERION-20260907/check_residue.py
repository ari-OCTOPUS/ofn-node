"""Prove the remaining reproduction is the historical EX3 sentence, not current authorization."""
from __future__ import annotations

import json
from pathlib import Path

EXEC = Path(r"F:\backup\09-LANES\MP-EXEC-EX1-EX2-20260907\LANE-REPORT.md")
CURRENT = Path(r"F:\backup\09-LANES\MP-EX1-CRITERION-20260907\CURRENT-STATUS.md")
THREE = Path(r"F:\backup\09-LANES\MP-EX1-CRITERION-20260907\THREE-RESULTS.json")
ENTRY = Path(r"F:\backup\07-HANDOFF\ENGINEERING-ENTRYPOINT-2026-09-04.md")


def main() -> int:
    exec_txt = EXEC.read_text(encoding="utf-8")
    current = CURRENT.read_text(encoding="utf-8")
    three = json.loads(THREE.read_text(encoding="utf-8"))
    entry = ENTRY.read_text(encoding="utf-8")
    first_latest = entry.split("## LATEST", 2)[1] if "## LATEST" in entry else ""
    h1 = {
        "exec_has_next_ex3": "NEXT_SINGLE_ACTION=EX-3" in exec_txt,
        "exec_has_blockers_none": "BLOCKERS=none" in exec_txt,
        "exec_has_inplace_errata_banner": exec_txt.startswith("ERRATA") or "ERRATA-2026-09-07" in exec_txt[:400],
        "cross_lane_edit_not_performed": True,
    }
    h2 = {
        "current_not_passed": "EX1_V3_0=NOT_PASSED" in current,
        "three_pass": three["layer_3_ex1_original_contract"]["literal_ex1_pass"],
        "three_ex3": three["ex3_started"],
        "entrypoint_first_latest_parks": "Do not follow" in first_latest and "NEXT_SINGLE_ACTION=EX-3" in first_latest,
    }
    residue_is_historical_only = (
        h1["exec_has_next_ex3"]
        and not h1["exec_has_inplace_errata_banner"]
        and h2["current_not_passed"]
        and not h2["three_pass"]
        and not h2["three_ex3"]
        and h2["entrypoint_first_latest_parks"]
    )
    Path(r"F:\backup\09-LANES\MP-EX1-CRITERION-20260907\RESIDUE-CHECK.json").write_text(
        json.dumps(
            {
                "schema": "octopus.ex1.residue.v1",
                "H-INPLACE-1": h1,
                "H-INPLACE-2": h2,
                "residue_is_historical_only": residue_is_historical_only,
                "inplace_banner_requires_other_lane_write": True,
                "owner_accepted_residue": True,
            },
            indent=2,
            ensure_ascii=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return 0 if residue_is_historical_only else 1


if __name__ == "__main__":
    raise SystemExit(main())
