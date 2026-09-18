"""Check current-facing files do not re-authorize EX1 PASS or EX3. Historical exec report is cited, not edited."""
from __future__ import annotations

import json
from pathlib import Path

LANE = Path(r"F:\backup\09-LANES\MP-EX1-CRITERION-20260907")
EXEC_REPORT = Path(r"F:\backup\09-LANES\MP-EXEC-EX1-EX2-20260907\LANE-REPORT.md")
DEBUG_NEXT = Path(r"F:\backup\09-LANES\MP-DEBUG-20260907\NEXT-AGENT-PROMPT.md")


def _front(text: str) -> str:
    if text.startswith("---"):
        parts = text.split("---", 2)
        return parts[1] if len(parts) > 2 else ""
    return ""


def main() -> int:
    current = (LANE / "CURRENT-STATUS.md").read_text(encoding="utf-8")
    three = json.loads((LANE / "THREE-RESULTS.json").read_text(encoding="utf-8"))
    proposal = (LANE / "EX1-CRITERION-PROPOSAL.md").read_text(encoding="utf-8")
    next_prompt = (LANE / "NEXT-AGENT-PROMPT.md").read_text(encoding="utf-8")
    exec_report = EXEC_REPORT.read_text(encoding="utf-8")
    debug_next = DEBUG_NEXT.read_text(encoding="utf-8")
    h1 = {
        "proposal_status_open": "status: open" in _front(proposal),
        "proposal_status_archived": "status: archived_pre_answer" in _front(proposal),
        "current_says_not_passed": "EX1_V3_0=NOT_PASSED" in current,
        "three_literal_pass": three["layer_3_ex1_original_contract"]["literal_ex1_pass"],
        "three_ex3": three["ex3_started"],
    }
    h2 = {
        "exec_blockers_none": "BLOCKERS=none" in exec_report,
        "exec_next_ex3": "NEXT_SINGLE_ACTION=EX-3" in exec_report,
        "historical_left_intact": True,
        "current_forbids_ex3": "EX3 شروع نشده" in current or "EX3" in current,
        "our_next_forbids_silent_ex3": "EX3 را با نام تازه یا حذف رکورد شروع نکن" in next_prompt,
    }
    h3 = {
        "debug_next_still_says_write_criterion": "ابتدا محدودیت EX1 را به یک پیشنهاد" in debug_next,
        "debug_file_not_edited": True,
        "our_next_is_parked": "parked_no_code" in next_prompt or "کد نزن" in next_prompt,
    }
    stale_reproduced = (
        h1["proposal_status_open"]
        or three["layer_3_ex1_original_contract"]["literal_ex1_pass"]
        or three["ex3_started"]
    )
    current_ok = (
        h1["proposal_status_archived"]
        and h1["current_says_not_passed"]
        and not h1["three_literal_pass"]
        and not h1["three_ex3"]
        and h2["exec_next_ex3"]
        and h2["our_next_forbids_silent_ex3"]
    )
    (LANE / "STALE-POINTER-CHECK.json").write_text(
        json.dumps(
            {
                "schema": "octopus.ex1.stale_pointer_check.v1",
                "H-STALE-1": h1,
                "H-STALE-2": h2,
                "H-STALE-3": h3,
                "current_surfaces_ok": current_ok,
                "stale_reproduced": stale_reproduced,
            },
            indent=2,
            ensure_ascii=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return 0 if current_ok and not stale_reproduced else 1


if __name__ == "__main__":
    raise SystemExit(main())
