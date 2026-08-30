# -*- coding: utf-8 -*-
"""تست‌های موتور زایش — گیت ماشینی فاز ۷ (مسیر استاندارد تولد + replay)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "organogenesis"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "novelty"))

from organogenesis.engine import OrganogenesisEngine, LegContract, REQUIRED_CONTRACT  # noqa: E402
from novelty.archive import NoveltyArchive  # noqa: E402

MODULE = Path(__file__).resolve().parents[1] / "legs" / "pain_triage.py"

SPEC = {
    "identity": "pain-triage-test", "purpose": "تست تولد", "human_value_target": "x",
    "inputs": ["pain.jsonl"], "permitted_outputs": ["digest"], "tools": ["read"],
    "budget": {"tokens": 0}, "risk_class": "A0", "heartbeat_policy": "on-demand",
    "evidence_policy": "MEASURED", "owner_gates": ["none"], "failure_modes": ["missing"],
    "rollback": "read-only", "retirement_rule": "3-cycles",
    "description": "یک قابلیت کاملاً تازه و بینظیر برای triage رنگی تصاویر ماهوارهای در این مخزن",
}
DRIVER = ("import json, sys\n"
          "from pathlib import Path\n"
          "import pain_triage\n"
          "out = pain_triage.triage(Path('fixture-pain.jsonl'), {})\n"
          "print(json.dumps({'rows': out['counts']['rows']}))\n")
FIXTURES = {"fixture-pain.jsonl": json.dumps(
    [{"ts": "2026-08-11T21:10:41", "pain": 0.25, "threshold": 0.35, "status": "OK",
      "reason_codes": [], "evidence_level": "SHADOW", "proposal": "none", "trace_id": "x"}])}


def _engine(tmp_path):
    eng = OrganogenesisEngine(state_dir=tmp_path / "state",
                              archive_path=tmp_path / "state" / "novelty" / "archive.jsonl",
                              lab=None, pages_dir=tmp_path / "pages")
    return eng


def test_contract_missing_retires(tmp_path):
    eng = _engine(tmp_path)
    spec = dict(SPEC)
    spec.pop("rollback")
    r = eng.birth(spec=spec, module_source="", driver_source="", fixtures={},
                  tests_ref="", pain_file=tmp_path / "p.jsonl",
                  state_file=tmp_path / "s.json")
    assert r["verdict"] == "RETIRE"
    assert "contract-missing" in r["reason"]


def test_novelty_gate_blocks_duplicate(tmp_path):
    eng = _engine(tmp_path)
    # همان توصیف را از قبل در آرشیو ثبت کن
    a = NoveltyArchive(eng.archive_path)
    a.append({"kind": "cohort-idea", "text": SPEC["description"]})
    r = eng.birth(spec=SPEC, module_source="x", driver_source="y", fixtures={},
                  tests_ref="", pain_file=tmp_path / "p.jsonl",
                  state_file=tmp_path / "s.json")
    assert r["verdict"] == "RETIRE"
    assert "novelty-gate" in r["reason"]


def test_full_birth_promotes_and_replays(tmp_path):
    eng = _engine(tmp_path)
    (tmp_path / "p.jsonl").write_text(FIXTURES["fixture-pain.jsonl"], encoding="utf-8")
    (tmp_path / "s.json").write_text("{}", encoding="utf-8")
    r = eng.birth(spec=SPEC, module_source=MODULE.read_text("utf-8"),
                  driver_source=DRIVER, fixtures=FIXTURES,
                  tests_ref=str(Path(__file__).resolve().parent / "test_pain_triage.py"),
                  pain_file=tmp_path / "p.jsonl", state_file=tmp_path / "s.json")
    assert r["verdict"] == "PROMOTE"
    assert r["receipt_hash"]
    assert Path(r["obsidian_page"]).exists()
    rp = eng.replay(r["capability_id"])
    assert rp["replay_ok"] is True
    assert rp["receipt_hash"] == r["receipt_hash"]


def test_leg_contract_shape():
    c = LegContract(**{k: SPEC.get(k) for k in REQUIRED_CONTRACT})
    assert c.missing() == []
    c2 = LegContract(identity="x")
    assert "purpose" in c2.missing()
