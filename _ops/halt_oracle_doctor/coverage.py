"""coverage — does the canonical halt oracle actually STOP each consumer?

This is the question OD-4 exists for. Path correctness ("does execution get from the
entry point to the egress?") is a DIFFERENT question, and the answer to it was already
established by the 2026-09-17 audit — so it is carried here as a declared input with
its source named, not re-derived and not presented as the doctor's own finding.

Coverage labels are restricted to the four the owner authorized:
    WIRED / TESTED_ONLY / DOC_ONLY / UNVERIFIED

`UNVERIFIED` is returned when the consumer's code region cannot be located — never a
guess upward to DOC_ONLY, and never downward to WIRED.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

LABELS = ("WIRED", "TESTED_ONLY", "DOC_ONLY", "UNVERIFIED")

ORACLE_SYMBOLS = ("master_halted", "halt_flag_active", "is_halted")

# Declared inputs. path_correctness comes from the audit, NOT from this static pass.
AUDIT_SOURCE = "09-LANES/LIVE-PATH-GATE-AUDIT-20260917/REPORT-GATE-ENQUEUE-AND-EGRESS-AUDIT.md"

CONSUMERS = (
    {
        "consumer_id": "A-1",
        "effect_id": "E-A-telegram-send",
        "label": "Telegram send",
        "file": "ofn/node.py",
        "function": "publish_to_telegram",
        "egress": "ofn/adapters/platforms/telegram_channel.py:65",
        "path_correctness": "WIRED",
        "check": "release_context_kwarg",
        "kwarg": "kill_switch_active",
    },
    {
        "consumer_id": "B-1",
        "effect_id": "E-B-text-model-spend",
        "label": "router model admission",
        "file": "ofn/adapters/router.py",
        "function": "ask",
        "egress": "ofn/adapters/remote_brain.py:88",
        "path_correctness": "WIRED",
        "check": "function_body",
    },
    {
        "consumer_id": "B-2",
        "effect_id": "E-B-text-model-spend",
        "label": "assistant_update direct call",
        "file": "ofn/assistant_update.py",
        "function": "main",
        "egress": "ofn/adapters/remote_brain.py:88",
        "path_correctness": "WIRED",
        "check": "before_first_brain_call",
    },
)


@dataclass
class CoverageRow:
    consumer_id: str
    effect_id: str
    label: str
    file: str
    function: str
    egress: str
    path_correctness: str
    coverage: str
    evidence: str
    oracle_reference: str | None
    note: str = ""

    def as_dict(self) -> dict:
        return {
            "consumer_id": self.consumer_id,
            "effect_id": self.effect_id,
            "label": self.label,
            "file": self.file,
            "function": self.function,
            "egress": self.egress,
            "path_correctness": self.path_correctness,
            "path_correctness_source": AUDIT_SOURCE,
            "coverage": self.coverage,
            "evidence": self.evidence,
            "oracle_reference": self.oracle_reference,
            "note": self.note,
        }


def _dotted(node: ast.AST) -> str:
    parts: list[str] = []
    cur = node
    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value
    if isinstance(cur, ast.Name):
        parts.append(cur.id)
    return ".".join(reversed(parts))


def _find_function(tree: ast.AST, name: str):
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    return None


def _oracle_refs(node: ast.AST) -> list[tuple[int, str]]:
    """Every reference to an oracle symbol inside `node`, as (lineno, source)."""
    out: list[tuple[int, str]] = []
    for sub in ast.walk(node):
        if isinstance(sub, ast.Call):
            short = _dotted(sub.func).split(".")[-1]
            if short in ORACLE_SYMBOLS:
                out.append((getattr(sub, "lineno", 0), ast.unparse(sub)[:160]))
        elif isinstance(sub, ast.Attribute):
            if sub.attr in ORACLE_SYMBOLS or sub.attr.endswith("halt_oracle"):
                out.append((getattr(sub, "lineno", 0), ast.unparse(sub)[:160]))
    return sorted(set(out))


def _doc_only_note(kind: str) -> str:
    return (
        f"the canonical halt oracle is documented as the node-wide safeguard but is not "
        f"consulted on this path ({kind}). This is a COVERAGE gap, not a path error."
    )


def analyse_consumer(repo: Path, spec: dict) -> CoverageRow:
    path = repo / spec["file"]
    if not path.exists():
        return CoverageRow(
            spec["consumer_id"], spec["effect_id"], spec["label"], spec["file"],
            spec["function"], spec["egress"], spec["path_correctness"], "UNVERIFIED",
            evidence=f"file not found: {spec['file']}", oracle_reference=None,
            note="cannot certify a consumer whose code was not found",
        )

    from .resolver import parse_python
    tree, perr = parse_python(path)
    if perr is not None:
        return CoverageRow(
            spec["consumer_id"], spec["effect_id"], spec["label"], spec["file"],
            spec["function"], spec["egress"], spec["path_correctness"], "UNVERIFIED",
            evidence=f"could not parse {spec['file']}: {perr}", oracle_reference=None,
            note="unparsable consumer code is an UNKNOWN, not a clean result",
        )
    fn = _find_function(tree, spec["function"])
    if fn is None:
        return CoverageRow(
            spec["consumer_id"], spec["effect_id"], spec["label"], spec["file"],
            spec["function"], spec["egress"], spec["path_correctness"], "UNVERIFIED",
            evidence=f"function {spec['function']!r} not found in {spec['file']}",
            oracle_reference=None,
            note="function renamed or moved — re-locate before trusting any label",
        )

    check = spec["check"]
    evidence = ""
    refs: list[tuple[int, str]] = []
    scope: ast.AST = fn

    if check == "release_context_kwarg":
        kwarg = spec["kwarg"]
        found: list[str] = []
        for node in ast.walk(fn):
            if isinstance(node, ast.Call) and _dotted(node.func).split(".")[-1] == "ReleaseContext":
                for kw in node.keywords:
                    if kw.arg == kwarg:
                        found.append(ast.unparse(kw.value))
        if not found:
            return CoverageRow(
                spec["consumer_id"], spec["effect_id"], spec["label"], spec["file"],
                spec["function"], spec["egress"], spec["path_correctness"], "UNVERIFIED",
                evidence=f"no ReleaseContext({kwarg}=...) found in {spec['function']}",
                oracle_reference=None,
                note="the gate input could not be located; do not assume it is absent",
            )
        evidence = f"{kwarg}={found[0]}"
        # oracle reference = an oracle symbol inside the kwarg expression itself
        for sub in ast.walk(fn):
            if isinstance(sub, ast.Call) and _dotted(sub.func).split(".")[-1] == "ReleaseContext":
                for kw in sub.keywords:
                    if kw.arg == kwarg:
                        for s2 in ast.walk(kw.value):
                            if isinstance(s2, (ast.Call, ast.Attribute)):
                                short = _dotted(s2.func).split(".")[-1] if isinstance(s2, ast.Call) else s2.attr
                                if short in ORACLE_SYMBOLS or short.endswith("halt_oracle"):
                                    refs.append((getattr(s2, "lineno", 0), ast.unparse(s2)[:160]))
        scope = fn

    elif check == "function_body":
        refs = _oracle_refs(fn)
        # evidence: show the gate that IS on the path, so the gap is legible
        gates: list[str] = []
        for node in ast.walk(fn):
            if isinstance(node, ast.Call):
                short = _dotted(node.func).split(".")[-1]
                if short in ("_charge", "_quota", "check", "allows"):
                    gates.append(f"{short}()@{getattr(node, 'lineno', 0)}")
        evidence = "gates on path: " + (", ".join(sorted(set(gates))) or "none located")

    elif check == "before_first_brain_call":
        brain_line = None
        for node in ast.walk(fn):
            if isinstance(node, ast.Call):
                short = _dotted(node.func).split(".")[-1]
                if short in ("RemoteBrain", "answer"):
                    ln = getattr(node, "lineno", 0)
                    brain_line = ln if brain_line is None else min(brain_line, ln)
        if brain_line is None:
            return CoverageRow(
                spec["consumer_id"], spec["effect_id"], spec["label"], spec["file"],
                spec["function"], spec["egress"], spec["path_correctness"], "UNVERIFIED",
                evidence="no RemoteBrain()/answer() call found in main()",
                oracle_reference=None,
                note="the egress call could not be located; do not assume it is absent",
            )
        evidence = f"first brain call at line {brain_line}"
        refs = [(ln, src) for ln, src in _oracle_refs(fn) if ln < brain_line]
        if not refs:
            all_refs = _oracle_refs(fn)
            if all_refs:
                refs = []
                evidence += " (oracle referenced only AFTER the egress — does not gate it)"

    coverage = "WIRED" if refs else "DOC_ONLY"
    note = "" if refs else _doc_only_note(check)
    return CoverageRow(
        spec["consumer_id"], spec["effect_id"], spec["label"], spec["file"],
        spec["function"], spec["egress"], spec["path_correctness"], coverage,
        evidence=evidence,
        oracle_reference=f"line {refs[0][0]}: {refs[0][1]}" if refs else None,
        note=note,
    )


def analyse_all(repo: Path) -> list[CoverageRow]:
    return [analyse_consumer(repo, spec) for spec in CONSUMERS]


def summarise(rows: list[CoverageRow]) -> dict:
    by_label: dict[str, int] = {lab: 0 for lab in LABELS}
    for r in rows:
        by_label[r.coverage] = by_label.get(r.coverage, 0) + 1
    return {
        "consumers_total": len(rows),
        "path_correct": sum(1 for r in rows if r.path_correctness == "WIRED"),
        "covered_by_canonical_oracle": by_label.get("WIRED", 0),
        "by_label": by_label,
    }


# --------------------------------------------------------------------------- #
# Kernel start-gate primitives — they RECEIVE a halt value; they do not read it.
#
# Discovered by the doctor's own site scan (2026-09-17) as two extra `is_halted`
# call sites. They are NOT consumers of the canonical oracle in the coverage sense,
# because the kernel contract is explicit that the kernel does not read the file
# (`ofn/kernel/start_permit.py:125`). They are reported separately so OD-4's
# three-approved-consumer scope stays exact and auditable.
# --------------------------------------------------------------------------- #

KERNEL_PRIMITIVES = (
    {
        "primitive_id": "P-1",
        "file": "ofn/kernel/start_permit.py",
        "function": "decide_start",
        "parameter": "halt_raw",
        "self_doc": "start_permit.py:125 - \"the kernel does not read the file\"",
    },
    {
        "primitive_id": "P-2",
        "file": "ofn/kernel/stale_class.py",
        "function": "admit_refresh",
        "parameter": "halt",
        "self_doc": "stale_class.py:313-322 - halt is bool or raw flag, supplied by the caller",
    },
)

_ORACLE_READERS = ("master_halted", "halt_flag_active")
_FILE_READ_CALLS = ("read_bytes", "read_text", "open")


def _scan_references(repo: Path, defining_file: str, func_name: str) -> dict:
    """Find production callers + importers of a symbol, by AST. No hardcoding."""
    callers: list[str] = []
    importers: list[str] = []
    imported_names: list[str] = []

    for path in sorted((repo / "ofn").rglob("*.py")):
        if "__pycache__" in path.parts or path.name.startswith("test_"):
            continue
        rel = path.relative_to(repo).as_posix()
        if rel == defining_file:
            continue
        tree, err = _parse(path)
        if err is not None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if _dotted(node.func).split(".")[-1] == func_name:
                    callers.append(f"{rel}:{getattr(node, 'lineno', 0)}")
            elif isinstance(node, ast.ImportFrom):
                if (node.module or "").endswith(defining_file.split("/")[-1][:-3]):
                    importers.append(f"{rel}:{getattr(node, 'lineno', 0)}")
                    imported_names.extend(a.name for a in node.names)
    return {"callers": sorted(set(callers)),
            "importers": sorted(set(importers)),
            "imported_names": sorted(set(imported_names))}


def _parse(path: Path):
    from .resolver import parse_python
    return parse_python(path)


def analyse_kernel_primitives(repo: Path) -> list[dict]:
    """Coverage state for the kernel start-gate primitives."""
    rows: list[dict] = []
    for spec in KERNEL_PRIMITIVES:
        path = repo / spec["file"]
        row = dict(spec)
        row["path_correctness"] = None          # not an egress consumer
        row["in_od4_scope"] = False
        row["effect"] = "none - kernel decision primitive, no egress"
        row["reads_halt_file"] = None
        row["coverage"] = "UNVERIFIED"
        row["production_callers"] = []
        row["importers"] = []
        row["imported_names"] = []
        row["note"] = ""

        if not path.exists():
            row["note"] = f"file not found: {spec['file']}"
            rows.append(row)
            continue

        tree, err = _parse(path)
        if err is not None:
            row["note"] = f"unparsable: {err}"
            rows.append(row)
            continue

        fn = _find_function(tree, spec["function"])
        if fn is None:
            row["note"] = f"function {spec['function']!r} not found"
            rows.append(row)
            continue

        # does THIS function read the flag file, or only consume a supplied value?
        reads = []
        for node in ast.walk(fn):
            if isinstance(node, ast.Call):
                short = _dotted(node.func).split(".")[-1]
                if short in _ORACLE_READERS or short in _FILE_READ_CALLS:
                    reads.append(f"{short}@{getattr(node, 'lineno', 0)}")
        row["reads_halt_file"] = bool(reads)
        row["reads_evidence"] = sorted(set(reads))

        refs = _scan_references(repo, spec["file"], spec["function"])
        row["production_callers"] = refs["callers"]
        row["importers"] = refs["importers"]
        row["imported_names"] = refs["imported_names"]

        if refs["callers"]:
            row["coverage"] = "WIRED"
            row["note"] = "a production caller exists - re-audit before treating this as dormant"
        else:
            row["coverage"] = "TESTED_ONLY"
            if refs["importers"]:
                row["note"] = ("module is imported only for other names ("
                               + ", ".join(refs["imported_names"])
                               + ") - this primitive has no production caller")
            else:
                row["note"] = "no production caller and no importer in ofn/"
        if reads:
            row["note"] += " | WARNING: this function appears to read the flag itself"
        rows.append(row)
    return rows
