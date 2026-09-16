"""safety_check — the doctor's fail-closed self-certification.

Runs BEFORE any analysis, and again as a test. It answers one question: *can this
package produce an effect outside its declared boundary?* Failure raises
FailClosedError with a named rule — never a warning, never a downgrade.

Honest scope of each rule is stated inline. Rules R1-R3/R5/R6 are STATIC (AST over
this package). R4 is static AND backed by a runtime canary in the tests, because a
write target cannot always be resolved statically — saying so is better than implying
the static rule covers it.

The one bounded exception (spec section 8.1): Tier 2 may import `ofn.kernel.halt`
only. `assert_predicate_import_is_pure()` checks that mechanically at runtime instead
of trusting the kernel's own purity contract.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import Iterable

# ---- R1: transport / process primitives that would make this tool an egress path ----
R1_FORBIDDEN_MODULES = {
    "socket", "subprocess", "ssl", "http", "smtplib", "imaplib", "ftplib",
    "requests", "paramiko", "multiprocessing", "urllib.request", "urllib.error",
    "sqlite3", "asyncio", "webbrowser",
}

# ---- R2: the live organism's protected surfaces ----
R2_PROTECTED_PREFIXES = (
    "ofn.kernel", "ofn.adapters", "ofn.agents", "ofn.budget",
)
R2_PROTECTED_EXACT = {"ofn.node", "ofn.run", "ofn", "ofn.config", "ofn.worker"}
# The single allowlist exception. Anything else under ofn is a stop condition.
R2_ALLOWLIST = {"ofn.kernel.halt"}

# ---- R3: dynamic execution ----
R3_FORBIDDEN_CALLS = {
    "eval", "exec", "compile", "__import__",
    "os.system", "os.popen", "os.execv", "os.spawnv",
}

# ---- R5: flag families that must never be referenced (narrow by design) ----
R5_FORBIDDEN_LITERALS = ("OCTOPUS_WIRE_", "OFN_WIRE_")

# ---- R6: environment reads (this tool takes configuration as arguments) ----
R6_FORBIDDEN_ATTRS = {"os.environ", "os.getenv", "os.putenv", "os.environb"}

# Modules that may legitimately appear after the allowlisted predicate import.
# `urllib.parse` is string manipulation only; it is proven transport-free in
# `assert_predicate_import_is_pure()` rather than assumed pure here.
PREDICATE_IMPORT_TRANSPORT_PREFIXES = (
    "socket", "ssl", "http", "urllib.request", "urllib.error", "sqlite3",
    "subprocess", "select", "asyncio",
)


class FailClosedError(RuntimeError):
    """A rule could not be satisfied. The doctor must not run."""


class Violation:
    __slots__ = ("rule", "path", "line", "detail")

    def __init__(self, rule: str, path: str, line: int, detail: str) -> None:
        self.rule, self.path, self.line, self.detail = rule, path, line, detail

    def as_dict(self) -> dict:
        return {"rule": self.rule, "path": self.path, "line": self.line, "detail": self.detail}

    def __str__(self) -> str:
        return f"[{self.rule}] {self.path}:{self.line} {self.detail}"


def _dotted(node: ast.AST) -> str:
    """Best-effort dotted name for an attribute/name chain."""
    parts: list[str] = []
    cur = node
    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value
    if isinstance(cur, ast.Name):
        parts.append(cur.id)
        return ".".join(reversed(parts))
    return ""


def _iter_py_files(root: Path) -> Iterable[Path]:
    for p in sorted(root.rglob("*.py")):
        if "__pycache__" in p.parts:
            continue
        yield p


def scan_package(package_dir: Path) -> list[Violation]:
    """Static rules R1, R2, R3, R5, R6 over every .py in the package."""
    violations: list[Violation] = []

    for path in _iter_py_files(package_dir):
        rel = path.name
        src = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(src, filename=str(path))
        except SyntaxError as exc:  # unparsable = cannot certify
            violations.append(Violation("R0-parse", rel, exc.lineno or 0, f"unparsable: {exc.msg}"))
            continue

        for node in ast.walk(tree):
            # R1 / R2 — imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    n = alias.name
                    if n in R1_FORBIDDEN_MODULES or n.split(".")[0] in {"socket", "subprocess", "ssl", "http", "smtplib", "imaplib", "ftplib", "requests", "paramiko", "multiprocessing", "sqlite3"}:
                        violations.append(Violation("R1-module", rel, node.lineno, f"forbidden import {n!r}"))
                    if n in R2_PROTECTED_EXACT or n.startswith(R2_PROTECTED_PREFIXES):
                        violations.append(Violation("R2-protected", rel, node.lineno, f"protected-surface import {n!r}"))
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                if mod in R1_FORBIDDEN_MODULES or mod.split(".")[0] in {"socket", "subprocess", "ssl", "http", "smtplib", "imaplib", "ftplib", "requests", "paramiko", "multiprocessing", "sqlite3"}:
                    violations.append(Violation("R1-module", rel, node.lineno, f"forbidden import from {mod!r}"))
                # `from ofn.kernel import halt` IS `ofn.kernel.halt`, and importing a
                # NAME from an allowlisted module is still that module. Resolve both
                # forms before judging against the allowlist.
                for alias in node.names:
                    effective = f"{mod}.{alias.name}" if mod else alias.name
                    if mod in R2_ALLOWLIST or effective in R2_ALLOWLIST:
                        continue
                    if effective.startswith(R2_PROTECTED_PREFIXES):
                        violations.append(Violation(
                            "R2-protected", rel, node.lineno,
                            f"protected-surface import {effective!r} (allowlist={sorted(R2_ALLOWLIST)})"))
                    elif effective in R2_PROTECTED_EXACT:
                        violations.append(Violation(
                            "R2-protected", rel, node.lineno,
                            f"protected-surface import {effective!r}"))

            # R3 — dynamic execution
            if isinstance(node, ast.Call):
                name = _dotted(node.func)
                if name in R3_FORBIDDEN_CALLS:
                    violations.append(Violation("R3-dynamic-exec", rel, node.lineno, f"call to {name!r}"))

            # R6 — environment reads
            if isinstance(node, ast.Attribute):
                name = _dotted(node)
                if name in R6_FORBIDDEN_ATTRS:
                    violations.append(Violation("R6-env-read", rel, node.lineno, f"reads {name!r}"))

            # R5 — flag-family literals.
        # STATED LIMITATION: this module is exempt from R5, because the rule's own
        # definition must contain the patterns it forbids. The exemption is recorded
        # in the receipt rather than hidden, and it is the only file-level exemption.
        is_rule_definition = rel == "safety_check.py"
        if not is_rule_definition:
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    for lit in R5_FORBIDDEN_LITERALS:
                        if lit in node.value:
                            violations.append(Violation("R5-flag-literal", rel, node.lineno, f"references flag family {lit!r}"))

            for lit in R5_FORBIDDEN_LITERALS:
                if lit in src:
                    violations.append(Violation("R5-flag-literal", rel, 0, f"references flag family {lit!r} (raw text)"))

    return violations


def assert_predicate_import_is_pure(repo: Path) -> dict:
    """The one allowlisted import, checked mechanically instead of trusted.

    Puts the live repo on sys.path (read-only, insertion only) so `ofn.kernel.halt`
    can be imported WITHOUT importing any adapter or agent code, then asserts that
    nothing transport-shaped arrived in sys.modules.
    """
    repo_str = str(repo)
    inserted = False
    if repo_str not in sys.path:
        sys.path.insert(0, repo_str)
        inserted = True

    before = set(sys.modules)
    try:
        from ofn.kernel import halt as _halt  # noqa: F401  (R2 allowlist: ofn.kernel.halt)
    except Exception as exc:  # noqa: BLE001 — any failure is "cannot prove", not "fine"
        raise FailClosedError(f"predicate import failed: {type(exc).__name__}: {exc}") from exc

    added = sorted(set(sys.modules) - before)
    offenders = [m for m in sys.modules if m.startswith(PREDICATE_IMPORT_TRANSPORT_PREFIXES)]
    if offenders:
        raise FailClosedError(
            "predicate import pulled transport-capable modules into sys.modules: "
            + ", ".join(sorted(offenders)[:8])
        )
    return {
        "modules_added": added,
        "transport_modules_present": [],
        "sys_path_inserted": inserted,
        "predicate_module": "ofn.kernel.halt",
    }


def certify(package_dir: Path, *, predicate_import: bool, repo: Path | None = None) -> dict:
    """Run the full certification. Raises FailClosedError on any violation."""
    violations = scan_package(package_dir)
    if violations:
        raise FailClosedError(
            f"{len(violations)} static violation(s): "
            + "; ".join(str(v) for v in violations[:6])
        )

    purity: dict = {"checked": False}
    if predicate_import:
        if repo is None:
            raise FailClosedError("predicate import requested without a repo path")
        purity = assert_predicate_import_is_pure(repo)
        purity["checked"] = True

    return {
        "certified": True,
        "static_violations": 0,
        "rules_checked": ["R0-parse", "R1-module", "R2-protected", "R3-dynamic-exec",
                          "R5-flag-literal", "R6-env-read"],
        "rule_exemptions": [
            "R5 does not self-scan safety_check.py (the rule's definition must contain "
            "the patterns it forbids) — the only file-level exemption"
        ],
        "note_R4": ("write-scope is enforced statically where literal + by the runtime "
                    "non-mutation canary in tests/test_doctor.py; not claimed as a full "
                    "static guarantee"),
        "predicate_import_purity": purity,
    }
