# tests/test_validate_registry.py — گیتِ validator: مثبت روی registry واقعی
# + ۳ تستِ منفی (exit=1): kill_condition ناقص، may_mutate_ledger=true، ۲۱ فعال.
#
# اجرا:  py -m pytest _ops/hypothesis_engine/tests/test_validate_registry.py -q
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

HERE = Path(__file__).resolve()
OPS = HERE.parents[2]                      # _ops/
REPO = HERE.parents[3]                     # backup/
VALIDATOR = OPS / "scripts" / "validate_hypothesis_registry.py"
REAL_REGISTRY = REPO / "architecture" / "hypothesis-registry.yaml"

# نردبانِ کامل + قیودِ سختِ پایه — هر تستِ منفی فرضیه(های) خود را تزریق می‌کند.
_BASE = textwrap.dedent("""\
    schema_version: 1
    registry_id: octopus-hypothesis-test
    owner: octopus-core
    evidence_ladder:
      - {level: SPECULATIVE,   may_gate: false, may_trigger_tool: false, may_mutate_ledger: false}
      - {level: HYPOTHESIZING, may_gate: false, may_trigger_tool: false, may_mutate_ledger: false}
      - {level: TESTING,       may_gate: false, may_trigger_tool: false, may_mutate_ledger: false}
      - {level: EVIDENCED,     may_gate: true,  may_trigger_tool: false, may_mutate_ledger: false}
      - {level: FALSIFIED,     may_gate: false, may_trigger_tool: false, may_mutate_ledger: false}
      - {level: ARCHIVED,      may_gate: false, may_trigger_tool: false, may_mutate_ledger: false}
    hard_constraints:
      forbidden_effects: [payment, external_send]
      max_active_hypotheses: 20
      min_eig_for_testing: 0.3
      max_test_cost_hours: 4.0
      evidenced_threshold: 0.7
      falsified_threshold: 0.15
    hypotheses:
""")


def _write(tmp_path: Path, hyps_yaml: str) -> Path:
    p = tmp_path / "reg.yaml"
    p.write_text(_BASE + hyps_yaml, encoding="utf-8")
    return p


def _run(registry_path: Path):
    proc = subprocess.run(
        [sys.executable, str(VALIDATOR), "--registry", str(registry_path)],
        capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr


# ---------------------------------------------------------------------------
# مثبت — registry واقعیِ کامیت‌شده باید exit=0 بدهد
# ---------------------------------------------------------------------------
def test_real_registry_is_valid():
    assert REAL_REGISTRY.is_file(), f"registry نبود: {REAL_REGISTRY}"
    code, out = _run(REAL_REGISTRY)
    assert code == 0, f"registry واقعی نامعتبر:\n{out}"


# ---------------------------------------------------------------------------
# مثبت — یک فرضیهٔ TESTINGِ کامل هم exit=0
# ---------------------------------------------------------------------------
def test_valid_testing_hypothesis_passes(tmp_path):
    hyps = textwrap.dedent("""\
      - id: HYP-POS-1
        statement: "valid"
        status: TESTING
        existence_probability: 0.4
        usefulness_probability: 0.7
        testability: 0.8
        cost_of_testing_hours: 2.0
        expected_information_gain: 0.6
        test_plan: "run it"
        kill_condition: "if false"
        may_gate: false
        may_trigger_tool: false
        may_mutate_ledger: false
""")
    code, _ = _run(_write(tmp_path, hyps))
    assert code == 0


# ---------------------------------------------------------------------------
# منفی ۱ — TESTING بدون kill_condition ⇒ exit=1
# ---------------------------------------------------------------------------
def test_testing_without_kill_condition_rejected(tmp_path):
    hyps = textwrap.dedent("""\
      - id: HYP-NEG-KILL
        statement: "no kill"
        status: TESTING
        existence_probability: 0.4
        testability: 0.8
        cost_of_testing_hours: 2.0
        expected_information_gain: 0.6
        test_plan: "run it"
        may_gate: false
        may_trigger_tool: false
        may_mutate_ledger: false
""")
    code, out = _run(_write(tmp_path, hyps))
    assert code == 1
    assert "kill_condition" in out


# ---------------------------------------------------------------------------
# منفی ۲ — may_mutate_ledger=true در سطحی که اجازه نمی‌دهد ⇒ exit=1
# ---------------------------------------------------------------------------
def test_may_mutate_ledger_true_rejected(tmp_path):
    hyps = textwrap.dedent("""\
      - id: HYP-NEG-LEDGER
        statement: "tries ledger"
        status: TESTING
        existence_probability: 0.4
        testability: 0.8
        cost_of_testing_hours: 2.0
        expected_information_gain: 0.6
        test_plan: "run it"
        kill_condition: "if false"
        may_gate: false
        may_trigger_tool: false
        may_mutate_ledger: true
""")
    code, out = _run(_write(tmp_path, hyps))
    assert code == 1
    assert "may_mutate_ledger" in out


# ---------------------------------------------------------------------------
# منفی ۳ — ۲۱ فرضیهٔ فعال (> سقف ۲۰) ⇒ exit=1
# ---------------------------------------------------------------------------
def test_too_many_active_rejected(tmp_path):
    lines = []
    for i in range(21):
        lines.append(textwrap.dedent(f"""\
          - id: HYP-OVF-{i:02d}
            statement: "filler {i}"
            status: SPECULATIVE
            existence_probability: 0.3
            testability: 0.5
            may_gate: false
            may_trigger_tool: false
            may_mutate_ledger: false
"""))
    code, out = _run(_write(tmp_path, "".join(lines)))
    assert code == 1
    assert "سقف" in out or "فعال" in out
