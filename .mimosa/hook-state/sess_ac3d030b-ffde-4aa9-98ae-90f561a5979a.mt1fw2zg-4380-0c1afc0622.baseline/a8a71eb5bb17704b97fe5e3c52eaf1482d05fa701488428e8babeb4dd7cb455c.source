"""Import lint: the kernel is stdlib-only, and dependencies flow one way.

This is the Phase 0 architecture gate. It parses every module with `ast` (no
imports executed) and fails on:
  1. any kernel module importing anything outside the Python stdlib or the
     kernel itself;
  2. the kernel importing adapters/app/api (dependency direction);
  3. adapters importing app or api (adapters serve, they don't orchestrate).
"""

import ast
import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent / "src" / "nbb_cp"


def imported_modules(path: Path) -> set[str]:
    """Every module an import binds, from this file's point of view.

    Intra-package targets are recorded as ``nbb_cp::<subpackage>`` (kernel/adapters/
    app/api) so the direction checks can reason about them; everything else by its
    top-level name. Three spellings all have to resolve or the gate is porous:
      * ``import nbb_cp.app``            (absolute intra-package — was recorded as bare 'nbb_cp')
      * ``from .. import adapters``      (bare relative — names ARE the submodules; was dropped)
      * ``from ..adapters.llm import x`` (dotted relative — already handled)
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                parts = alias.name.split(".")
                if parts[0] == "nbb_cp":
                    if len(parts) > 1:  # import nbb_cp.app[.service] -> nbb_cp::app
                        found.add(f"nbb_cp::{parts[1]}")
                    # bare `import nbb_cp` is the package root: harmless
                else:
                    found.add(parts[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                # Relative import: resolve which top subpackage of nbb_cp it lands in.
                package_parts = path.relative_to(SRC).parent.parts
                if node.level - 1 <= len(package_parts):
                    base = list(package_parts[: len(package_parts) - (node.level - 1)])
                else:
                    base = []
                if node.module:  # from ..adapters.llm import x -> base + module parts
                    landing = (base + node.module.split("."))[:1]
                else:  # from .. import a, b -> each imported name is a submodule of base
                    landing = [(base + [alias.name])[0] for alias in node.names]
                found.update(f"nbb_cp::{part}" for part in landing if part)
            elif node.module:
                found.add(node.module.split(".")[0])
    return found


def kernel_files():
    return sorted((SRC / "kernel").rglob("*.py"))


def package_files(package: str):
    return sorted((SRC / package).rglob("*.py"))


class TestKernelPurity:
    @pytest.mark.parametrize("path", kernel_files(), ids=lambda p: p.name)
    def test_kernel_imports_stdlib_only(self, path: Path):
        for name in imported_modules(path):
            if name.startswith("nbb_cp::"):
                target = name.split("::")[1]
                assert target == "kernel", f"{path.name} imports nbb_cp.{target}"
                continue
            assert name in sys.stdlib_module_names, (
                f"{path.name} imports third-party module {name!r} — the kernel is stdlib-only"
            )


class TestParserCatchesEvasions:
    """The three spellings that previously bypassed the gate must now be recorded.

    Isolated via a temp SRC so no probe file ever lands in the real package tree
    (where the runtime kernel-purity scan would trip over it)."""

    def _probe(self, tmp_path, monkeypatch, subpkg: str, source: str) -> set[str]:
        monkeypatch.setattr(sys.modules[__name__], "SRC", tmp_path)
        pkg = tmp_path / subpkg
        pkg.mkdir(parents=True)
        f = pkg / "probe.py"
        f.write_text(source, encoding="utf-8")
        return imported_modules(f)

    def test_bare_relative_import_recorded(self, tmp_path, monkeypatch):
        # `from .. import adapters` in a kernel module lands in nbb_cp.adapters; the
        # old parser never consulted node.names and dropped it silently.
        assert "nbb_cp::adapters" in self._probe(tmp_path, monkeypatch, "kernel", "from .. import adapters\n")

    def test_absolute_intra_package_import_recorded(self, tmp_path, monkeypatch):
        # `import nbb_cp.app.service` in an adapter was recorded as bare 'nbb_cp' and
        # skipped by the direction checks; it must surface as nbb_cp::app.
        assert "nbb_cp::app" in self._probe(tmp_path, monkeypatch, "adapters", "import nbb_cp.app.service\n")

    def test_dotted_relative_still_recorded(self, tmp_path, monkeypatch):
        assert "nbb_cp::adapters" in self._probe(tmp_path, monkeypatch, "kernel", "from ..adapters.llm import mock\n")


class TestDependencyDirection:
    def test_adapters_never_import_app_or_api(self):
        for path in package_files("adapters"):
            for name in imported_modules(path):
                if name.startswith("nbb_cp::"):
                    target = name.split("::")[1]
                    assert target in ("kernel", "adapters"), (
                        f"{path} imports nbb_cp.{target}; adapters may only use the kernel"
                    )

    def test_kernel_package_never_imports_outward(self):
        for path in kernel_files():
            for name in imported_modules(path):
                if name.startswith("nbb_cp::"):
                    assert name == "nbb_cp::kernel", f"{path} escapes the kernel: {name}"
