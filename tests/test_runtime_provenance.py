"""Contract tests, not simulated measurements or runtime health evidence."""
from pathlib import Path
import tempfile
import types
import unittest
from unittest import mock

from ofn.adapters import runtime_provenance


class RuntimeProvenanceTests(unittest.TestCase):
    def test_matches_actual_imported_function_and_is_deterministic(self):
        first = runtime_provenance.code_witness(runtime_provenance, ["code_witness"])
        self.assertTrue(first["matched"], first)
        self.assertEqual(first, runtime_provenance.code_witness(runtime_provenance, ["code_witness"]))

    def test_bad_module_and_function_inputs_fail_closed(self):
        self.assertFalse(runtime_provenance.code_witness(None, ["code_witness"])["matched"])
        for names in [[], ["_digest"], ["no_such_function"], ["code_witness"] * 2, "code_witness", [1]]:
            with self.subTest(names=names):
                self.assertFalse(runtime_provenance.code_witness(runtime_provenance, names)["matched"])

    def test_non_python_and_missing_source_fail_closed(self):
        module = types.ModuleType("contract_module")
        for path in [None, "relative.py", str(Path(tempfile.gettempdir()) / "not-present-octopus-contract.py")]:
            module.__file__ = path
            self.assertFalse(runtime_provenance.code_witness(module, ["observe"])["matched"])

    def test_stale_loaded_code_detected_without_executing_current_source(self):
        # Deliberate tiny API-contract fixture, never presented as node data.
        with tempfile.TemporaryDirectory(prefix="octopus-code-witness-contract-") as scratch:
            path = Path(scratch) / "contract_module.py"
            original = "def observe():\n    return 1\n"
            path.write_text(original, encoding="utf-8")
            module = types.ModuleType("contract_module")
            module.__file__ = str(path)
            exec(compile(original, str(path), "exec"), vars(module))
            self.assertTrue(runtime_provenance.code_witness(module, ["observe"])["matched"])
            path.write_text("def observe():\n    return 2\nraise RuntimeError('must not execute source')\n", encoding="utf-8")
            result = runtime_provenance.code_witness(module, ["observe"])
            self.assertFalse(result["matched"])
            self.assertEqual(result["functions"]["observe"]["reason"], "loaded_function_differs_from_current_source")

    def test_over_budget_source_is_not_loaded(self):
        with tempfile.TemporaryDirectory(prefix="octopus-code-witness-budget-") as scratch:
            path = Path(scratch) / "contract_module.py"
            path.write_bytes(b"#" * (runtime_provenance.MAX_SOURCE_BYTES + 1))
            module = types.ModuleType("contract_module")
            module.__file__ = str(path)
            self.assertFalse(runtime_provenance.code_witness(module, ["observe"])["matched"])

    def test_ambiguous_top_level_definitions_fail_closed(self):
        with tempfile.TemporaryDirectory(prefix="octopus-code-witness-ambiguous-") as scratch:
            path = Path(scratch) / "contract_module.py"
            source = "def observe():\n    return 1\ndef observe():\n    return 2\n"
            path.write_text(source, encoding="utf-8")
            module = types.ModuleType("contract_module")
            module.__file__ = str(path)
            exec(compile(source, str(path), "exec"), vars(module))
            result = runtime_provenance.code_witness(module, ["observe"])
            self.assertFalse(result["matched"])
            self.assertEqual(result["functions"]["observe"]["reason"], "source_function_missing_or_ambiguous")

    def test_syntax_error_in_current_source_fails_closed(self):
        with tempfile.TemporaryDirectory(prefix="octopus-code-witness-syntax-") as scratch:
            path = Path(scratch) / "contract_module.py"
            source = "def observe():\n    return 1\n"
            path.write_text(source, encoding="utf-8")
            module = types.ModuleType("contract_module")
            module.__file__ = str(path)
            exec(compile(source, str(path), "exec"), vars(module))
            path.write_text("def :\n", encoding="utf-8")
            self.assertFalse(runtime_provenance.code_witness(module, ["observe"])["matched"])

    def test_link_path_rejected_before_open(self):
        link_stat = types.SimpleNamespace(st_mode=0o120777, st_file_attributes=0)
        with mock.patch.object(Path, "lstat", return_value=link_stat), \
             mock.patch.object(runtime_provenance.os, "open") as opener:
            result = runtime_provenance.code_witness(runtime_provenance, ["code_witness"])
        self.assertFalse(result["matched"])
        opener.assert_not_called()

    def test_requested_imported_function_is_not_local_module_code(self):
        module = types.ModuleType("contract_module")
        module.__file__ = runtime_provenance.__file__
        module.code_witness = runtime_provenance.code_witness
        result = runtime_provenance.code_witness(module, ["code_witness"])
        self.assertFalse(result["matched"])
        self.assertEqual(result["functions"]["code_witness"]["reason"], "not_a_local_python_function")


if __name__ == "__main__":
    unittest.main()
