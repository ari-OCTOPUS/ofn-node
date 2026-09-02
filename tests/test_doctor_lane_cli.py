# Lane LB tests — CLI end-to-end on a synthetic vault (integration for 15).
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ofn.doctor.cli import main as cli_main  # noqa: E402
from ofn.doctor.round import tree_hash  # noqa: E402


def _vault(root: Path):
    (root / "01-TRUTH").mkdir(parents=True)
    (root / "01-TRUTH" / "STATE.md").write_text(
        "# state\nref `gone/x.md`\n", encoding="utf-8")
    (root / "debug-old.log").write_text("junk", encoding="utf-8")


def test_cli_round_backlog_destiny_end_to_end(tmp_path, capsys):
    vault = tmp_path / "vault"
    vault.mkdir()
    _vault(vault)
    runs = tmp_path / "runs"
    skip = {".pytest_cache", "__pycache__"}
    before = tree_hash(vault, skip)

    rc = cli_main(["round", "--vault", str(vault), "--out", str(runs)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "read_only_proven=True" in out
    assert tree_hash(vault, skip) == before          # vault still untouched

    findings = json.loads((runs / "findings.json").read_text(encoding="utf-8"))
    assert findings["read_only_proven"] is True
    cats = {f["category"] for f in findings["findings"]}
    assert "deadref" in cats and "junk" in cats and "contract" in cats
    receipt = json.loads(json.dumps(
        [json.loads(l) for l in (runs / "receipt.jsonl").read_text(
            encoding="utf-8").splitlines() if l]))
    kinds = {r["kind"] for r in receipt}
    assert {"round_start", "integrity_before", "finding", "integrity_after",
            "round_end"} <= kinds

    rc = cli_main(["backlog", "--state", str(runs / "self-backlog.json")])
    assert rc == 0
    backlog = json.loads((runs / "self-backlog.json").read_text(encoding="utf-8"))
    assert backlog["count"] >= 1

    proposals = [{
        "id": "PROP-LANE-CODE", "title": "self-completing doctor package",
        "target_path": "ofn/doctor/", "action": "code_change", "reversible": True,
        "evidence_refs": ["09-LANES/LB/DoD.md"],
    }, {
        "id": "PROP-JUNK", "title": "archive root junk",
        "target_path": "99-ARCHIVE/root-junk/debug-old.log", "action": "archive",
        "reversible": True, "evidence_refs": ["findings.json"],
    }, {
        "id": "PROP-BAD", "title": "no evidence", "target_path": "ofn/doctor/y.py",
        "action": "code_change", "reversible": True, "evidence_refs": [],
    }]
    (runs / "proposals.json").write_text(
        json.dumps(proposals), encoding="utf-8")
    rc = cli_main(["destiny", "--journal", str(runs / "journal.jsonl"),
                   "--proposals", str(runs / "proposals.json"),
                   "--out", str(runs / "proposal-outcomes.json"),
                   "--pr-url", "https://github.com/ari-OCTOPUS/ofn-node/pull/TEST"])
    assert rc == 0
    outcomes = json.loads((runs / "proposal-outcomes.json").read_text(encoding="utf-8"))
    assert outcomes["orphans"] == 0
    assert outcomes["all_destined"] is True
    by_id = {k: v["outcome"] for k, v in outcomes["outcomes"].items()}
    assert by_id["PROP-LANE-CODE"] == "PR_CREATED"
    assert by_id["PROP-JUNK"] == "QUEUED_WITH_REASON"
    assert by_id["PROP-BAD"] == "REJECTED_WITH_REASON"
