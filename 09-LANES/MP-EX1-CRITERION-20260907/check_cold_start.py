"""Cold-start navigation check. Does not edit historical exec/debug lane files."""
from __future__ import annotations

import json
from pathlib import Path

ENTRY = Path(r"F:\backup\07-HANDOFF\ENGINEERING-ENTRYPOINT-2026-09-04.md")
ENTRY7 = Path(r"F:\backup\07-HANDOFF\ENGINEERING-ENTRYPOINT-20260907.md")
CURRENT = Path(r"F:\backup\09-LANES\MP-EX1-CRITERION-20260907\CURRENT-STATUS.md")
OBS = Path(r"C:\Users\Armin\Desktop\اختاپوس بک لپ\OCTOPUS-LAB\02-agent-memory-and-handoffs\MP-EXEC-DEBUG-HANDOFF-2026-09-07.md")


def main() -> int:
    entry = ENTRY.read_text(encoding="utf-8")
    entry7 = ENTRY7.read_text(encoding="utf-8")
    current = CURRENT.read_text(encoding="utf-8")
    obs = OBS.read_text(encoding="utf-8") if OBS.is_file() else ""
    first = entry.split("## LATEST", 1)[0] + "## LATEST" + entry.split("## LATEST", 1)[1].split("## LATEST", 1)[0]
    h1 = {
        "agents_md_entrypoint_has_ex1_latest": "EX1 criterion 2026-09-07" in entry,
        "first_latest_forbids_exec_next_ex3": "NEXT_SINGLE_ACTION=EX-3" in first and "Do not follow" in first,
        "first_latest_points_current_status": "CURRENT-STATUS" in first,
    }
    h2 = {
        "dated_entrypoint_exists": ENTRY7.is_file(),
        "dated_says_not_passed": "EX1_V3_0=NOT_PASSED" in entry7,
    }
    h3 = {
        "obsidian_debug_reroutes": "ادامه از اینجا نیست" in obs,
        "current_not_passed": "EX1_V3_0=NOT_PASSED" in current,
    }
    ok = all(h1.values()) and all(h2.values()) and all(h3.values())
    Path(r"F:\backup\09-LANES\MP-EX1-CRITERION-20260907\COLD-START-CHECK.json").write_text(
        json.dumps({"schema": "octopus.ex1.cold_start.v1", "H-NAV-1": h1, "H-NAV-2": h2, "H-NAV-3": h3, "ok": ok}, indent=2)
        + "\n",
        encoding="utf-8",
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
