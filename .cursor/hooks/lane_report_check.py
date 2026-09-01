import os, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _common import read_input, emit, append_ledger

d = read_input()
lane = os.environ.get("OCTOPUS_LANE", "UNDECLARED")
report = pathlib.Path("09-LANES") / lane / "LANE-REPORT.md"
loop = int(d.get("loop_count", 0) or 0)

append_ledger({"kind": "session_stop", "status": d.get("status"),
               "lane": lane, "report_exists": report.exists(), "loop_count": loop})

if d.get("status") == "completed" and not report.exists() and loop < 2:
    emit({"followup_message":
          f"Exit gate not met: {report} is missing. Write the lane report now with five "
          "sections — what was done, what remains, what failed, evidence paths, rollback steps. "
          "Use only verified numbers; mark anything unconfirmed as unverified. Do not start new work."})
else:
    emit({})
