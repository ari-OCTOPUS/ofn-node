#!/usr/bin/env python3
"""Tests for verify_math_atlas.py.

Uses temporary fixture repos. Covers:
  - exact row names/order (#1 BCM, #10 SOG, #17 Chrono rhythm, #20 Doctor stability)
  - flag precedence/drift
  - SOG paths validation
  - AST immunity (comments/docstrings not parsed)
  - --out only write
  - structured exit behavior (benign CRIT string in noncritical note vs true drift)
  - #17 registry/capability truth
  - spec rows (15/16/19/20 SPEC not OK)
  - missing implementation => CRIT
"""
from __future__ import annotations

import json
import os
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in os.sys.path:
    os.sys.path.insert(0, str(_SCRIPTS_DIR))

import verify_math_atlas as vma  # noqa: E402


# ---------------------------------------------------------------------------
# Fixture repo builder
# ---------------------------------------------------------------------------

class FakeRepo:
    def __init__(self, tmp: Path, *,
                 with_bcm: bool = True, with_hebbian: bool = True,
                 with_nociceptor: bool = True, with_latent: bool = True,
                 with_identity: bool = True, with_sog: bool = True,
                 with_control_law: bool = True, with_cardiac: bool = True,
                 with_chrono: bool = True, with_spectral: bool = True,
                 with_spectral_v2: bool = True,
                 with_rhythm: bool = True, with_consolidate: bool = True,
                 with_sog_lock: bool = True, with_flags: bool = True,
                 with_verdicts: bool = True, with_run_all: bool = True,
                 with_signals_registry: bool = True,
                 with_capability_manifest: bool = True,
                 with_specs: bool = True,
                 flags_content: str = "", verdicts_content: str = "",
                 sog_lock_data: dict | None = None):
        self.root = tmp
        ops = tmp / "_ops"
        ops.mkdir(parents=True, exist_ok=True)

        # --- Neural ---
        neural = ops / "neural"
        neural.mkdir(parents=True, exist_ok=True)
        if with_bcm:
            (neural / "bcm.py").write_text(
                "class BCMStabilizer:\n    def step(self, activations): pass\n",
                encoding="utf-8")
        if with_hebbian:
            (neural / "hebbian.py").write_text(
                "class HebbianAssociator:\n    pass\n", encoding="utf-8")
        if with_nociceptor:
            (neural / "nociceptor.py").write_text(
                "class Nociceptor:\n    pass\n", encoding="utf-8")
        if with_latent:
            (neural / "latent_space.py").write_text(
                "class SharedLatentSpace:\n    pass\n", encoding="utf-8")

        # --- Identity equations ---
        if with_identity:
            (ops / "identity_equations.py").write_text(
                'IDENTITIES = {"learner": {"weights": {"delta_pos": 0.40}}}\n'
                'def evaluate(signals=None): return {}\n'
                'def card(report=None): return ""\n'
                'def detail_card(name): return ""\n',
                encoding="utf-8")

        # --- SOG ---
        heart = ops / "heart"
        heart.mkdir(parents=True, exist_ok=True)
        if with_sog:
            (heart / "sog_math.py").write_text(
                "def solve_floors(rho, lam, se, sz, sd): return {}\n"
                "def delta_self(fl): return 0.0\n"
                "def e_shadow(fl): return 0.0\n"
                "def identity_total(fl): return 0.0\n"
                "def evaluate_gates(core, ipred, dare): return {}\n"
                "def run_lock(out_path=None): return {}\n",
                encoding="utf-8")
        if with_control_law:
            (heart / "control_law.py").write_text(
                "def heart_step(inputs): return {}\n", encoding="utf-8")

        # --- Cardiac, chrono ---
        if with_cardiac:
            (ops / "cardiac.py").write_text(
                "def bio_rhythm(mass=None): return {}\n", encoding="utf-8")
        if with_chrono:
            (ops / "chrono.py").write_text(
                "PHI_SUSPECT = 8.0\n"
                "def _phi_honest(): return True\n", encoding="utf-8")

        # --- Doctor spectral ---
        doctor = ops / "doctor"
        doctor.mkdir(parents=True, exist_ok=True)
        if with_spectral:
            (doctor / "spectral.py").write_text(
                "def laplacian_spectrum(edges, n): return ([], None)\n",
                encoding="utf-8")
        if with_spectral_v2:
            (doctor / "spectral_definitions.py").write_text(
                "LEGACY_SIGMA_CAP = 10.0\n"
                "def compute_legacy_sigma(l2, lm): return 0.0\n",
                encoding="utf-8")

        # --- Rhythm ---
        chrono_r = ops / "chrono_rhythm"
        chrono_r.mkdir(parents=True, exist_ok=True)
        if with_rhythm:
            (chrono_r / "rhythm.py").write_text(_RHYTHM_PY, encoding="utf-8")

        # --- Consolidate ---
        cortex = ops / "cortex"
        cortex.mkdir(parents=True, exist_ok=True)
        if with_consolidate:
            (cortex / "consolidate.py").write_text(_CONSOLIDATE_PY, encoding="utf-8")

        # --- SOG lock ---
        if with_sog_lock:
            sim = ops / "state" / "sim"
            sim.mkdir(parents=True, exist_ok=True)
            data = sog_lock_data or _DEFAULT_SOG_LOCK
            (sim / "PULSE-EQUATIONS-LOCKED.json").write_text(
                json.dumps(data), encoding="utf-8")

        # --- Specs ---
        if with_specs:
            (tmp / "04 - Architect System").mkdir(parents=True, exist_ok=True)
            (tmp / "04 - Architect System" / "DOCTOR-BOX-OF-AGENTS-SPEC.md").write_text(
                "# Doctor Box of Agents Spec\n", encoding="utf-8")
            (tmp / "04 - Architect System" / "BIO-SYNTHESIS-MAP.md").write_text(
                "# Bio Synthesis Map\n", encoding="utf-8")
            (tmp / "07 - Knowledge" / "Time-Architecture").mkdir(parents=True, exist_ok=True)
            (tmp / "07 - Knowledge" / "Time-Architecture" / "MAP.md").write_text(
                "# Time Architecture\n", encoding="utf-8")

        # --- Flags cmd ---
        if with_flags:
            (ops / "OCTOPUS-flags.cmd").write_text(
                flags_content or _DEFAULT_FLAGS, encoding="utf-8")

        # --- Owner verdicts ---
        if with_verdicts:
            (ops / "owner-verdicts.yaml").write_text(
                verdicts_content or _DEFAULT_VERDICTS, encoding="utf-8")

        # --- run_all ---
        tests_dir = ops / "tests"
        tests_dir.mkdir(parents=True, exist_ok=True)
        if with_run_all:
            (tests_dir / "run_all.py").write_text(
                'TESTS = ["test_rhythm.py", "test_canonical_consolidation.py",'
                ' "test_identity_equations.py", "test_verify_math_atlas.py"]\n',
                encoding="utf-8")

        # --- Signals registry ---
        arch = tmp / "architecture"
        arch.mkdir(parents=True, exist_ok=True)
        if with_signals_registry:
            (arch / "signals-registry.yaml").write_text(
                _DEFAULT_SIGNALS_REGISTRY, encoding="utf-8")

        # --- Capability manifest ---
        if with_capability_manifest:
            (ops / "capability-manifest.json").write_text(
                '{"schema":"v1","capability_id":"self_goal_cycle"}',
                encoding="utf-8")


_DEFAULT_SOG_LOCK = {
    "ts": "2026-07-10T20:09:22", "schema": "PULSE-EQUATIONS-LOCKED.v1",
    "full_run": True,
    "operating_point": {"rho": 0.5},
    "floors": {"P": 0.00325},
    "gates": {"dare_crosscheck": {"ok": True}},
    "status": {"delta_self": "locked", "e_shadow": "locked", "i_pred": "locked"},
    "provenance": {"code_sha256": "a" * 64, "method": "mc-sim"},
}

_DEFAULT_FLAGS = textwrap.dedent("""\
    set OCTOPUS_WIRE_BCM=1
    set OCTOPUS_WIRE_IDENTITY_EQ=1
    set OCTOPUS_WIRE_BIO=1
    set OCTOPUS_CHRONO_PHI_HONEST=1
    set OCTOPUS_WIRE_CHRONO_RHYTHM=1
    set OCTOPUS_NEURAL_LEARNED_APPLY=1
    set OCTOPUS_WIRE_BCM_FEED=1
""")

_DEFAULT_VERDICTS = textwrap.dedent("""\
    verdicts:
      neural_learned_apply:
        env: OCTOPUS_NEURAL_LEARNED_APPLY
        value: "1"
      chrono_rhythm_cr_b0:
        env: OCTOPUS_WIRE_CHRONO_RHYTHM
        value: "1"
""")

_DEFAULT_SIGNALS_REGISTRY = textwrap.dedent("""\
    schema_version: 1
    signals:
      - id: chrono-rhythm-cr-b0
        role: estimator
        truth_status: LIVE
    """)

_RHYTHM_PY = textwrap.dedent('''\
    """rhythm.py -- CR-B0."""
    import math
    class FractalNoise:
        def sample(self): return 0.0
    class Rhythm:
        def step(self, readiness, stress): pass
        def advisory(self): return {}
    def kuramoto_order_parameter(phases): return None
    def kuramoto_step(phases, coupling): return [], None
''')

_CONSOLIDATE_PY = textwrap.dedent('''\
    """consolidate.py -- memory consolidation."""
    def _salience(ev, now=None): return 0.0
    def consolidate_once(now=None):
        return {"n_in": 0, "n_semantic": 0}
''')


@pytest.fixture
def repo(tmp_path):
    return FakeRepo(tmp_path)


@pytest.fixture
def empty_repo(tmp_path):
    ops = tmp_path / "_ops"
    ops.mkdir(parents=True, exist_ok=True)
    return tmp_path


# ---------------------------------------------------------------------------
# Test: exact names/order
# ---------------------------------------------------------------------------

class TestRowOrder:
    def test_count_20(self, repo):
        atlas = vma._build_atlas(repo.root)
        assert len(atlas) == 20

    def test_first_is_BCM(self, repo):
        atlas = vma._build_atlas(repo.root)
        assert atlas[0]["name"] == "BCM"

    def test_row_10_is_SOG(self, repo):
        atlas = vma._build_atlas(repo.root)
        assert atlas[9]["name"] == "SOG/DARE/Kalman bundle"

    def test_row_17_is_Chrono_rhythm(self, repo):
        atlas = vma._build_atlas(repo.root)
        assert atlas[16]["name"] == "Chrono rhythm"

    def test_row_20_is_Doctor_stability(self, repo):
        atlas = vma._build_atlas(repo.root)
        assert atlas[19]["name"] == "Doctor stability"

    def test_row_18_is_Decay_Reinforcement(self, repo):
        atlas = vma._build_atlas(repo.root)
        assert atlas[17]["name"] == "Decay-Reinforcement"

    def test_sequential_numbers(self, repo):
        atlas = vma._build_atlas(repo.root)
        assert [r["eq"] for r in atlas] == list(range(1, 21))


# ---------------------------------------------------------------------------
# Test: spec rows
# ---------------------------------------------------------------------------

class TestSpecRows:
    def test_spec_rows_are_SPEC(self, repo):
        atlas = vma._build_atlas(repo.root)
        for r in atlas:
            if r["eq"] in (15, 16, 19, 20):
                assert r["status"] == vma.SPEC, f"Row {r['eq']} should be SPEC, got {r['status']}"

    def test_spec_row_not_OK(self, repo):
        atlas = vma._build_atlas(repo.root)
        for r in atlas:
            if r["eq"] in (15, 16, 19, 20):
                assert r["status"] != vma.OK


# ---------------------------------------------------------------------------
# Test: missing implementation => CRIT
# ---------------------------------------------------------------------------

class TestMissingImpl:
    def test_missing_bcm_crit(self, tmp_path):
        r = FakeRepo(tmp_path, with_bcm=False)
        atlas = vma._build_atlas(r.root)
        assert atlas[0]["status"] == vma.CRIT

    def test_missing_hebbian_crit(self, tmp_path):
        r = FakeRepo(tmp_path, with_hebbian=False)
        atlas = vma._build_atlas(r.root)
        assert atlas[1]["status"] == vma.CRIT

    def test_missing_rhythm_crit(self, tmp_path):
        r = FakeRepo(tmp_path, with_rhythm=False)
        atlas = vma._build_atlas(r.root)
        assert atlas[16]["status"] == vma.CRIT


# ---------------------------------------------------------------------------
# Test: #17 classification
# ---------------------------------------------------------------------------

class TestRow17:
    def test_cr_b0_built_tested(self, repo):
        atlas = vma._build_atlas(repo.root)
        r = atlas[16]
        assert r["status"] == vma.OK
        assert "CR-B0 built/tested" in r["evidence"]

    def test_kuramoto_partial_note(self, repo):
        atlas = vma._build_atlas(repo.root)
        r = atlas[16]
        assert "CR-B1 PARTIAL" in r["evidence"]

    def test_no_kuramoto_unbuilt(self, tmp_path):
        code = _RHYTHM_PY.replace("def kuramoto_order_parameter", "# removed kuramoto")
        r = FakeRepo(tmp_path, with_rhythm=False)
        chrono_dir = r.root / "_ops" / "chrono_rhythm"
        chrono_dir.mkdir(parents=True, exist_ok=True)
        (chrono_dir / "rhythm.py").write_text(code, encoding="utf-8")
        atlas = vma._build_atlas(r.root)
        assert "CR-B1 unbuilt" in atlas[16]["evidence"]


# ---------------------------------------------------------------------------
# Test: #18 classification
# ---------------------------------------------------------------------------

class TestRow18:
    def test_consolidate_built_tested(self, repo):
        atlas = vma._build_atlas(repo.root)
        r = atlas[17]
        assert r["status"] == vma.OK
        assert "built-partial/TESTED" in r["evidence"]

    def test_missing_consolidate_crit(self, tmp_path):
        r = FakeRepo(tmp_path, with_consolidate=False)
        atlas = vma._build_atlas(r.root)
        assert atlas[17]["status"] == vma.CRIT


# ---------------------------------------------------------------------------
# Test: flag precedence and drift
# ---------------------------------------------------------------------------

class TestFlagGovernance:
    def test_env_wins(self, repo):
        with patch.dict(os.environ, {"OCTOPUS_WIRE_BCM": "0"}):
            flags = vma._check_flags(repo.root)
        bcm_flag = [f for f in flags if f["flag"] == "OCTOPUS_WIRE_BCM"][0]
        assert bcm_flag["value"] == "0"
        assert bcm_flag["source"] == "env"

    def test_flags_cmd_wins_when_no_env(self, repo):
        with patch.dict(os.environ, {}, clear=True):
            flags = vma._check_flags(repo.root)
        bcm_flag = [f for f in flags if f["flag"] == "OCTOPUS_WIRE_BCM"][0]
        assert bcm_flag["value"] == "1"
        assert bcm_flag["source"] == "flags.cmd"

    def test_drift_detected(self, tmp_path):
        r = FakeRepo(tmp_path,
                     flags_content="set OCTOPUS_WIRE_BCM=1\n",
                     verdicts_content=textwrap.dedent("""\
                         verdicts:
                           bcm_verdict:
                             env: OCTOPUS_WIRE_BCM
                             value: "0"
                     """))
        with patch.dict(os.environ, {}, clear=True):
            flags = vma._check_flags(r.root)
        bcm_flag = [f for f in flags if f["flag"] == "OCTOPUS_WIRE_BCM"][0]
        assert bcm_flag["drift"] is not None
        assert "drift" in bcm_flag["drift"].lower()

    def test_env_zero_wins_explicit(self, tmp_path):
        """Explicit env `0` wins over flags.cmd `1`."""
        r = FakeRepo(tmp_path,
                     flags_content="set OCTOPUS_WIRE_BCM=1\n")
        with patch.dict(os.environ, {"OCTOPUS_WIRE_BCM": "0"}):
            flags = vma._check_flags(r.root)
        bcm_flag = [f for f in flags if f["flag"] == "OCTOPUS_WIRE_BCM"][0]
        assert bcm_flag["value"] == "0"
        assert bcm_flag["source"] == "env"

    def test_drift_causes_exit_1(self, tmp_path):
        r = FakeRepo(tmp_path,
                     flags_content="set OCTOPUS_WIRE_BCM=1\n",
                     verdicts_content=textwrap.dedent("""\
                         verdicts:
                           bcm_verdict:
                             env: OCTOPUS_WIRE_BCM
                             value: "0"
                     """))
        with patch.dict(os.environ, {}, clear=True):
            ret = vma.main(["--root", str(r.root)])
        assert ret == 1


# ---------------------------------------------------------------------------
# Test: SOG lock
# ---------------------------------------------------------------------------

class TestSogLock:
    def test_valid_lock(self, repo):
        result = vma._check_sog_lock(repo.root)
        assert result["status"] == vma.OK

    def test_missing_lock(self, empty_repo):
        result = vma._check_sog_lock(empty_repo)
        assert result["status"] == vma.CRIT

    def test_invalid_json(self, repo):
        lock = repo.root / vma.SOG_LOCK
        lock.write_text("not json{{{", encoding="utf-8")
        result = vma._check_sog_lock(repo.root)
        assert result["status"] == vma.CRIT

    def test_minimal_json_warns(self, repo):
        lock = repo.root / vma.SOG_LOCK
        lock.write_text('{"just": "a"}', encoding="utf-8")
        result = vma._check_sog_lock(repo.root)
        assert result["status"] == vma.WARN


# ---------------------------------------------------------------------------
# Test: AST immunity
# ---------------------------------------------------------------------------

class TestASTImmunity:
    def test_comment_not_parsed(self, tmp_path):
        code = ('# settle() would be bad but this is a comment\n'
                'def clean(): return 1.0\n')
        r = FakeRepo(tmp_path, with_rhythm=False)
        chrono_dir = r.root / "_ops" / "chrono_rhythm"
        chrono_dir.mkdir(parents=True, exist_ok=True)
        (chrono_dir / "rhythm.py").write_text(code, encoding="utf-8")
        result = vma._check_rhythm_purity(r.root)
        assert result["status"] == vma.OK

    def test_docstring_not_parsed(self, tmp_path):
        code = ('"""This module talks about settle and money."""\n'
                'import math\n'
                'def safe(): return math.pi\n')
        r = FakeRepo(tmp_path, with_rhythm=False)
        chrono_dir = r.root / "_ops" / "chrono_rhythm"
        chrono_dir.mkdir(parents=True, exist_ok=True)
        (chrono_dir / "rhythm.py").write_text(code, encoding="utf-8")
        result = vma._check_rhythm_purity(r.root)
        assert result["status"] == vma.OK

    def test_real_forbidden_import_detected(self, tmp_path):
        code = 'import opslib\ndef beat(): return 1.0\n'
        r = FakeRepo(tmp_path, with_rhythm=False)
        chrono_dir = r.root / "_ops" / "chrono_rhythm"
        chrono_dir.mkdir(parents=True, exist_ok=True)
        (chrono_dir / "rhythm.py").write_text(code, encoding="utf-8")
        result = vma._check_rhythm_purity(r.root)
        assert result["status"] == vma.CRIT

    def test_real_forbidden_call_detected(self, tmp_path):
        code = 'def bad(): return settle(amount=10)\n'
        r = FakeRepo(tmp_path, with_rhythm=False)
        chrono_dir = r.root / "_ops" / "chrono_rhythm"
        chrono_dir.mkdir(parents=True, exist_ok=True)
        (chrono_dir / "rhythm.py").write_text(code, encoding="utf-8")
        result = vma._check_rhythm_purity(r.root)
        assert result["status"] == vma.CRIT


# ---------------------------------------------------------------------------
# Test: --out only write
# ---------------------------------------------------------------------------

class TestOutputWrite:
    def test_out_writes_file(self, repo, tmp_path):
        out_file = tmp_path / "report.md"
        with patch.dict(os.environ, {}, clear=True):
            ret = vma.main(["--root", str(repo.root), "--out", str(out_file)])
        assert out_file.exists()
        content = out_file.read_text(encoding="utf-8")
        assert "# Math Atlas Verification Report" in content

    def test_stdout_is_markdown(self, repo, capsys):
        with patch.dict(os.environ, {}, clear=True):
            vma.main(["--root", str(repo.root)])
        assert "# Math Atlas Verification Report" in capsys.readouterr().out

    def test_no_out_no_extra_files(self, repo, tmp_path):
        with patch.dict(os.environ, {}, clear=True):
            vma.main(["--root", str(repo.root)])
        # No report.md should exist -- only the spec .md files from FakeRepo
        report_files = [f for f in tmp_path.glob("**/*.md") if f.name == "report.md"]
        assert len(report_files) == 0


# ---------------------------------------------------------------------------
# Test: structured exit behavior
# ---------------------------------------------------------------------------

class TestExitStatus:
    def test_exit_0_on_ok(self, repo):
        with patch.dict(os.environ, {}, clear=True):
            assert vma.main(["--root", str(repo.root)]) == 0

    def test_exit_1_on_missing_sog_lock(self, empty_repo):
        with patch.dict(os.environ, {}, clear=True):
            assert vma.main(["--root", str(empty_repo)]) == 1

    def test_exit_1_on_drift_not_string_search(self, tmp_path):
        """True drift (structural CRIT) => exit 1."""
        r = FakeRepo(tmp_path,
                     flags_content="set OCTOPUS_WIRE_BCM=1\n",
                     verdicts_content=textwrap.dedent("""\
                         verdicts:
                           bcm_verdict:
                             env: OCTOPUS_WIRE_BCM
                             value: "0"
                     """))
        with patch.dict(os.environ, {}, clear=True):
            assert vma.main(["--root", str(r.root)]) == 1


# ---------------------------------------------------------------------------
# Test: #17 registry/capability truth
# ---------------------------------------------------------------------------

class TestRegistryTruth:
    def test_chrono_rhythm_in_registry(self, repo):
        result = vma._check_registry_truth(repo.root)
        assert result["status"] == vma.OK
        assert any("chrono_rhythm" in n for n in result["notes"])

    def test_missing_registry_unknown(self, tmp_path):
        r = FakeRepo(tmp_path, with_signals_registry=False)
        result = vma._check_registry_truth(r.root)
        assert result["status"] == vma.UNKNOWN

    def test_parse_failure_unknown(self, tmp_path):
        r = FakeRepo(tmp_path, with_signals_registry=False)
        arch = r.root / "architecture"
        arch.mkdir(parents=True, exist_ok=True)
        (arch / "signals-registry.yaml").write_text("{{{invalid yaml", encoding="utf-8")
        result = vma._check_registry_truth(r.root)
        # Either UNKNOWN (parse failure) or CRIT (governance unverifiable)
        assert result["status"] in (vma.UNKNOWN, vma.CRIT)


# ---------------------------------------------------------------------------
# Test: run_all registration
# ---------------------------------------------------------------------------

class TestRunAll:
    def test_verifier_registered(self, repo):
        result = vma._check_run_all(repo.root)
        reg = [r for r in result["registrations"] if r["test"] == "test_verify_math_atlas.py"]
        assert len(reg) == 1
        assert reg[0]["found"] is True

    def test_missing_verifier_warns(self, tmp_path):
        r = FakeRepo(tmp_path, with_run_all=True)
        ra = r.root / vma.RUN_ALL
        ra.write_text(
            'TESTS = ["test_rhythm.py"]\n', encoding="utf-8")
        result = vma._check_run_all(r.root)
        assert result["status"] == vma.WARN
