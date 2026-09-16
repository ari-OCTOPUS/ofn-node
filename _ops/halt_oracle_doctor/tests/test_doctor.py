"""Offline fixture harness for the halt-oracle doctor. stdlib only. No network, no node.

Tiers:
  T1  resolver fixtures F1-F5 on synthetic trees (paths, not the host's real files)
  T2  predicate fixtures — the REAL `ofn.kernel.halt.is_halted` under the allowlist
  T3  coverage fixtures — a synthetic consumer set with a known covered and a known
      uncovered consumer; a run that omits the uncovered row is a FAILED harness
  T4  safety-check NEGATIVE tests — one planted violation per rule, each must refuse
  T5  non-mutation canary — fixtures and the live repo's target files unchanged, and
      arming a HALT path is refused
  T6  determinism — two runs differ only in timestamps

Run:  python -m unittest discover -s _ops/halt_oracle_doctor/tests -v
  or: python _ops/halt_oracle_doctor/tests/test_doctor.py
"""

from __future__ import annotations

import hashlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from _ops.halt_oracle_doctor import canon, coverage, doctor, resolver, safety_check  # noqa: E402

LIVE_REPO = Path("F:/ofn-node")
PKG = Path(__file__).resolve().parents[1]

# Files whose bytes must not change across a doctor run (the live path's controls).
GUARDED_FILES = [
    "ofn/node.py", "ofn/adapters/router.py", "ofn/assistant_update.py",
    "ofn/kernel/callbudget.py", "ofn/kernel/release_switch.py",
    "ofn/budget/opslib.py", "data/gates.json",
]


def _sha(p: Path) -> str:
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()
    except OSError:
        return "<absent>"


def _snapshot(paths) -> dict:
    return {str(p): _sha(Path(p)) for p in paths}


class T1_ResolverFixtures(unittest.TestCase):
    """F1-F5 on synthetic trees. The declared HOME drives the answer."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _opslib(self, body: str = "") -> None:
        d = self.root / "ofn" / "budget"
        d.mkdir(parents=True, exist_ok=True)
        (d / "opslib.py").write_text(
            "import os as _os\nfrom pathlib import Path as _P\n"
            "HOME = _P(_os.path.expanduser('~'))\n"
            "OFN_ROOT = HOME / 'ofn'\n"
            'HALT_FLAG = OFN_ROOT / "HALT-ALL"\n' + body,
            encoding="utf-8", newline="\n")

    def test_F1_declared_home_resolves_canonical_oracle(self):
        self._opslib()
        got = resolver.resolve_canonical_oracle(self.root, "/home/ari")
        self.assertTrue(got["found"])
        self.assertEqual(got["resolved_path"], "/home/ari/ofn/HALT-ALL")
        self.assertEqual(got["literal_expression"], "OFN_ROOT / 'HALT-ALL'")

    def test_F2_resolution_tracks_the_declared_home_not_a_default(self):
        """The oracle must MOVE when HOME moves — otherwise it is a hardcode."""
        self._opslib()
        a = resolver.resolve_canonical_oracle(self.root, "/home/ari")["resolved_path"]
        b = resolver.resolve_canonical_oracle(self.root, "/srv")["resolved_path"]
        self.assertEqual(a, "/home/ari/ofn/HALT-ALL")
        self.assertEqual(b, "/srv/ofn/HALT-ALL")
        self.assertNotEqual(a, b)

    def test_F3_absent_flag_is_RUNNING_and_that_is_not_an_error(self):
        """Absent == RUNNING is the documented normal state (halt.py)."""
        got = resolver.classify_file(self.root / "nope.flag")
        self.assertEqual(got["state"], "absent")
        self.assertEqual(got["predicate"], "RUNNING")

    def test_F4_documented_vs_code_divergence_is_emitted(self):
        """D-3 encoded as a test: docs name one path, the code computes another."""
        self._opslib()
        canonical = resolver.resolve_canonical_oracle(self.root, "/home/ari")
        row = coverage.CoverageRow(
            "A-1", "E-A-telegram-send", "x", "ofn/node.py", "f", "egress",
            "WIRED", "DOC_ONLY", "e", None)
        mism = doctor._mismatches(canonical, "F:/ofn-node/HALT", [row])
        kinds = [m["kind"] for m in mism]
        self.assertIn("path_divergence", kinds)
        div = next(m for m in mism if m["kind"] == "path_divergence")
        self.assertTrue(div["owner_action_required"])
        self.assertEqual(div["severity"], "high")

    def test_F5_undocumented_extra_flag_file_is_classified_not_ignored(self):
        """A present flag is classified by state, and an unparsable one is HALTED."""
        p = self.root / "HALT"
        p.write_bytes(b"1")
        got = resolver.classify_file(p)
        self.assertEqual(got["state"], "present")
        self.assertEqual(got["predicate"], "HALTED")

    def test_F6_symlink_is_HALTED(self):
        """A planted link is not a verifiable flag (halt_flag.py:31-34)."""
        target = self.root / "real.flag"
        target.write_bytes(b"0")
        link = self.root / "link.flag"
        try:
            link.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("symlink not permitted on this host")
        got = resolver.classify_file(link)
        self.assertEqual(got["state"], "symlink")
        self.assertEqual(got["predicate"], "HALTED")

    def test_F7_directory_at_flag_path_is_HALTED(self):
        d = self.root / "HALT-ALL"
        d.mkdir()
        got = resolver.classify_file(d)
        self.assertEqual(got["state"], "directory")
        self.assertEqual(got["predicate"], "HALTED")


class T2_PredicateFixtures(unittest.TestCase):
    """The REAL predicate, imported under the single bounded allowlist."""

    @classmethod
    def setUpClass(cls):
        try:
            safety_check.assert_predicate_import_is_pure(LIVE_REPO)
        except safety_check.FailClosedError as exc:
            raise unittest.SkipTest(f"predicate unavailable: {exc}")
        from ofn.kernel.halt import is_halted
        cls.is_halted = staticmethod(is_halted)

    def test_absent_is_running(self):
        self.assertFalse(self.is_halted(None))

    def test_on_words_are_halted(self):
        for w in ("1", "true", "yes", "on", "TRUE", " on "):
            with self.subTest(w=w):
                self.assertTrue(self.is_halted(w))

    def test_off_words_are_running(self):
        for w in ("0", "false", "no", "off"):
            with self.subTest(w=w):
                self.assertFalse(self.is_halted(w))

    def test_unparsable_fails_ON_never_silently_off(self):
        """Empty, foreign vocabulary, and junk must all mean HALTED."""
        for w in ("", "   ", "maybe", "2", "halt?", "\x00"):
            with self.subTest(w=repr(w)):
                self.assertTrue(self.is_halted(w), f"{w!r} must fail ON")

    def test_classifier_uses_the_real_predicate_when_given_it(self):
        p = Path(tempfile.mkdtemp()) / "HALT-ALL"
        p.write_bytes(b"off")
        got = resolver.classify_file(p, self.is_halted)
        self.assertEqual(got["predicate"], "RUNNING")
        self.assertIn("real predicate", got["predicate_source"])

    def test_mirror_is_labelled_when_the_predicate_is_absent(self):
        """Without the real predicate the doctor must SAY it is mirroring."""
        p = Path(tempfile.mkdtemp()) / "HALT-ALL"
        p.write_bytes(b"yes")
        got = resolver.classify_file(p)          # no callable supplied
        self.assertEqual(got["predicate"], "HALTED")
        self.assertIn("NOT proof of the live adapter", got["predicate_source"])


class T3_CoverageFixtures(unittest.TestCase):
    """A synthetic consumer set: one covered, one not. Omitting the uncovered row fails."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        (self.repo / "ofn").mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        self.tmp.cleanup()

    def test_uncovered_and_covered_consumers_both_reported(self):
        (self.repo / "ofn" / "node.py").write_text(
            "class Node:\n"
            "    def publish_to_telegram(self):\n"
            "        ctx = ReleaseContext(kill_switch_active=self.killed)\n"
            "        return ctx\n"
            "    def other(self):\n"
            "        ctx = ReleaseContext(kill_switch_active=self.killed or master_halted())\n"
            "        return ctx\n",
            encoding="utf-8", newline="\n")

        uncovered = coverage.analyse_consumer(self.repo, coverage.CONSUMERS[0])
        self.assertEqual(uncovered.coverage, "DOC_ONLY")
        self.assertIn("kill_switch_active=self.killed", uncovered.evidence)

        covered_spec = dict(coverage.CONSUMERS[0], function="other")
        covered = coverage.analyse_consumer(self.repo, covered_spec)
        self.assertEqual(covered.coverage, "WIRED")
        self.assertIsNotNone(covered.oracle_reference)

    def test_summary_counts_only_true_coverage(self):
        rows = [
            coverage.CoverageRow("A-1", "E-A", "l", "f", "f", "e", "WIRED", "DOC_ONLY", "e", None),
            coverage.CoverageRow("B-1", "E-B", "l", "f", "f", "e", "WIRED", "WIRED", "e", "ln 1"),
        ]
        s = coverage.summarise(rows)
        self.assertEqual(s["consumers_total"], 2)
        self.assertEqual(s["path_correct"], 2)
        self.assertEqual(s["covered_by_canonical_oracle"], 1)

    def test_missing_consumer_code_is_UNVERIFIED_not_a_guess(self):
        row = coverage.analyse_consumer(self.repo, coverage.CONSUMERS[0])
        self.assertEqual(row.coverage, "UNVERIFIED")
        self.assertTrue(row.note, "an UNVERIFIED row must explain itself")
        self.assertTrue("not found" in row.evidence or "not found" in row.note, row.as_dict())


class T4_SafetyCheckNegativeTests(unittest.TestCase):
    """One planted violation per rule. Each MUST refuse — six red cases, not one."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.pkg = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _plant(self, body: str, name: str = "planted.py"):
        (self.pkg / name).write_text(body, encoding="utf-8", newline="\n")
        return safety_check.scan_package(self.pkg)

    def test_clean_module_yields_no_violations(self):
        self.assertEqual(self._plant("import json\nx = json.dumps({})\n"), [])

    def test_R1_transport_import_refused(self):
        v = self._plant("import socket\n")
        self.assertTrue(any(x.rule == "R1-module" for x in v), v)

    def test_R1_subprocess_import_refused(self):
        v = self._plant("from subprocess import run\n")
        self.assertTrue(any(x.rule == "R1-module" for x in v), v)

    def test_R2_protected_surface_import_refused(self):
        v = self._plant("from ofn.adapters import halt_flag\n")
        self.assertTrue(any(x.rule == "R2-protected" for x in v), v)

    def test_R2_allowlisted_predicate_is_permitted(self):
        """The single exception must actually pass, or the exception is a lie."""
        self.assertEqual(self._plant("from ofn.kernel.halt import is_halted\n"), [])

    def test_R3_dynamic_exec_refused(self):
        v = self._plant("eval('1+1')\n")
        self.assertTrue(any(x.rule == "R3-dynamic-exec" for x in v), v)

    def test_R5_flag_family_literal_refused(self):
        forbidden = "OCTOPUS" + "_WIRE" + "_LEAD_OUTBOUND"
        v = self._plant("NAME = '" + forbidden + "'\n")
        self.assertTrue(any(x.rule == "R5-flag-literal" for x in v), v)

    def test_R6_env_read_refused(self):
        v = self._plant("import os\nX = os.environ.get('HOME')\n")
        self.assertTrue(any(x.rule == "R6-env-read" for x in v), v)

    def test_unparsable_module_is_a_violation_not_a_pass(self):
        v = self._plant("def broken(:\n")
        self.assertTrue(any(x.rule == "R0-parse" for x in v), v)

    def test_certify_raises_on_a_planted_violation(self):
        self._plant("import socket\n")
        with self.assertRaises(safety_check.FailClosedError):
            safety_check.certify(self.pkg, predicate_import=False)

    def test_real_package_certifies_clean(self):
        result = safety_check.certify(PKG, predicate_import=False)
        self.assertTrue(result["certified"])
        self.assertEqual(result["static_violations"], 0)


class T5_NonMutationCanary(unittest.TestCase):
    """The whole point: a read-only tool that can arm a switch is worse than no tool."""

    def test_arming_a_halt_path_is_refused(self):
        receipts = PKG / "receipts"
        for target in (LIVE_REPO / "HALT", LIVE_REPO / "HALT-ALL", Path("F:/backup/plans/x.json")):
            with self.subTest(target=str(target)):
                with self.assertRaises(safety_check.FailClosedError):
                    doctor._guard_write(target, receipts)

    def test_writing_inside_receipts_is_allowed(self):
        receipts = PKG / "receipts"
        doctor._guard_write(receipts / "sample.json", receipts)   # must not raise

    def test_no_halt_file_exists_after_a_full_run(self):
        before = (LIVE_REPO / "HALT-ALL").exists(), (LIVE_REPO / "HALT").exists()
        with tempfile.TemporaryDirectory() as td:
            doctor.run(LIVE_REPO, "/home/ari", "F:/ofn-node/HALT", Path(td), "PRE")
            after = (LIVE_REPO / "HALT-ALL").exists(), (LIVE_REPO / "HALT").exists()
        self.assertEqual(before, after)
        self.assertEqual(after, (False, False), "a HALT file appeared — the doctor mutated")

    def test_guarded_files_are_byte_identical_across_a_run(self):
        paths = [LIVE_REPO / f for f in GUARDED_FILES]
        before = _snapshot(paths)
        with tempfile.TemporaryDirectory() as td:
            doctor.run(LIVE_REPO, "/home/ari", "F:/ofn-node/HALT", Path(td), "PRE")
        after = _snapshot(paths)
        self.assertEqual(before, after, "a guarded live-path file changed during the run")

    def test_receipt_declares_zero_mutations(self):
        with tempfile.TemporaryDirectory() as td:
            res = doctor.run(LIVE_REPO, "/home/ari", "F:/ofn-node/HALT", Path(td), "PRE")
            self.assertEqual(res["mutations_performed"], 0)
            cov = json.loads((Path(td) / sorted(p.name for p in Path(td).glob("PRE-coverage-*.json"))[0]).read_text(encoding="utf-8"))
            self.assertEqual(cov["mutations_performed"], 0)
            self.assertEqual(cov["node_observation"].split(" ")[0], "NOT_PERFORMED")


class T6_DeterminismAndShellGuard(unittest.TestCase):

    def test_two_runs_agree_except_timestamps(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            ra = doctor.run(LIVE_REPO, "/home/ari", "F:/ofn-node/HALT", Path(a), "PRE")
            rb = doctor.run(LIVE_REPO, "/home/ari", "F:/ofn-node/HALT", Path(b), "PRE")
        for r in (ra, rb):
            r.pop("generated_at_utc", None)
            r.pop("artifacts", None)
            for m in r["mismatches"]:
                m.pop("observed_at_utc", None)
        self.assertEqual(canon.digest(ra), canon.digest(rb), "the doctor is not deterministic")

    def test_shell_rewritten_path_is_refused_not_silently_used(self):
        """Git-Bash turned /home/ari into C:/Program Files/Git/home/ari once."""
        for bad in ("C:/Program Files/Git/home/ari", "C:\\home\\ari", "home/ari", ""):
            with self.subTest(bad=bad):
                with self.assertRaises(safety_check.FailClosedError):
                    doctor._require_posix_absolute(bad, "--declared-home")

    def test_literal_posix_path_is_accepted(self):
        doctor._require_posix_absolute("/home/ari", "--declared-home")   # must not raise

    def test_canon_self_test_is_green(self):
        self.assertEqual(canon.self_test(), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
