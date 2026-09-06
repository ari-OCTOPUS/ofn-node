import json, sys
from pathlib import Path
sys.path.insert(0, str(ROOT := Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(ROOT / "tools"))
from experiments_output import emit, read_all
def test_emit_and_read(tmp_path, monkeypatch):
    import experiments_output as eo
    monkeypatch.setattr(eo, "OUTPUT", tmp_path / "proposals.jsonl")
    n = eo.emit([{"proposal_id": "P1", "title": "test", "outcome": "RECORDED"}])
    assert n == 1
    rows = eo.read_all()
    assert len(rows) == 1 and rows[0]["proposal_id"] == "P1"
